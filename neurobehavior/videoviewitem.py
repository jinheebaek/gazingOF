from PySide6.QtCore import Signal, Slot, Property
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QImage
from PySide6.QtQml import QmlElement
from PySide6.QtQuick import QQuickPaintedItem

from neurobehavior.chamber import Chamber

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class VideoViewItem(QQuickPaintedItem):
    chamberChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._frame = QImage(1024, 480, QImage.Format_RGB32)
        self._chamber = None
        self._conVideoCtrl = None

        self.chamberChanged.connect(self.updateVideoConnection)
        self.visibleChanged.connect(self.updateVideoConnection)

    def paint(self, painter):
        painter.drawImage(0, 0, self._frame)
    
    @Slot(QImage)
    def updateFrame(self, image):
        self._frame = image.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        self.update()

    def getChamber(self):
        return self._chamber

    def setChamber(self, chamber):
        if self._chamber:
            self._chamber.videoCtrlChanged.disconnect(
                self.updateVideoConnection)

        self._chamber = chamber
        if self._chamber:
            self._chamber.videoCtrlChanged.connect(self.updateVideoConnection)
        self.chamberChanged.emit()

    chamber = Property(Chamber, getChamber, setChamber, notify=chamberChanged)

    def updateVideoConnection(self):
        if self._conVideoCtrl:
            QObject.disconnect(self._conVideoCtrl)
            self._conVideoCtrl = None

        if self.isVisible() and self._chamber and self._chamber.videoCtrl:
            self._conVideoCtrl = self._chamber.videoCtrl.frameUpdated.connect(
                self.updateFrame)
