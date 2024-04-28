from PySide6.QtCore import Signal, Slot, qDebug
from PySide6.QtCore import QObject, Property
from PySide6.QtQml import QmlElement

from pulsepal.PulsePal import PulsePalObject
from neurobehavior.protocol.event import EventBoolean

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class PulsePal(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pp = None

        # self.pulse_dur = 5      # ms
        # self.pulse_intv = 45    # ms
        # self.pulse_dur = 0      # ms
        # self.pulse_intv = 0    # ms

        # self.connect()
        # self.__setup__()
        self.status = [0, 0, 0, 0]

    def connect(self, port="COM3"):
        try:
            self.pp = PulsePalObject(port)
            print("pulsepal connected")
        except:
            pass
            ## TODO: activate QTimer to retry connect

    @Slot(str, int, bool)
    def onPulsepalTriggered(self, cmbrname, evtid, value):
        target_ch = [0] * 4
        if evtid == 0:
            ch = int(cmbrname.lstrip("chamber"))

            if value:
                # print("##### pulsepal channel {} triggered".format(ch))
                # self.pp.programOutputChannelParam("phase1Duration", ch, self.pulse_dur * 1e-3)
                # self.pp.programOutputChannelParam("interPulseInterval", ch, self.pulse_intv * 1e-3)
                self.status[ch-1] = 1
            else:
                # print("##### pulsepal channel {} off".format(ch))
                self.status[ch-1] = 0

            target_ch[ch-1] = 1
        self.pp.abortPulseTrains()
        self.pp.triggerOutputChannels(*self.status)
        # self.pp.triggerOutputChannels(*target_ch)

    @Slot(str, int, float, float)
    def setPulsepalParams(self, cmbrname, evtid, dur, intv):
        if evtid == 0:
            ch = int(cmbrname.lstrip("chamber"))

            self.pp.programOutputChannelParam("isBiphasic", ch, 0)
            self.pp.programOutputChannelParam("phase1Voltage", ch, 5)
            self.pp.programOutputChannelParam("phase1Duration", ch, dur * 1e-3)
            self.pp.programOutputChannelParam("interPulseInterval", ch, intv * 1e-3)
            self.pp.programOutputChannelParam("pulseTrainDuration", ch, 3600)

    # def __setup__(self):
    #     if not self.pp:
    #         return

    #     for i in range(1, 5):
    #         self.pp.programOutputChannelParam("isBiphasic", i, 0)
    #         self.pp.programOutputChannelParam("phase1Voltage", i, 5)
    #         # self.pp.programOutputChannelParam("phase1Duration", i, self.pulse_dur * 1e-3)
    #         # self.pp.programOutputChannelParam("interPulseInterval", i, self.pulse_intv * 1e-3)
    #         # self.pp.programOutputChannelParam("phase1Duration", i, 1)
    #         # self.pp.programOutputChannelParam("interPulseInterval", i, 3599)
    #         self.pp.programOutputChannelParam("pulseTrainDuration", i, 3600)
    #         # self.pp.setContinuousLoop(i, 1)  # assume that pulseTrainDuration is multiple of dur + intv
    #     # self.pp.triggerOutputChannels(1, 1, 1, 1)
    #     # self.pp.abortPulseTrains()
