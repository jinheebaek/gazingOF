from PySide6.QtCore import Signal, Slot
from PySide6.QtCore import QTimer
from neurobehavior.protocol import Protocol
from neurobehavior.protocol import State

import time
import numpy as np


class ProtocolOF(Protocol):
    name = "OFL"
    params = dict(
        habituation=300,
        session_duration=540,
        gazing_angle_threshold=60
    )

    inp = [""]
    out = [""]
    led = [""]

    def initialize(self):
        super().initialize()
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

        self.shock_intv_timer = QTimer()
        self.shock_intv_timer.setInterval(8e3)
        self.shock_intv_timer.setSingleShot(True)
        self.shock_intv_timer.timeout.connect(self.shock_on)

        self.shock_dur_timer = QTimer()
        self.shock_dur_timer.setInterval(2e3)
        self.shock_dur_timer.setSingleShot(True)
        self.shock_dur_timer.timeout.connect(self.shock_off)

    def finalize(self):
        super().finalize()
        self.gazingAngleUpdated.disconnect()
        # self.pulsepalTriggered.emit(0, False)
        # self.ardIOTriggered.emit(0, False)
        # self.ardIOTriggered.emit(1, False)  
        self.shock_intv_timer.timeout.disconnect(self.shock_on)
        self.shock_intv_timer.stop()
        self.shock_dur_timer.timeout.disconnect(self.shock_off)
        self.shock_dur_timer.stop()
        self.ardIOCleared.emit()  
    
    def shock_on(self):
        print(self.timer.elapsed(), ": shocker on")
        self.ardIOTriggered.emit(2, True) 
        self.shock_dur_timer.start()
    
    def shock_off(self):
        print(self.timer.elapsed(), ": shocker off")
        self.ardIOTriggered.emit(2, False) 
        self.shock_intv_timer.start()


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
        self.protocol.shock_on()
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
            self.protocol.recordData("gazing", {
                "timestamp": self.protocol.timer.elapsed(),
                "event": "onset"
            })
        if angle >= self.protocol.params["gazing_angle_threshold"] and self.protocol.is_gazing:
            print("laser off")
            # self.protocol.pulsepalTriggered.emit(0, False)
            # self.protocol.pulsepal = False
            self.protocol.ardIOTriggered.emit(1, False)  
            self.protocol.is_gazing = False
            self.protocol.recordData("gazing", {
                "timestamp": self.protocol.timer.elapsed(),
                "event": "offset"
            })

    def onExited(self):
        self.gazingCtrl = False
        self.protocol.ardIOTriggered.emit(0, False)

