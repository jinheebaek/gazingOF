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
        hab_duration=5,
        iti_duration=[3, 4, 5, 6, 7],
        cue_duration=10,
        trial_autostart=False,
        reward_clear_on_autostart=False,
        reward_duration=10,
        reward_duration_random=False,
        reward_nose_wo_cue=False,
        wait_reward_consumption=True,
        initial_reward=False,
        max_trial=100,
        # session_duration_min=1,
        fake_reward_duration=10,
        p_fake_reward_trial=0,
        p_fake_reward_cue=0.5,
        p_random_reward=0,
        fr=1                    # unused
    )

    inp = ["reward_zone", "reward_nose", "nose", "2A", "2B"]
    out = ["reward_light", "reward", "nose", "2B"]
    led = ["reward_center", "reward_surround"]

    def initialize(self):
        self.addStates({
            "habituation": StateHab,
            "ITI": StateITI,
            "cue": StateCue,
            "reward": StateReward,
            "initialreward": StateInitialReward,
            "fakereward": StateFakeReward,
            "randomreward": StateReward,
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
        self.reward_receiving = False

        self.head_in_reward_cup = False

    def finalize(self):
        self.reward_timer.stop()
        self.reward_received_timer.stop()
        # self.pulsepalTriggered.emit(0, False)

    def isLastTrial(self):
        return self.isTimeout() or self.trial >= self.params["max_trial"]

    def onInputChange(self, channel, value):
        if channel == "reward_nose":
            if self.reward_available:
                if value:
                    # self.pulsepalTriggered.emit(0, True)
                    self.reward_received_led_on()
                else:
                    self.updateLED({"reward_center": (0, 0, 0)})
                    self.updateOutput([("reward_light", False)])
                    self.reward_available = False
                    # self.pulsepalTriggered.emit(0, False)
            if value:
                self.head_in_reward_cup = True
            else:
                self.head_in_reward_cup = False

        if self.params["reward_nose_wo_cue"]:
            if channel == "nose" and value:
                self.reward_on()

        if channel == "nose" and value:
            self.triggerVibration()

    def reward_on(self, add_queue=1):
        self.reward_queue += add_queue

        if self.reward_queue > 1 and add_queue:  # reward was on (queue == 1) before called
            return

        self.updateOutput([("reward", True), ("reward_light", True)])
        # self.reward_timer.setInterval(0.25 * 1e3)  # 30 ml syringe
        # self.reward_timer.setInterval(0.57 * 1e3)  # 10 ml syringe

        vol = 10
        syringe_cross_sectional_areal = 3.662  # 30 ml
        # syringe_cross_sectional_areal = 1.635  # 10 ml
        rpm = 3.33
        sec = vol * 1e-3 / (0.19538 * rpm * syringe_cross_sectional_areal / 60)

        self.reward_timer.setInterval(sec * 1e3)  # 10 ml syringe
        self.reward_timer.start()

        if not self.reward_available:
            self.updateLED({"reward_center": (255, 255, 255)})
            self.t_reward_on = time.time()
            self.reward_trial = self.trial
            self.reward_available = True

            if self.head_in_reward_cup:
                self.reward_received_led_on()

    def reward_off(self):
        self.updateOutput([("reward", False)])
        self.reward_queue -= 1
        if self.reward_queue:
            self.reward_on(add_queue=0)

    def reward_received_led_on(self):
        if self.reward_receiving:
            return
        self.reward_receiving = True
        # self.updateOutput([("reward_light", False)])
        self.updateOutput([("reward_light", False), ("reward", False)])  # to make sure
        self.updateLED({"reward_surround": (255, 255, 255)})
        self.recordData("lat2reward", {
            "trial": self.reward_trial,
            "latency": round(time.time() - self.t_reward_on, 6)
        })
        self.reward_received_timer.setInterval(2 * 1e3)
        self.reward_received_timer.start()

    def reward_received_led_off(self):
        if self.params["wait_reward_consumption"]:
            self.updateLED({"reward_surround": (0, 0, 0)})
            # self.updateOutput([("reward_light", False)])
            self.updateOutput([("reward_light", False), ("reward", False)])  # to make sure
        else:
            self.clearLED()
            self.updateOutput([("reward_light", False), ("reward", False)])  # to make sure
            self.reward_available = False
        self.reward_receiving = False


class StateHab(State):
    def initialize(self):
        if self.protocol.params["initial_reward"]:
            self.connectState(self.timeout, "initialreward")
        else:
            self.connectState(self.timeout, "ITI")

    def onEntered(self):
        self.resetOutput([])
        self.clearLED()
        self.startTimer(self.protocol.params["hab_duration"])


class StateInitialReward(State):
    startNewTrial = Signal()

    def initialize(self):
        self.connectState(self.startNewTrial, "ITI")
        self.timeout.connect(self.onTimeout)

    def onInputChange(self, channel, value):
        if channel == "reward_nose" and not value:
            self.startNewTrial.emit()

    def onEntered(self):
        self.protocol.reward_on()
        if self.protocol.params["trial_autostart"]:
            self.startTimer(self.protocol.params["hab_duration"])

    # def onExited(self):
    #     if self.protocol.params["trial_autostart"]:
    #         self.timer.stop()

    def onTimeout(self):
        if self.protocol.params["reward_clear_on_autostart"] and \
           self.protocol.reward_available:
            self.protocol.reward_received_led_on()
            self.updateLED({"reward_center": (0, 0, 0)})
            self.protocol.reward_available = False

        self.startNewTrial.emit()


class StateITI(State):
    startNormalTrial = Signal()
    startFakeTrial = Signal()
    startRandomRewardTrial = Signal()

    def initialize(self):
        self.connectState(self.startNormalTrial, "cue")
        self.connectState(self.startFakeTrial, "fakereward")
        self.connectState(self.startRandomRewardTrial, "reward")
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
        if self.protocol.lastState != "randomreward":
            self.protocol.trial += 1
        self.protocol.iti = dur
        self.protocol.recordCountData("count_trial", "trial")

    def onTimeout(self):
        p_fake = self.protocol.params["p_fake_reward_trial"]
        p_random = self.protocol.params["p_random_reward"]
        if p_fake:
            if np.random.rand() >= p_fake:
                self.startNormalTrial.emit()
            else:
                self.startFakeTrial.emit()
        elif p_random:
            if np.random.rand() >= p_random:
                self.startNormalTrial.emit()
            else:
                self.protocol.reward_on()
                self.startRandomRewardTrial.emit()
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

        if not self.protocol.params["wait_reward_consumption"]:
            self.protocol.reward_received_timer.timeout.connect(self.onRewardReceivedOff)

    def onRewardReceivedOff(self):
        if self.active():
            self.endRewardState()

    def endRewardState(self):
        if self.protocol.isLastTrial():
            self.finishProtocol.emit()
        else:
            self.startNewTrial.emit()

    def onInputChange(self, channel, value):
        if channel == "reward_nose" and not value:
            self.endRewardState()

    def onEntered(self):
        if not self.protocol.params["reward_nose_wo_cue"]:
            self.protocol.reward_on()
        if self.protocol.params["trial_autostart"]:
            if self.protocol.params["reward_duration_random"]:
                lat = np.random.normal(6, 4)
                if lat < 0.5 :
                    lat = 0.5
                if lat > self.protocol.params["reward_duration"]:
                    lat = self.protocol.params["reward_duration"]
                self.startTimer(lat)
            else:
                self.startTimer(self.protocol.params["reward_duration"])

    # def onExited(self):
    #     if self.protocol.params["trial_autostart"]:
    #         self.timer.stop()

    def onTimeout(self):
        if self.protocol.params["reward_clear_on_autostart"] and \
           self.protocol.reward_available:
            self.protocol.reward_received_led_on()
            self.updateLED({"reward_center": (0, 0, 0)})
            # self.clearLED()
            # self.updateOutput([("reward_light", False), ("reward", False)])  # to make sure
            self.protocol.reward_available = False

        self.endRewardState()


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
