from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtCore import QThread, QBitArray
from PySide6.QtCore import qDebug, qWarning
from PySide6.QtQml import QmlElement

import math
# from neurobehavior.ardio import ArdIO
from neurobehavior.session import Session
from neurobehavior.videoctrl import VideoCtrl

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Chamber(QObject):
    statusChanged = Signal(str, str)
    sessionChanged = Signal()
    protocolFinished = Signal(str)
    inputListChanged = Signal()
    outputListChanged = Signal()
    stateListChanged = Signal(list)
    inputChanged = Signal(str, bool, arguments=["channel", "value"])
    outputChanged = Signal(str, bool, arguments=["channel", "value"])
    gazingAngleUpdated = Signal(float, float)
    stateEntered = Signal(str, str)
    stateExited = Signal(str, str)
    laserTriggered = Signal(float)
    ardT0Reset = Signal(float)

    pulsepalTriggered = Signal(str, int, bool)
    setPulsepalParams = Signal(str, int, float, float)
    ardIOTriggered = Signal(int, bool)
    ardResetTimer = Signal()
    ardIOCleared = Signal()

    arduinoOutputRequested = Signal(bytes)

    dataUpdated = Signal(str, list)
    dataAppended = Signal(str, dict)
    dataSaveReady = Signal(dict)

    videoCtrlChanged = Signal()

    ## called in the main thread
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._name = config["name"]
        self._status = ""
        self.inputChannels = config["inputChannels"]
        self.outputChannels = config["outputChannels"]
        self.leds = config["leds"]

        self._videoctrl = None
        # self.protocolConnections = []

    ## called in a chamber thread
    @Slot()
    def initialize(self):
        self.inputBits = QBitArray(len(self.inputChannels))
        self.outputBits = QBitArray(len(self.outputChannels))
        self._session = None
        self.protocol = None
        self.states = []
        self._status = "disconnected"
        # self.arduinoPortChanged.emit(self.ardPort)

    @Slot(result=str)
    def getStatus(self):
        return self._status

    @Slot(str)
    def setStatus(self, status):
        if status not in ("ready", "running"):
            qWarning("Invalid chamber status value: {}".format(status))
        self._status = status
        self.statusChanged.emit(self.name, self._status)

    status = Property(str, getStatus, setStatus, notify=statusChanged)

    @Property(str)
    @Slot(result=str)
    def name(self):
        return self._name

    @Slot(result=dict)
    def getData(self):
        if self.protocol:
            return self.protocol.getData()
        else:
            return {}

    @Slot(result=list)
    def inputVals(self):
        return list(self.inputBits)
    inputVals = Property(list, inputVals, notify=inputChanged)

    @Slot(result=list)
    def outputVals(self):
        return list(self.outputBits)
    outputVals = Property(list, outputVals, notify=outputChanged)

    @Slot(result=list)
    def inputList(self):
        return self.inputChannels
    inputList = Property(list, inputList, notify=inputListChanged)

    @Slot(result=list)
    def outputList(self):
        return self.outputChannels
    outputList = Property(list, outputList, notify=outputListChanged)

    @Slot(result=list)
    def stateList(self):
        return self.states
    stateList = Property(list, stateList, notify=stateListChanged)

    @Slot(result=VideoCtrl)
    def getVideoCtrl(self):
        return self._videoCtrl

    @Slot(VideoCtrl)
    def setVideoCtrl(self, videoCtrl):
        self._videoCtrl = videoCtrl
        self.videoCtrlChanged.emit()

    Property(VideoCtrl, getVideoCtrl, setVideoCtrl, notify=videoCtrlChanged)

    @Slot(str)
    def onStateEntered(self, statename):
        if not statename in self.states:
            self.states.append(statename)
            self.stateEntered.emit(self.name, statename)
            self.stateListChanged.emit(self.states)

    @Slot(str)
    def onStateExited(self, statename):
        if statename in self.states:
            self.states.remove(statename)
            self.stateExited.emit(self.name, statename)
            self.stateListChanged.emit(self.states)

    @Slot()
    def onConnected(self):
        if self.status == "disconnected":
            self.status = "ready"
            self.statusChanged.emit(self.name, self.status)

        if self.status != "running":
            self.clearOutput()
            self.clearLED()

    @Slot()
    def onDisconnected(self):
        if self.status == "ready":
            self.status = "disconnected"
            self.statusChanged.emit(self.name, self.status)

    @Slot(result=Session)
    def getSession(self):
        return self._session

    @Slot(Session)
    def setSession(self, session):
        if self._session == session:
            return

        if self._session:
            self._session.sessionStopped.disconnect(self.stopProtocol)
            self.protocolFinished.disconnect()
            self.dataSaveReady.disconnect()

        self._session = session
        if self._session:
            self._session.sessionStopped.connect(self.stopProtocol)
            self.protocolFinished.connect(self._session.onChamberFinished)
            self.dataSaveReady.connect(self._session.onDataSaveReady)
        self.sessionChanged.emit()

    session = Property(Session, getSession, setSession, notify=sessionChanged)

    @Slot(type, dict)
    def setProtocol(self, Protocol, params):
        if self.status == "running":
            # self.stopProtocol()
            qWarning("Trying to set a new protocol to a running chamber")
            return

        self.protocol = Protocol()
        self.protocol.updateParams(params)

    @Slot(str, Session)
    def onSessionStartRequested(self, cmbrname, session, Protocol, params):
        if cmbrname != self.name:
            return
        self.setProtocol(Protocol, params)
        self.setSession(session)
        self.startProtocol()

    @Slot()
    def startProtocol(self):
        if not self.protocol:
            return

        self.protocol.clearOutputRequested.connect(self.clearOutput)
        self.protocol.updateOutputRequested.connect(self.updateOutput)
        self.protocol.resetOutputRequested.connect(self.resetOutput)
        self.protocol.clearLEDRequested.connect(self.clearLED)
        self.protocol.updateLEDRequested.connect(self.updateLED)
        self.protocol.resetLEDRequested.connect(self.resetLED)
        self.protocol.triggerVibrationRequested.connect(self.triggerVibration)
        self.protocol.dataSaveReady.connect(self.dataSaveReady)
        self.protocol.stateEntered.connect(self.onStateEntered)
        self.protocol.stateExited.connect(self.onStateExited)
        self.protocol.dataUpdated.connect(self.dataUpdated)
        self.protocol.dataAppended.connect(self.dataAppended)
        self.protocol.protocolFinished.connect(self.onProtocolFinished)
        self.protocol.pulsepalTriggered.connect(self.onPulsepalTriggered)
        self.protocol.setPulsepalParams.connect(self.onSetPulsepalParams)
        self.protocol.ardIOTriggered.connect(self.ardIOTriggered)
        self.protocol.ardResetTimer.connect(self.ardResetTimer)
        self.protocol.ardIOCleared.connect(self.ardIOCleared)
        self.protocol.startProtocol()
        self.inputChanged.connect(self.protocol.inputChanged)
        self.outputChanged.connect(self.protocol.outputChanged)
        self.laserTriggered.connect(self.protocol.laserTriggered)
        self.ardT0Reset.connect(self.protocol.ardT0Reset)
        self.gazingAngleUpdated.connect(self.protocol.gazingAngleUpdated)
        self.status = "running"

    @Slot()
    def stopProtocol(self):
        if self.protocol:
            self.inputChanged.disconnect(self.protocol.inputChanged)
            self.outputChanged.disconnect(self.protocol.outputChanged)            
            self.laserTriggered.disconnect(self.protocol.laserTriggered)
            self.ardT0Reset.disconnect(self.protocol.ardT0Reset)
            self.gazingAngleUpdated.disconnect(self.protocol.gazingAngleUpdated)
            self.protocol.stopProtocol()
            self.protocol.clearOutputRequested.disconnect()
            self.protocol.updateOutputRequested.disconnect()
            self.protocol.resetOutputRequested.disconnect()
            self.protocol.clearLEDRequested.disconnect()
            self.protocol.updateLEDRequested.disconnect()
            self.protocol.resetLEDRequested.disconnect()
            self.protocol.triggerVibrationRequested.disconnect()
            self.protocol.dataSaveReady.disconnect()
            self.protocol.stateEntered.disconnect()
            self.protocol.stateExited.disconnect()
            self.protocol.dataUpdated.disconnect()
            self.protocol.dataAppended.disconnect()
            self.protocol.protocolFinished.disconnect()
            self.protocol.pulsepalTriggered.disconnect()
            self.protocol.setPulsepalParams.disconnect()
            self.protocol.ardIOTriggered.disconnect()
            self.protocol.ardResetTimer.disconnect()
            self.protocol.ardIOCleared.disconnect()
            self.protocol = None
        self.clearOutput()
        self.clearLED()
        self.states = []
        self.status = "ready"

    @Slot()
    def onProtocolFinished(self):
        self.inputChanged.disconnect(self.protocol.inputChanged)
        self.outputChanged.disconnect(self.protocol.outputChanged)        
        self.laserTriggered.disconnect(self.protocol.laserTriggered)
        self.ardT0Reset.disconnect(self.protocol.ardT0Reset)
        self.protocol.clearOutputRequested.disconnect()
        self.protocol.updateOutputRequested.disconnect()
        self.protocol.resetOutputRequested.disconnect()
        self.protocol.clearLEDRequested.disconnect()
        self.protocol.updateLEDRequested.disconnect()
        self.protocol.resetLEDRequested.disconnect()
        self.protocol.triggerVibrationRequested.disconnect()
        self.protocol.dataSaveReady.disconnect()
        self.protocol.stateEntered.disconnect()
        self.protocol.stateExited.disconnect()
        self.protocol.dataUpdated.disconnect()
        self.protocol.dataAppended.disconnect()
        self.protocol.protocolFinished.disconnect()
        self.protocol.pulsepalTriggered.disconnect()
        self.protocol.setPulsepalParams.disconnect()
        self.protocol.ardIOTriggered.disconnect()
        self.protocol.ardResetTimer.disconnect()
        self.protocol.ardIOCleared.disconnect()
        self.clearOutput()
        self.clearLED()
        self.status = "ready"
        self.protocolFinished.emit(self.name)

    @Slot(int, bool)
    def onPulsepalTriggered(self, evtid, value):
        self.pulsepalTriggered.emit(self.name, evtid, value)

    @Slot(int, float, float)
    def onSetPulsepalParams(self, evtid, dur, intv):
        self.setPulsepalParams.emit(self.name, evtid, dur, intv)

    # @Slot(int, bool)
    # def onArdIOTriggered(self, evtid, value):
    #     self.ardIOTriggered.emit(evtid, value)

    @Slot(int)
    def onTLaserMsgReceived(self, tlaser):
        self.laserTriggered.emit(tlaser)

    @Slot(int)
    def onArdT0Reset(self, t0):
        self.ardT0Reset.emit(t0)

    @Slot(str, str, int)
    def onArdMsgReceived(self, cmbrname, msgtype, msg):
        if cmbrname != self.name:
            return

        if msgtype == "input":
            self.onArdInputChanged(msg)
        elif msgtype == "output":
            self.onArdOutputChanged(msg)

    @Slot(int)
    def onArdInputChanged(self, msg):
        for ichannel in range(self.inputBits.size()):
            val_prev = self.inputBits[ichannel]
            val_now = bool((1 << ichannel) & msg)
            val_now = not val_now  # input low when sensor on

            if val_prev != val_now:
                ch = self.inputChannels[ichannel]
                self.inputBits.setBit(ichannel, val_now)
                # qDebug("Input {}: {}".format(ch, val_now))
                self.inputChanged.emit(ch, val_now)

    @Slot(int)
    def onArdOutputChanged(self, msg):
        for ichannel in range(self.outputBits.size()):
            val_prev = self.outputBits[ichannel]
            val_now = bool((1 << ichannel) & msg)

            if val_prev != val_now:
                ch = self.outputChannels[ichannel]
                self.outputBits.setBit(ichannel, val_now)
                # qDebug("Output {}: {}".format(ch, val_now))
                self.outputChanged.emit(ch, val_now)

    @Slot(int, list, result=bytes)
    def encodeMsg(self, code, bits):
        msg = 0
        for i in range(len(bits)):
            # msg += bits[i] * 2**(i)
            msg |= bits[i] << i
        msg = (int(msg)).to_bytes(math.ceil(len(bits)/8), byteorder="little")
        msg = code.encode() + msg + "\r\n".encode()
        return msg

    @Slot(str, list)
    def onUpdateOutputBroadcast(self, chamber_name, output):
        if chamber_name == self.name:
            self.updateOutput(output)

    @Slot(list)
    def resetOutput(self, output):
        self.clearOutput()
        # self.clearOutput(clear_sound=clear_sound)
        self.updateOutput(output)

    @Slot(list)
    def updateOutput(self, output, clear_sound=False):
        """
        Set output

        Arguments
        output: list of tuples, (outputname, switch)
        """
        nbit = math.ceil(len(self.outputBits)/8) * 8
        update_on = [0] * nbit
        update_off = [1] * nbit

        for oname, switch in output:
            iport = self.outputChannels.index(oname)
            if switch == True:
                update_on[iport] = 1
            elif switch == False:
                update_off[iport] = 0

            # if oname == "reward":
            #     print("######## cmbr {}, reward {}".format(self.name, switch))

        if sum(update_on) > 0:
            msg_on = self.encodeMsg("+", update_on)
            # self.ard.sendMessage(msg_on)
            self.arduinoOutputRequested.emit(msg_on)
        if sum(update_off) < nbit:
            msg_off = self.encodeMsg("-", update_off)
            # self.ard.sendMessage(msg_off)
            self.arduinoOutputRequested.emit(msg_off)

    @Slot()
    def clearLED(self):
        msg = b"lc\r\n"
        self.arduinoOutputRequested.emit(msg)

    @Slot(list)
    def resetLED(self, led_outputs):
        self.clearLED()
        self.updateLED(led_outputs)

    @Slot(list)
    def updateLED(self, led_outputs):
        msg = b"lu"

        msg_led = 0
        msg_rgb = b""
        for led in led_outputs:
            i = self.leds.index(led)
            msg_led |= 1 << i

            for val in led_outputs[led]:
                msg_rgb += (val).to_bytes(1, byteorder="little")
        msg += (msg_led).to_bytes(math.ceil(len(self.leds)/8), byteorder="little")
        msg += msg_rgb
        msg += "\r\n".encode()
        self.arduinoOutputRequested.emit(msg)

    @Slot()
    def triggerVibration(self):
        msg = b"v\r\n"
        self.arduinoOutputRequested.emit(msg)

    @Slot()
    def clearOutput(self, clear_sound=True):
        msg = (0).to_bytes(math.ceil(len(self.outputBits)/8), byteorder="little")
        msg = "o".encode() + msg + "\r\n".encode()
        # self.ard.sendMessage(msg)
        self.arduinoOutputRequested.emit(msg)
