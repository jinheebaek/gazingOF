from PySide6.QtCore import QObject, Signal, Slot, QBitArray
from PySide6.QtCore import qDebug
from PySide6.QtCore import QTimer
from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPort

import math
import time


class ArdIO(QObject):
    connected = Signal()
    disconnected = Signal()
    inputMsgReceived = Signal(int)
    outputMsgReceived = Signal(int)
    configMsgReceived = Signal(str)
    tlaserMsgReceived = Signal(float)
    ardT0Reset = Signal(float)

    # def initialize(self):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ard = QSerialPort()
        self.timer = QTimer()
        self.timer.setInterval(1)
        self.con_timer = QTimer()
        self.con_timer.setInterval(1000)
        self.con_timer.timeout.connect(self.connectArd)
        self.is_connected = False
        self.port = "COM4"
        self.outputBits = QBitArray(2)
        self.connectArd()
        self.t0_msg = 0

    @Slot()
    def setPort(self, port):
        if self.is_connected:
            self.stop()
            self.is_connected = False
        # self.ard.setPortName(port)
        self.port = port
        qDebug("Trying to connect arduino")
        self.con_timer.start()

    @Slot()
    def connectArd(self):
        self.ard.setPortName(self.port)
        if self.ard.open(QIODeviceBase.ReadWrite):
            self.ard.setBaudRate(115200)
            qDebug("Arduino connected")
            time.sleep(1)
            self.ard.flush()
            self.clearOutput()
            self.ard.errorOccurred.connect(self.onErrorOccurred)
            self.timer.timeout.connect(self.processMessage)
            self.timer.start()
            self.connected.emit()
            self.is_connected = True
            self.con_timer.stop()

    @Slot()
    def onErrorOccurred(self):
        if self.is_connected:
            self.stop()
        self.con_timer.start()

    @Slot()
    def stop(self):
        self.con_timer.stop()
        self.con_timer.stop()

        if self.is_connected:
            self.clearOutput()
            self.ard.errorOccurred.disconnect(self.onErrorOccurred)
            self.timer.timeout.disconnect(self.processMessage)
            self.timer.stop()
            self.ard.close()
            self.disconnected.emit()
            self.is_connected = False

    @Slot()
    def processMessage(self):
        while self.ard.canReadLine():
            msg = self.ard.readLine().data()
            if msg.endswith(b"\r\n"):
                msg = msg[:-2]
            # qDebug("from Ard: {}".format(msg))
            if msg.startswith(b'i'):
                msg = int.from_bytes(msg[1:], byteorder="little")
                self.inputMsgReceived.emit(msg)
            elif msg.startswith(b'o'):
                msg = int.from_bytes(msg[1:], byteorder="little")
                self.outputMsgReceived.emit(msg)
            elif msg.startswith(b'c'):
                self.configMsgReceived.emit(msg[1:].decode())
            elif msg.startswith(b'l'):
                t_laser = int(msg[1:].decode().strip())
                t_msg_delay = (time.time() - self.t0_msg) / 2
                self.tlaserMsgReceived.emit(self.t0_msg + t_msg_delay)

    @Slot()
    def sendMessage(self, msg):
        # qDebug("to Ard: {}".format(msg))
        if self.is_connected:
            if msg == self.encodeMsg("+", [0, 1, 0, 0, 0, 0, 0, 0]):
                self.t0_msg = time.time()
            self.ard.write(msg)

    @Slot(int, list, result=bytes)
    def encodeMsg(self, code, bits):
        msg = 0
        for i in range(len(bits)):
            # msg += bits[i] * 2**(i)
            msg |= bits[i] << i
        msg = (int(msg)).to_bytes(math.ceil(len(bits)/8), byteorder="little")
        msg = code.encode() + msg + "\r\n".encode()
        return msg
    
    @Slot(int, bool)
    def onArdIOTriggered(self, evtid, value):
        """
        Set output

        Arguments
        output: list of tuples, (outputname, switch)
        """
        nbit = math.ceil(len(self.outputBits)/8) * 8
        update_on = [0] * nbit
        update_off = [1] * nbit

        if value:
            update_on[evtid] = 1
        else:
            update_off[evtid] = 0

        if sum(update_on) > 0:
            msg_on = self.encodeMsg("+", update_on)
            # self.ard.sendMessage(msg_on)
            self.sendMessage(msg_on)
        if sum(update_off) < nbit:
            msg_off = self.encodeMsg("-", update_off)
            # self.ard.sendMessage(msg_off)
            self.sendMessage(msg_off)
    
    @Slot(int, bool)
    def onArdResetTimer(self):
        self.sendMessage("t".encode() + "\r\n".encode())
        self.ardT0Reset.emit(time.time())

    @Slot()
    def clearOutput(self):
        msg = (0).to_bytes(math.ceil(len(self.outputBits)/8), byteorder="little")
        msg = "o".encode() + msg + "\r\n".encode()
        self.sendMessage(msg)
