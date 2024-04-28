#!/usr/bin/env python
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

# from importlib.resources import files

from neurobehavior.session import Session
from neurobehavior.chamber import Chamber
from neurobehavior.sessionlistmodel import SessionListModel
from neurobehavior.videoviewitem import VideoViewItem
from neurobehavior.pulsepal import PulsePal
from neurobehavior.seriallist import SerialList
from neurobehavior.ardio import ArdIO
from neurobehavior.datatablemodel import DataTableModel
from neurobehavior.dbmodels import Base, SessionModel, ChamberModel, DataModel
from neurobehavior.protocol import *
from neurobehavior.neurobehavior import Neurobehavior

def main_gui():
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("JBaek")
    app.setApplicationName("Neurobehavior")
    QQuickStyle.setStyle("Material")
    engine = QQmlApplicationEngine()

    qml_file = Path(__file__).parent / "main.qml"
    # qml_file = files("neurobehavior").joinpath("ui/main.qml")

    engine.load(qml_file)
    app.exec()


if __name__ == "__main__":
    main_gui()