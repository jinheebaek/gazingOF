from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtCore import qDebug
from PySide6.QtCore import QTimer
from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPort

import time


class ArdIO(QObject):
    connected = Signal()
    disconnected = Signal()
    inputMsgReceived = Signal(int)
    outputMsgReceived = Signal(int)
    configMsgReceived = Signal(str)

    def initialize(self):
        self.ard = QSerialPort()
        self.timer = QTimer()
        self.timer.setInterval(1)
        self.con_timer = QTimer()
        self.con_timer.setInterval(1000)
        self.con_timer.timeout.connect(self.connectArd)
        self.is_connected = False
        self.port = ""

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

    @Slot()
    def sendMessage(self, msg):
        # qDebug("to Ard: {}".format(msg))
        if self.is_connected:
            self.ard.write(msg)
