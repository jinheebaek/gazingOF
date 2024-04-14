from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtCore import QTimer
from PySide6.QtQml import QmlElement
from PySide6.QtStateMachine import QStateMachine, QFinalState

from neurobehavior.protocol.event import EventBoolean

import time

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Protocol(QObject):
    protocolStarted = Signal()
    protocolStopped = Signal()
    protocolFinished = Signal()
    timeout = Signal()

    clearOutputRequested = Signal()
    updateOutputRequested = Signal(list)  # list of tuple. e.g. [("reward", True)]
    resetOutputRequested = Signal(list)  # list of tuple. e.g. [("reward", True)]
    clearLEDRequested = Signal()
    updateLEDRequested = Signal(dict)  # e.g. {"reward_zone": (255, 255, 0)}
    resetLEDRequested = Signal(dict)  # e.g. {"reward_zone": (255, 255, 0)}
    triggerVibrationRequested = Signal()

    dataUpdated = Signal(str, list)
    dataAppended = Signal(str, dict)
    dataSaveReady = Signal(dict)

    inputChanged = Signal(str, bool, arguments=["channel", "value"])
    outputChanged = Signal(str, bool, arguments=["channel", "value"])

    stateEntered = Signal(str)
    stateExited = Signal(str)

    pulsepalTriggered = Signal(int, bool)
    setPulsepalParams = Signal(int, float, float)

    name = ""
    inp = []
    out = []
    led = []
    params = {}

    # @classmethod
    # def getParams(cls):
    #     return cls.params

    def __init__(self, parent=None):
        super().__init__(parent)
        self.machine = QStateMachine()
        self._events = {}
        self.data = {}
        self.dataRoot = "/home/jinhee/"

        self.states = {}
        self.states["final_state"] = QFinalState()
        self.machine.addState(self.states["final_state"])
        self.machine.finished.connect(self.finishProtocol)
        self.lastState = None

        self.timer = Timer()
        self.timer.timeout.connect(self.onTimeout)
        self.is_timeout = False

        self.status = "ready"

    def initialize(self):
        return

    def finalize(self):
        return

    def onInputChange(self, channel, value):
        return

    def onOutputChange(self, channel, value):
        return

    def addStates(self, states):
        for k in states:
            self.states[k] = states[k](k, self)
            self.machine.addState(self.states[k])

            self.states[k].stateEntered.connect(self.stateEntered)
            self.states[k].stateEntered.connect(self.onStateEntered)
            self.states[k].stateReady.connect(self.onStateReady)
            self.states[k].stateExited.connect(self.stateExited)
            self.states[k].stateExited.connect(self.onStateExited)

    def setInitialState(self, state):
        self.machine.setInitialState(self.getState(state))

    def getState(self, state):
        return self.states[state]

    @Property(list)
    def events(self):
        return list(sorted(self._events.keys()))

    @Slot(EventBoolean)
    def getEvent(self, name):
        return self._events[name]

    @Slot()
    def updateParams(self, params):
        self.params.update(params)

    @Slot()
    def startProtocol(self):
        self.initialize()
        self.clearOutputRequested.emit()
        self.clearLEDRequested.emit()
        self.timer.start()
        self.machine.start()
        # self.inputChanged.connect(self.onInputChange)
        # self.outputChanged.connect(self.onOutputChange)
        self.protocolStarted.emit()
        self.status = "running"

    @Slot()
    def stopProtocol(self):
        self.finalize()
        # self.inputChanged.disconnect(self.onInputChange)
        # self.outputChanged.disconnect(self.onOutputChange)
        self.timer.stop()
        self.machine.stop()
        self.protocolStopped.emit()
        ## enabling randomly crashes during stopping
        # self.clearOutputRequested.emit()
        # self.clearLEDRequested.emit()
        self.status = "stopped"

    def onTimeout(self):
        self.is_timeout = True
        self.timeout.emit()

    def isTimeout(self):
        return self.is_timeout

    # @Slot()
    # def pause(self):
    #     if self.status != "running":
    #         return

    #     self.prtcTimer.pause()
    #     ## TODO
    #     self.status = "paused"

    @Slot()
    def finishProtocol(self):
        print("called ")
        self.finalize()
        # self.inputChanged.disconnect(self.onInputChange)
        # self.outputChanged.disconnect(self.onOutputChange)
        self.timer.stop()
        self.dataSaveReady.emit(self.data)
        self.protocolFinished.emit()
        # self.clearOutputRequested.emit()
        # self.clearLEDRequested.emit()
        self.status = "finished"
        print("finished")

    @Slot(str, str)
    def recordCountData(self, table, variable):
        if table in self.data:
            if variable in self.data[table][0]:
                self.data[table][0][variable] += 1
            else:
                self.data[table][0][variable] = 1
        else:
            self.data[table] = [{variable: 1}]
        self.dataUpdated.emit(table, self.data[table])

    def recordData(self, table, record):
        try:
            record["index"] = len(self.data[table])
            self.data[table].append(record)
        except KeyError:
            record["index"] = 0
            self.data[table] = [record]
        self.dataAppended.emit(table, record)

    @Slot(result=dict)
    def getData(self):
        return self.data

    @Slot()
    def onNewData(self, tblname, datadict):
        if tblname in self.data:
            # datadict["index"] = len(self.data[tblname])
            self.data[tblname].append(datadict)
        else:
            datadict["index"] = 0
            self.data[tblname] = [datadict]

    @Slot()
    def onChamberInputChanged(self, port, value):
        if port in self.intputPorts:
            self.inputChanged.emit(self.inputPorts[port], value)

    @Slot()
    def onChamberOutputChanged(self, port, value):
        if port in self.outputPorts:
            self.outputChanged.emit(self.inputPorts[port], value)

    @Slot(str)
    def onStateEntered(self, statename):
        return

    @Slot(str)
    def onStateReady(self, statename):
        return

    @Slot(str)
    def onStateExited(self, statename):
        return

    def clearOutput(self):
        self.clearOutputRequested.emit()

    def updateOutput(self, output):
        self.updateOutputRequested.emit(output)

    def resetOutput(self, output):
        self.resetOutputRequested.emit(output)

    def clearLED(self):
        self.clearLEDRequested.emit()

    def updateLED(self, output):
        self.updateLEDRequested.emit(output)

    def resetLED(self, output):
        self.resetLEDRequested.emit(output)

    def triggerVibration(self):
        self.triggerVibrationRequested.emit()


