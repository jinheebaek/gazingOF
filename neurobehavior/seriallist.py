from PySide6.QtCore import Signal, Slot, Property
from PySide6.QtCore import QObject, qDebug, QUrl
from PySide6.QtQml import QmlElement
from neurobehavior.protocol import *

import serial.tools.list_ports

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class SerialList(QObject):
    portsListChanged = Signal(list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ports = []
        self._cbox_list = []
        self.refresh()

    def refresh(self):
        self._ports = []
        self._cbox_list = []

        for port, desc, hid in serial.tools.list_ports.comports():
            if hid == "n/a":
                continue

            self._ports.append(port)
            self._cbox_list.append("{} ({})".format(port, desc))

    @Property(list)
    def ports(self):
        return self._ports

    # @Property(list)
    def cbox_list(self):
        return self._cbox_list
    portsList = Property(list, cbox_list, notify=portsListChanged)
