from neurobehavior.protocol import ProtocolGiftTraining


class ProtocolGiftTestSelf(ProtocolGiftTraining):
    name = "GiftStimTestSelf"
    params = dict(
        session_duration=300,
        hab_duration=5,
        iti_duration=[5, 6, 7, 8, 9, 10],
        cue_duration=10,
        trial_autostart=False,
        reward_clear_on_autostart=False,
        reward_duration=10,
        reward_nose_wo_cue=False,
        max_trial=100,
        fake_reward_duration=10,
        p_fake_reward_trial=0,
        p_fake_reward_cue=0.5,
        fr=1
    )
