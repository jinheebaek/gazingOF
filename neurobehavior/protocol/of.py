from PySide6.QtCore import Signal
from PySide6.QtCore import QTimer
from neurobehavior.protocol import Protocol
from neurobehavior.protocol import State

import time
import numpy as np


class ProtocolOF(Protocol):
    name = "OFL"
    params = dict(
        habituation=3,
        session_duration=8
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

    def finalize(self):
        return
        # self.pulsepalTriggered.emit(0, False)


class StateHab(State):
    def initialize(self):
        self.connectState(self.timeout, "conditioning")

    def onEntered(self):
        self.startTimer(self.protocol.params["habituation"])


class StateCond(State):
    def initialize(self):
        return

    def onEntered(self):
        return
        # self.startTimer(
        #     self.protocol.params["session_duration"] - self.protocol.params["habituation"])

