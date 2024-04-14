from PySide6.QtCore import Signal
from PySide6.QtCore import QTimer
from neurobehavior.protocol import Protocol
from neurobehavior.protocol import State

import time
import numpy as np


class ProtocolGiftTraining(Protocol):
    name = "GiftStimTraining"
    params = dict(
        session_duration=1200,
        hab_duration=10,
        iti_duration=5,
        cue_duration=10,
        trial_autostart=False,
        reward_clear_on_autostart=False,
        reward_duration=10,
        reward_nose_wo_cue=False,
        max_trial=100,
        # session_duration_min=1,
        fake_reward_duration=10,
        p_fake_reward_trial=0.1,
        p_fake_reward_cue=0.5,
        fr=1                    # unused
    )
    inp = ["reward_zone", "reward_nose", "nose", "2A", "2B"]
    out = ["reward", "nose", "2A", "2B"]
    led = ["reward_center", "reward_surround"]

    def initialize(self):
        self.addStates({
            "habituation": StateHab,
            "ITI": StateITI,
            "cue": StateCue,
            "reward": StateReward,
            "fakereward": StateFakeReward,
        })
        self.setInitialState("habituation")

        self.trial = 0
        self.iti = 0
        self.cue_duration = 0
        self.timer.setDuration(
            self.params["session_duration"])

        self.reward_timer = QTimer()
        self.reward_timer.setSingleShot(True)
        self.reward_timer.timeout.connect(self.reward_off)
        self.reward_available = False
        self.reward_trial = 0
        self.reward_queue = 0

        self.t_reward_on = 0
        self.reward_received_timer = QTimer()
        self.reward_received_timer.setSingleShot(True)
        self.reward_received_timer.timeout.connect(self.reward_received_led_off)

    def isLastTrial(self):
        return self.isTimeout() or self.trial >= self.params["max_trial"]

    def onInputChange(self, channel, value):
        if channel == "reward_nose":
            if self.reward_available:
                if value:
                    self.reward_received_led_on()
                else:
                    self.updateLED({"reward_center": (0, 0, 0)})
                    self.reward_available = False

        if self.params["reward_nose_wo_cue"]:
            if channel == "nose" and value:
                self.reward_on()

    def reward_on(self, add_queue=1):
        self.reward_queue += add_queue

        if self.reward_queue > 1 and add_queue:  # reward was on (queue == 1) before called
            return

        self.updateOutput([("reward", True)])
        self.reward_timer.setInterval(1 * 1e3)
        self.reward_timer.start()

        if not self.reward_available:
            self.updateLED({"reward_center": (255, 255, 255)})
            self.t_reward_on = time.time()
            self.reward_trial = self.trial
            self.reward_available = True

    def reward_off(self):
        self.updateOutput([("reward", False)])
        self.reward_queue -= 1
        if self.reward_queue:
            self.reward_on(add_queue=0)

    def reward_received_led_on(self):
        self.updateLED({"reward_surround": (255, 255, 255)})
        self.recordData("lat2reward", {
            "trial": self.reward_trial,
            "latency": round(time.time() - self.t_reward_on, 6)
        })
        self.reward_received_timer.setInterval(2 * 1e3)
        self.reward_received_timer.start()

    def reward_received_led_off(self):
        self.updateLED({"reward_surround": (0, 0, 0)})


class StateHab(State):
    def initialize(self):
        self.connectState(self.timeout, "ITI")

    def onEntered(self):
        self.resetOutput([])
        self.startTimer(self.protocol.params["hab_duration"])


class StateITI(State):
    startNormalTrial = Signal()
    startFakeTrial = Signal()

    def initialize(self):
        self.connectState(self.startNormalTrial, "cue")
        self.connectState(self.startFakeTrial, "fakereward")
        self.timeout.connect(self.onTimeout)

    def onEntered(self):
        dur = self.protocol.params["iti_duration"]
        if isinstance(dur, list):
            dur = np.random.choice(dur, 1)[0]
        elif isinstance(dur, tuple):
            dur = dur[0] + ((dur[1] - dur[0]) * np.random.rand())

        ## np int64, etc cannot be json serialized
        if isinstance(dur, np.integer):
            dur = int(dur)
        if isinstance(dur, np.floating):
            dur = float(dur)

        self.startTimer(dur)
        self.protocol.trial += 1
        self.protocol.iti = dur
        self.protocol.recordCountData("count_trial", "trial")

    def onTimeout(self):
        p = self.protocol.params["p_fake_reward_trial"]
        if p:
            if np.random.rand() >= p:
                self.startNormalTrial.emit()
            else:
                self.startFakeTrial.emit()
        else:
            self.startNormalTrial.emit()

