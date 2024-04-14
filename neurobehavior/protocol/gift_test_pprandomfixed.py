from PySide6.QtCore import Slot
from PySide6.QtCore import QTimer
import numpy as np
from neurobehavior.protocol import ProtocolGiftTraining


class ProtocolGiftTestPPRandomFixed(ProtocolGiftTraining):
    name = "GiftStimTestPPRewardFixed"
    params = dict(
        session_duration=900,
        hab_duration=5,
        iti_duration=[3, 4, 5, 6, 7],
        cue_duration=10,
        trial_autostart=True,
        reward_clear_on_autostart=True,
        reward_duration=10,
        reward_duration_random=False,
        reward_nose_wo_cue=False,
        wait_reward_consumption=False,
        initial_reward=False,
        max_trial=100,
        # session_duration_min=1,
        fake_reward_duration=10,
        p_fake_reward_trial=0,
        p_fake_reward_cue=0.5,
        p_random_reward=0,
        fr=1                    # unused
    )

    def initialize(self):
        super().initialize()
        # self.setPulsepalParams.emit(0, 5, 45)
        # self.setPulsepalParams.emit(0, 3600e3, 3600e3)
        self.setPulsepalParams.emit(0, 3e3, 3600e3)
        self.pulsepal = False
        self.ppal_timer = QTimer()
        self.ppal_timer.setInterval(3e3)
        self.ppal_timer.setSingleShot(True)
        self.ppal_timer.timeout.connect(self.ppal_off)

        self.trial_delay = 0
        self.trial_delay = np.random.choice([1, 2, 3], 1)[0]
        self.trial_delay_counter = self.trial_delay
        self.stim_queue = 1     # minimum 1 stim
        self.stim_delay = 0
        self.stim_delay_timer = QTimer()
        self.stim_delay_timer.setSingleShot(True)
        self.stim_delay_timer.timeout.connect(self.ppal_on)

    def finalize(self):
        super().finalize()
        self.pulsepalTriggered.emit(0, False)
        self.pulsepal = False
        self.ppal_timer.timeout.disconnect(self.ppal_off)
        self.ppal_timer.stop()
        self.stim_delay_timer.timeout.disconnect(self.ppal_on)
        self.stim_delay_timer.stop()

    def ppal_on(self):
        self.pulsepalTriggered.emit(0, True)
        self.pulsepal = True
        self.ppal_timer.start()
        self.recordData("delayed_stim", {
            "timestamp": self.timer.elapsed(),
            "trial": self.trial,
            "stim_delay": self.stim_delay,
            "trial_delay": int(self.trial_delay)  # np.int64 to int for JSON
        })
        self.stim_queue -= 1
        if self.stim_queue:
            self.trial_delay = np.random.choice([1, 2, 3], 1)[0]
            self.trial_delay_counter = self.trial_delay

    def ppal_off(self):
        self.pulsepalTriggered.emit(0, False)
        self.pulsepal = False

    def delayed_stim(self):
        # iti = min(self.params["iti_duration"])
        iti = self.iti
        cue_duration = self.params["cue_duration"]
        self.stim_delay = round(
            1 + ((iti + cue_duration - 5) * np.random.rand()), 6
            # (iti - 3) * np.random.rand(), 6
        )
        self.stim_delay_timer.setInterval(self.stim_delay * 1e3)
        self.stim_delay_timer.start()

    @Slot(str)
    def onStateEntered(self, statename):
        if statename == "reward":
            self.stim_delay_timer.stop()
            self.stim_queue += 1
            self.trial_delay = np.random.choice([1, 2, 3], 1)[0]
            self.trial_delay_counter = self.trial_delay

    @Slot(str)
    def onStateReady(self, statename):
        ## use onStateReady to wait for self.iti update
        if statename == "ITI":
            self.trial_delay_counter = max(0, self.trial_delay_counter - 1)
            if self.stim_queue and self.trial_delay_counter == 0:
                self.delayed_stim()
