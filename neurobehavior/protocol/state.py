from PySide6.QtCore import Signal, Slot, qDebug
from PySide6.QtCore import QTimer
from PySide6.QtStateMachine import QState


class State(QState):
    timeout = Signal()
    stateEntered = Signal(str)
    stateReady = Signal(str)
    stateExited = Signal(str)

    def __init__(self, name, protocol):
        super().__init__()
        self.name = name
        self.protocol = protocol
        self.duration = 0

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.timeout)

        self.entered.connect(self.beforeOnEntered)
        self.entered.connect(self.onEntered)
        self.entered.connect(lambda: self.stateReady.emit(self.name))
        self.exited.connect(self.onExited)
        self.exited.connect(self.afterOnExited)
        self.protocol.protocolStarted.connect(self.initialize)
        self.protocol.protocolStopped.connect(self.onProtocolStopped)

    def initialize(self):
        return

    def beforeOnEntered(self):
        # print("t : {}".format(self.protocol.timer.elapsed()))
        # self.protocol.inputChanged.connect(self.recordInputChange)
        # self.protocol.outputChanged.connect(self.recordOutputChange)
        # self.protocol.inputChanged.connect(self.onInputChange)
        self.protocol.recordData("state", {
            "timestamp": self.protocol.timer.elapsed(),
            "state": self.name
        })
        self.stateEntered.emit(self.name)

    def onEntered(self):
        return

    def onExited(self):
        return

    def afterOnExited(self):
        # self.timer.stop()
        # self.protocol.inputChanged.disconnect(self.onInputChange)
        # self.protocol.inputChanged.disconnect(self.recordInputChange)
        # self.protocol.outputChanged.disconnect(self.recordOutputChange)
        self.stateExited.emit(self.name)
        self.protocol.lastState = self.name

    def startTimer(self, duration):
        if duration > 0:
            self.duration = duration
            self.timer.setInterval(self.duration * 1e3)  # arg in millisec
            self.timer.start()

    def connectState(self, sig, state):
        self.addTransition(sig, self.protocol.getState(state))

    def onInputChange(self, channel, value):
        return

    def recordInputChange(self, channel, value):
        self.protocol.recordData("input", {
            "timestamp": self.protocol.timer.elapsed(),
            "trial": self.protocol.trial,
            "state": self.name,
            "channel": channel,
            "value": value
        })
        if value:
            self.protocol.recordCountData("count_input", channel)

    def recordOutputChange(self, channel, value):
        self.protocol.recordData("output", {
            "timestamp": self.protocol.timer.elapsed(),
            "trial": self.protocol.trial,
            "state": self.name,
            "channel": channel,
            "value": value
        })
        if value:
            self.protocol.recordCountData("count_output", channel)

    def clearOutput(self):
        self.protocol.clearOutputRequested.emit()

    def updateOutput(self, output):
        self.protocol.updateOutputRequested.emit(output)

    def resetOutput(self, output):
        self.protocol.resetOutputRequested.emit(output)

    def clearLED(self):
        self.protocol.clearLEDRequested.emit()

    def updateLED(self, output):
        self.protocol.updateLEDRequested.emit(output)

    def resetLED(self, output):
        self.protocol.resetLEDRequested.emit(output)

    def onProtocolStopped(self):
        self.timer.stop()