class StateCue(State):
    correctChoice = Signal()
    startNewTrial = Signal()
    finishProtocol = Signal()

    def initialize(self):
        self.connectState(self.startNewTrial, "ITI")
        self.connectState(self.correctChoice, "reward")
        self.connectState(self.finishProtocol, "final_state")
        self.timeout.connect(self.onTimeout)
        self.t_cue_on = 0

    def onEntered(self):
        cue_dur = self.protocol.params["cue_duration"]

        self.updateOutput([["nose", True]])
        self.startTimer(cue_dur)
        self.protocol.cue_duration = cue_dur
        self.t_cue_on = time.time()

    def onInputChange(self, channel, value):
        if channel == "nose" and value:
            self.protocol.recordData("trial", {
                "timestamp": self.protocol.timer.elapsed(),
                "trial": self.protocol.trial,
                "iti": self.protocol.iti,
                "cue_duration": self.protocol.cue_duration,
                "result": "correct"
            })
            self.protocol.recordData("lat2resp", {
                "trial": self.protocol.trial,
                "latency": round(time.time() - self.t_cue_on, 6)
            })
            self.protocol.recordCountData("count_trial", "correct")
            self.correctChoice.emit()

    def onTimeout(self):
        self.protocol.recordData("trial", {
            "timestamp": self.protocol.timer.elapsed(),
            "trial": self.protocol.trial,
            "iti": self.protocol.iti,
            "cue_duration": self.protocol.cue_duration,
            "result": "omission"
        })
        self.protocol.recordCountData("count_trial", "omission")

        if self.protocol.isLastTrial():
            self.finishProtocol.emit()
        else:
            self.startNewTrial.emit()

    def onExited(self):
        self.updateOutput([("nose", False)])


class StateReward(State):
    startNewTrial = Signal()
    finishProtocol = Signal()

    def initialize(self):
        self.connectState(self.startNewTrial, "ITI")
        self.connectState(self.finishProtocol, "final_state")
        self.timeout.connect(self.onTimeout)

    def onInputChange(self, channel, value):
        if channel == "reward_nose" and not value:
            if self.protocol.isLastTrial():
                self.finishProtocol.emit()
            else:
                self.startNewTrial.emit()

    def onEntered(self):
        if not self.protocol.params["reward_nose_wo_cue"]:
            self.protocol.reward_on()
        if self.protocol.params["trial_autostart"]:
            self.startTimer(self.protocol.params["reward_duration"])

    def onExited(self):
        if self.protocol.params["trial_autostart"]:
            self.timer.stop()

    def onTimeout(self):
        if self.protocol.params["reward_clear_on_autostart"] and \
           self.protocol.reward_available:
            self.protocol.reward_received_led_on()
            self.updateLED({"reward_center": (0, 0, 0)})
            self.protocol.reward_available = False

        if self.protocol.isLastTrial():
            self.finishProtocol.emit()
        else:
            self.startNewTrial.emit()


class StateFakeReward(State):
    startNewTrial = Signal()
    finishProtocol = Signal()

    def initialize(self):
        self.connectState(self.startNewTrial, "ITI")
        self.connectState(self.finishProtocol, "final_state")
        # self.timeout.connect(self.onTimeout)

    def onInputChange(self, channel, value):
        # if not self.is_lat_recorded and value and \
        #     (channel in ["reward_nose", "reward_zone"]):
        #     self.protocol.recordData("lat2fake", {
        #         "trial": self.protocol.trial,
        #         "latency": round(time.time() - self.t_state_on, 6)
        #     })
        #     self.is_lat_recorded = True
        #     if self.is_timeout:
        #         if self.protocol.isLastTrial():
        #             self.finishProtocol.emit()
        #         else:
        #             self.startNewTrial.emit()

        # if channel == "reward_nose" and not value:
        #     if self.protocol.isLastTrial():
        #         self.finishProtocol.emit()
        #     else:
        #         self.startNewTrial.emit()

        if (channel in ["reward_nose", "reward_zone"]) and value:
            self.protocol.recordData("lat2fake", {
                "trial": self.protocol.trial,
                "reward_cue": self.fake_cue,
                "latency": round(time.time() - self.t_state_on, 6)
            })
            if self.protocol.isLastTrial():
                self.finishProtocol.emit()
            else:
                self.startNewTrial.emit()

    def onEntered(self):
        p = self.protocol.params["p_fake_reward_cue"]
        if np.random.rand() >= p:
            self.fake_cue = False
            result = "fakereward_off"
        else:
            self.fake_cue = True
            result = "fakereward_on"

        # self.startTimer(self.protocol.params["fake_reward_duration"])
        # self.is_timeout = False
        # self.is_lat_recorded = False
        self.t_state_on = time.time()
        if self.fake_cue:
            self.updateLED({"reward_center": (255, 255, 255)})
        self.protocol.recordData("trial", {
            "timestamp": self.protocol.timer.elapsed(),
            "trial": self.protocol.trial,
            "iti": self.protocol.iti,
            "cue_duration": 0,
            "result": result
        })
        self.protocol.recordCountData("count_trial", result)

    def onExited(self):
        # self.timer.stop()
        self.clearLED()

    # def onTimeout(self):
    #     if self.is_lat_recorded:
    #         if self.protocol.isLastTrial():
    #             self.finishProtocol.emit()
    #         else:
    #             self.startNewTrial.emit()
    #     self.is_timeout = True
