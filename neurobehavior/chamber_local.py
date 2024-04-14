from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtCore import QThread, QBitArray
from PySide6.QtCore import qDebug, qWarning
from PySide6.QtQml import QmlElement

import math
from neurobehavior.ardio import ArdIO
from neurobehavior.session import Session
from neurobehavior.videoctrl import VideoCtrl
from neurobehavior.chamber import Chamber

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ChamberLocal(Chamber):

    ## called in the main thread
    def __init__(self, config, parent=None):
        super().__init__(config, parent)

    ## called in a chamber thread
    @Slot()
    def initialize(self):
        super().initialize()
        self.onConnected()

