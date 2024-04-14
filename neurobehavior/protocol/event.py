from PySide6.QtCore import Signal, Slot, qDebug, QObject, Property


class EventBoolean(QObject):
    stateChanged = Signal(bool)
    activated = Signal()
    deactivated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = "eventname"
        self._state = False

    def getState(self):
        return self._state
    def setState(self, val):
        if not self._state == val:
            self._state = val
            qDebug("Boolean event {} set to {}".format(self.name, val))
            self.stateChanged.emit(val)
            if val:
                self.activated.emit()
            else:
                self.deactivated.emit()
    state = Property(int, getState, setState)

    @Slot()
    def setOn(self):
        self.state = True

    @Slot()
    def setOff(self):
        self.state = False

    @Slot()
    def toggle(self):
        if self.state:
            self.state = False
        else:
            self.state = True
