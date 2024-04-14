from PySide6.QtCore import Slot
from PySide6.QtCore import QTimer
import numpy as np
from neurobehavior.protocol import ProtocolGiftTraining


class ProtocolGiftTestPPITICue(ProtocolGiftTraining):
    name = "GiftStimTestPPITICue"
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
        self.setPulsepalParams.emit(0, 4e3, 1e3)
        self.pulsepal = False

        self.ppal_intv_timer = QTimer()
        self.ppal_intv_timer.setInterval(1e3)  # pulse interval
        self.ppal_intv_timer.setSingleShot(True)
        self.ppal_intv_timer.timeout.connect(self.ppal_on)

        self.ppal_dur_timer = QTimer()
        self.ppal_dur_timer.setInterval(3e3)  # pulse duration
        self.ppal_dur_timer.setSingleShot(True)
        self.ppal_dur_timer.timeout.connect(self.ppal_off)

    def finalize(self):
        super().finalize()
        self.pulsepalTriggered.emit(0, False)
        self.ppal_intv_timer.timeout.disconnect(self.ppal_on)
        self.ppal_intv_timer.stop()
        self.ppal_dur_timer.timeout.disconnect(self.ppal_off)
        self.ppal_dur_timer.stop()

    @Slot(str)
    def onStateEntered(self, statename):
        if statename == "ITI" and not self.pulsepal:
            self.ppal_on()
            self.pulsepal = True
        elif statename == "reward" and self.pulsepal:
            self.ppal_intv_timer.stop()
            self.ppal_dur_timer.stop()
            self.pulsepalTriggered.emit(0, False)
            self.pulsepal = False

    def ppal_on(self):
        self.pulsepalTriggered.emit(0, True)
        self.ppal_dur_timer.start()

    def ppal_off(self):
        self.pulsepalTriggered.emit(0, False)
        self.ppal_intv_timer.start()