class Timer(QObject):
    timeout = Signal()

    def __init__(self):
        super().__init__()
        self.status = "stopped"
        self.t0 = 0
        self.t_elapsed = 0

        self.timer = QTimer()
        self.timer_duration = 0

    def setDuration(self, duration):
        self.timer_duration = duration

    def start(self):
        if self.status != "stopped":
            return

        if self.timer_duration > 0:
            self.timer.setInterval(self.timer_duration * 1e3)
            self.timer.timeout.connect(self.timeout)
            self.timer.start()

        self.t0 = time.time()
        self.t_elapsed = 0

        self.status = "running"

    def pause(self):
        if self.status != "running":
            return

        self.t_elapsed += time.time() - self.t0
        self.timer.stop()
        self.status = "paused"

    def resume(self):
        if self.status != "paused":
            return
        self.t0 = time.time()
        ## does make sense only for single-shot timer
        self.timer = QTimer()
        self.timer.setInterval((self.timer_duration - self.t_elapsed) * 1e3)
        self.timer.start()
        self.status = "running"

    def stop(self):
        if self.status == "running":
            self.t_elapsed += time.time() - self.t0
        self.status = "stopped"
        self.timer.timeout.disconnect(self.timeout)
        self.timer.stop()

    def elapsed(self):
        if self.status == "running":
            return round(self.t_elapsed + (time.time() - self.t0), 6)
        else:
            return round(self.t_elapsed, 6)
