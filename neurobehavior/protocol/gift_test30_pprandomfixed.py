from PySide6.QtCore import Slot
# from neurobehavior.protocol import ProtocolGiftTraining
from neurobehavior.protocol import ProtocolGiftTestPPRandomFixed


class ProtocolGiftTest30PPRandomFixed(ProtocolGiftTestPPRandomFixed):
    name = "GiftStimTest30PPRandomFixed"
    params = dict(
        session_duration=1800,
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
        max_trial=200,
        # session_duration_min=1,
        fake_reward_duration=10,
        p_fake_reward_trial=0,
        p_fake_reward_cue=0.5,
        p_random_reward=0,
        fr=1                    # unused
    )
