from PySide6.QtCore import Signal, Slot
from PySide6.QtCore import QTimer
from neurobehavior.protocol import Protocol
from neurobehavior.protocol import State

import time
import numpy as np


class ProtocolOF(Protocol):
    name = "OFL"
    params = dict(
        habituation=3,
        session_duration=240,
        gazing_angle_threshold=90
    )

    inp = [""]
    out = [""]
    led = [""]

    def initialize(self):
        self.addStates({
            "habituation": StateHab,
            "conditioning": StateCond
        })
        self.setInitialState("habituation")

        self.timer.setDuration(self.params["session_duration"])
        self.timer.timeout.connect(self.finishProtocol)
        self.is_gazing = False

        # self.setPulsepalParams.emit(0, 3600e3, 3600e3)
        # self.pulsepal = False
        # self.ardIOTriggered.emit(0, False)
        # self.ardIOTriggered.emit(1, False)  
        self.ardIOCleared.emit()  

    def finalize(self):
        self.gazingAngleUpdated.disconnect()
        # self.pulsepalTriggered.emit(0, False)
        # self.ardIOTriggered.emit(0, False)
        # self.ardIOTriggered.emit(1, False)  
        self.ardIOCleared.emit()  


class StateHab(State):
    def initialize(self):
        self.connectState(self.timeout, "conditioning")

    def onEntered(self):
        self.protocol.ardIOTriggered.emit(0, True)
        self.startTimer(self.protocol.params["habituation"])


class StateCond(State):
    def initialize(self):
        self.protocol.gazingAngleUpdated.connect(self.onGazingAngleUpdated)
        self.gazingCtrl = False

    def finalize(self):
        self.protocol.gazingAngleUpdated.disconnect()

    def onEntered(self):
        self.gazingCtrl = True
        # self.startTimer(
        #     self.protocol.params["session_duration"] - self.protocol.params["habituation"])

    @Slot(float)
    def onGazingAngleUpdated(self, angle):
        if not self.gazingCtrl:
            return
        
        if not self.protocol.is_gazing and angle < self.protocol.params["gazing_angle_threshold"]:
            print("laser on")
            # self.protocol.pulsepalTriggered.emit(0, True)
            # self.protocol.pulsepal = True
            self.protocol.ardIOTriggered.emit(1, True)   
            self.protocol.is_gazing = True
        if angle >= self.protocol.params["gazing_angle_threshold"] and self.protocol.is_gazing:
            print("laser off")
            # self.protocol.pulsepalTriggered.emit(0, False)
            # self.protocol.pulsepal = False
            self.protocol.ardIOTriggered.emit(1, False)  
            self.protocol.is_gazing = False

    def onExited(self):
        self.gazingCtrl = False
        self.protocol.ardIOTriggered.emit(0, False)

