from PySide6.QtCore import Signal, Slot, Property
from PySide6.QtCore import QObject
from PySide6.QtCore import QTimer
from PySide6.QtCore import qDebug, qWarning
from PySide6.QtQml import QmlElement

import os
import time
import json
import pandas as pd

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Session(QObject):
    nameChanged = Signal(str)
    statusChanged = Signal(str, str)
    durationChanged = Signal()
    elapsedTimeChanged = Signal()
    sessionDataChanged = Signal(dict)
    sessionStarted = Signal()
    sessionStopped = Signal()
    sessionFinished = Signal()
    dataRootChanged = Signal()
    protocolChanged = Signal()
    saveData = Signal(str, str, str, str)

    def __init__(self, app, sessionData):
        super().__init__(app)
        self.app = app
        self.sessionData = sessionData
        sessionParams = sessionData["sessionParams"]
        self.sessionParams = sessionParams

        self._dataRoot = sessionParams["dataRoot"]

        self.t0 = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.elapsedTimeChanged)
        self.timer.setInterval(1e3)

        self.chamber_subjects = {}
        for cmbr, sbj in zip(sessionParams["chambers"], sessionParams["subjects"]):
            self.chamber_subjects[cmbr] = sbj

        self.chambers = {}
        for cmbrname in sessionParams["chambers"]:
            self.chambers[cmbrname] = app.chambers[cmbrname]

    @Slot(result=str)
    def getName(self):
        return self.sessionData["name"]

    @Slot(str)
    def setName(self, name):
        self.sessionData["name"] = name
        self.nameChanged.emit(self.sessionData["name"])

    name = Property(str, getName, setName, notify=nameChanged)

    @Slot(result=str)
    def getStatus(self):
        return self.sessionData["status"]

    @Slot(str)
    def setStatus(self, status):
        if status not in ("ready", "running", "completed"):
            qWarning("Invalid session status value: {}".format(status))
            return
        self.sessionData["status"] = status
        self.statusChanged.emit(self.name, self.sessionData["status"])
        self.sessionDataChanged.emit(self.sessionData)

    status = Property(str, getStatus, setStatus, notify=statusChanged)

    @Property(str, notify=dataRootChanged)
    @Slot(result=str)
    def dataRoot(self):
        return self._dataRoot

    @Slot(result="QVariant")
    def getChamberSubjects(self):
        return self.chamber_subjects

    @Slot(result=str)
    @Slot(str, result=str)
    def getDescription(self, desctype="short"):
        protocol = self.sessionData["protocol"]
        sparams = self.sessionData["sessionParams"]
        pparams = self.sessionData["protocolParams"]

        if desctype == "short":
            desc_short = "{}<br>".format(protocol)
            for c, s in zip(sparams["chambers"], sparams["subjects"]):
                desc_short += "<b>{}</b>: {}, ".format(c, s)
            desc_short = desc_short[:-2]

            return desc_short

        elif desctype == "long":
            desc_long = "<b>Protocol</b>: {}<br>".format(protocol)
            for k in sparams:
                desc_long += "<b>{}</b>: {}, ".format(k, sparams[k])
            for k in pparams:
                desc_long += "<b>{}</b>: {}, ".format(k, pparams[k])
            desc_long = desc_long[:-2]

            return desc_long

        else:
            return ""

    @Property(float, notify=durationChanged)
    @Slot(result=float)
    def duration(self):
        return self.sessionData["protocolParams"]["session_duration"]

    @Property(float, notify=elapsedTimeChanged)
    @Slot(result=float)
    def elapsedTime(self):
        if self.status == "running":
            return time.time() - self.t0
        else:
            return 0

    @Slot()
    def startSession(self):
        if self.status != "ready":
            qWarning("Trying to start a session not ready - {}".format(self.name))
            return

        protocol_name = self.sessionData["protocol"]
        protocol_params = self.sessionData["protocolParams"]
        Protocol = self.app.protocolSupported[protocol_name]
        for cmbrname in self.chambers:
            cmbr = self.chambers[cmbrname]
            self.app.chamberStartSession.emit(
                cmbrname, self, Protocol, protocol_params)
            cmbr.videoCtrl.recordStart(self)
        self.t0 = time.time()
        self.timer.start()
        self.status = "running"
        self.sessionStarted.emit()
        qDebug("session started")

    @Slot()
    def stopSession(self):
        if self.status != "running":
            qWarning("Trying to stop a session not running - {}".format(self.name))
            return

        for cmbrname in self.chambers:
            cmbr = self.chambers[cmbrname]
            cmbr.videoCtrl.recordStop()

        self.timer.stop()
        self.status = "ready"
        self.sessionStopped.emit()
        qDebug("session stopped")

    @Slot(str)
    def onChamberFinished(self, cmbrname):
        cmbr = self.chambers[cmbrname]
        cmbr.videoCtrl.recordStop()

        for cmbrname in self.chambers:
            cmbr = self.chambers[cmbrname]
            if cmbr.status == "running":
                return
        self.finishSession()

    @Slot(dict)
    # def onDataSaveReady(self, chambername, data):
    def onDataSaveReady(self, data):
        chambername = self.sender().name
        sbj = self.chamber_subjects[chambername]
        self.saveData.emit(
            self.name, chambername, sbj, json.dumps(data)
        )
        for k in data:
            dframe = pd.DataFrame(data[k])
            if "index" in dframe:
                dframe = dframe.set_index("index")

            idx = self.sessionParams["subjects"].index(sbj)
            exp = self.sessionParams["experiments"][idx]
            datafile = self.app.makeDataPath(self.dataRoot, self.name, sbj, exp)

            if not os.path.exists(os.path.dirname(datafile)):
                os.makedirs(os.path.dirname(datafile))

            try:
                dframe.to_hdf(datafile, k, format="table")
            except:
                dframe.to_csv(datafile.replace(".h5", "_{}.csv".format(k)),
                              index=False)

    @Slot(result=bool)
    def isDataExists(self):
        for sbj, exp in zip(self.sessionParams["subjects"],
                            self.sessionParams["experiments"]):
            path = self.app.makeDataPath(self.dataRoot, self.name, sbj, exp)
            if os.path.exists(path):
                return True
        return False

    @Slot()
    def finishSession(self):
        self.timer.stop()
        self.sessionFinished.emit()
        qDebug("session finished")
        self.status = "completed"
