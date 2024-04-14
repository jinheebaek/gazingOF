from PySide6.QtCore import Slot
from neurobehavior.protocol.gift import *


class ProtocolGiftTestSelfPPSession(ProtocolGiftTraining):
    name = "GiftStimTestSelfPPSession"
    params = dict(
        session_duration=600,
        hab_duration=5,
        iti_duration=[3, 4, 5, 6, 7],
        cue_duration=10,
        trial_autostart=False,
        reward_clear_on_autostart=False,
        reward_duration=10,
        reward_nose_wo_cue=False,
        wait_reward_consumption=True,
        initial_reward=False,
        max_trial=100,
        fake_reward_duration=10,
        p_fake_reward_trial=0,
        p_fake_reward_cue=0.5,
        p_random_reward=0,
        fr=1
    )

    def initialize(self):
        super().initialize()
        self.setPulsepalParams.emit(0, 0, 0)

    def finalize(self):
        super().finalize()
        self.pulsepalTriggered.emit(0, False)

    @Slot(str)
    def onStateExited(self, statename):
        if statename == "habituation":
            self.pulsepalTriggered.emit(0, True)
