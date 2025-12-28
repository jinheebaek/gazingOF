from PySide6.QtCore import Signal, Slot, Property, QObject
from PySide6.QtCore import Qt
from PySide6.QtCore import QMutex
from PySide6.QtCore import QThread
from PySide6.QtGui import QImage

import os
import time
import numpy as np
import cv2
import subprocess

from dlclive import DLCLive, Processor

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


class VideoCtrl(QObject):
    frameUpdated = Signal(QImage)
    gazingAngleUpdated = Signal(float, float)
    requestRecordStart = Signal(str)
    requestRecordStop = Signal()

    frameAnnotatedUpdated = Signal(QImage)
    requestRecordAnnotatedStart = Signal(str)
    requestRecordAnnotatedStop = Signal()

    # sessionStarted = Signal()

    # cmd = "ffmpeg -use_wallclock_as_timestamps 1 -f mjpeg -i http://192.168.100.{}:8081/?action=stream -vcodec libx264 -y {}"

    def __init__(self, app, video_index):
        super().__init__(app)
        self.app = app
        self.video_index = video_index

        self.frameLoader = FrameLoader(video_index)
        self.frameLoader.frameUpdated.connect(self.frameUpdated)
        self.frameLoader.frameAnnotatedUpdated.connect(self.frameAnnotatedUpdated)
        self.frameLoader.gazingAngleUpdated.connect(self.gazingAngleUpdated)
        self.frameLoader.connectionChanged.connect(self.onConnectionChanged)
        # self.frameLoader.start()
        self.is_connected = False

        # self.sessionStarted.connect(self.frameLoader.onSessionStarted)

        # self.videoWriterThread = None
        # self.videoWriter = None
        self.is_recording = False

        self.videoWriterThread = QThread()
        self.videoWriter = VideoWriter()
        self.videoWriter.moveToThread(self.videoWriterThread)
        self.requestRecordStart.connect(self.videoWriter.recordStart)
        self.requestRecordStop.connect(self.videoWriter.recordStop)
        self.videoWriterThread.started.connect(self.videoWriter.initialize)
        # self.videoWriterThread.start()

        self.videoWriterThread_annotated = QThread()
        self.videoWriter_annotated = VideoWriter()
        self.videoWriter_annotated.moveToThread(self.videoWriterThread_annotated)
        self.requestRecordAnnotatedStart.connect(self.videoWriter_annotated.recordStart)
        self.requestRecordAnnotatedStop.connect(self.videoWriter_annotated.recordStop)
        self.videoWriterThread_annotated.started.connect(self.videoWriter_annotated.initialize)
        # self.videoWriterThread_annotated.start()
        
    def stop(self):
        self.recordStop()
        self.videoWriterThread.quit()
        self.videoWriterThread.wait()
        self.videoWriterThread_annotated.quit()
        self.videoWriterThread_annotated.wait()
        self.frameLoader.frameUpdated.disconnect(self.frameUpdated)
        self.frameLoader.gazingAngleUpdated.disconnect(self.gazingAngleUpdated)
        self.frameLoader.connectionChanged.disconnect(self.onConnectionChanged)
        self.frameLoader.stop()
        self.frameLoader.quit()
        self.frameLoader.wait()

    @Slot()
    def onSessionStarted(self):
        self.frameLoader.start()
        self.videoWriterThread.start()
        self.videoWriterThread_annotated.start()

        # self.sessionStarted.emit()

    @Slot(bool)
    def onConnectionChanged(self, is_connected):
        self.is_connected = is_connected

    def getVideoDir(self, session):
        for cmbrname in self.app.chambers:
            if self.app.chambers[cmbrname].videoCtrl == self:
                idx = session.sessionParams["chambers"].index(cmbrname)
                sbj = session.sessionParams["subjects"][idx]
                exp = session.sessionParams["experiments"][idx]

                datafilepath = self.app.makeDataPath(
                    session.dataRoot,
                    session.name,
                    sbj, exp
                )
                return os.path.dirname(datafilepath)
        return session.dataRoot

    @Slot(str)
    def recordStart(self, session):
        if self.is_recording or not self.is_connected:
            return
        
        videoDir = self.getVideoDir(session)

        videoFile = os.path.join(
            # session.dataRoot,
            videoDir,
            # "{}_video{:02}.mp4".format(session.name, self.video_index)
            "{}_video{}.mp4".format(session.name, self.video_index)
        )

        videoFile_annotated = os.path.join(
            # session.dataRoot,
            videoDir,
            # "{}_video{:02}.mp4".format(session.name, self.video_index)
            "{}_video{}_annotated.mp4".format(session.name, self.video_index)
        )

        if not os.path.exists(videoDir):
            os.makedirs(videoDir)

        # self.videoWriter.recordStart(videoFile)
        self.requestRecordStart.emit(videoFile)
        self.frameUpdated.connect(self.videoWriter.write)
        self.requestRecordAnnotatedStart.emit(videoFile_annotated)
        self.frameAnnotatedUpdated.connect(self.videoWriter_annotated.write)

        self.is_recording = True

        # ## test
        # videoFile2 = videoFile.replace(".mp4", "_test.mp4")
        # recCmd = self.cmd.format(100 + self.video_index, videoFile2)
        # self.p_video = subprocess.Popen(recCmd, shell=True)
        # ts much faster than behavior

    @Slot()
    def recordStop(self):
        if not self.is_recording:
            return
        self.frameUpdated.disconnect(self.videoWriter.write)
        # self.videoWriter.recordStop()
        self.requestRecordStop.emit()
        self.frameAnnotatedUpdated.disconnect(self.videoWriter_annotated.write)
        self.requestRecordAnnotatedStop.emit()
        self.is_recording = False

        # ## test
        # self.p_video.terminate()


class FrameLoader(QThread):
    frameUpdated = Signal(QImage)
    frameAnnotatedUpdated = Signal(QImage)
    connectionChanged = Signal(bool)
    gazingAngleUpdated = Signal(float, float)

    def __init__(self, video_index, parent=None):
        super().__init__(parent)
        self.video_index = video_index
        self.frameRate = 15
        self.active = True
        self.mutex = QMutex()
        
        self.dlc_proc = Processor()  
        self.dlc_live = DLCLive("C:/Users/kimjg/Documents/Repository/gazingOF/model", processor=self.dlc_proc)
        self.dlc_infer = None

    # @Slot()
    # def onSessionStarted(self):
    #     self.active = True

    def run(self, record=False):
        while True:
            self.mutex.lock()
            if not self.active:
                self.mutex.unlock()
                break
            self.mutex.unlock()

            # vid1 = "C:\Users\kimjg\Documents\Repository\gazingOF\eOF01_ct_ob.mp4"
            # vid2 = "C:\Users\kimjg\Documents\Repository\gazingOF\eOF01_ct_dm.mp4"
            # vid1 = "C:/Users/kimjg/Documents/Repository/gazingOF/eOF01_ct_dm.mp4"
            # vid2 = "C:/Users/kimjg/Documents/Repository/gazingOF/eOF01_ct_ob.mp4"
            # self.cap1 = cv2.VideoCapture(vid1)
            # self.cap2 = cv2.VideoCapture(vid2)
            vid = "C:/Users/kimjg/Documents/Research/opto_nphr/nOF/nOF07_ctrl/2025-12-17/2025-12-17_10-21-44_video1.mp4"
            self.cap = cv2.VideoCapture(vid)
            # self.cap1 = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            # self.cap2 = cv2.VideoCapture(2, cv2.CAP_DSHOW)
            # if not self.cap1 or not self.cap1.isOpened():
            #     time.sleep(1)
            #     continue
            #     # break
            # if not self.cap2 or not self.cap2.isOpened():
            #     time.sleep(1)
            #     continue
            #     # break
            if not self.cap or not self.cap.isOpened():
                time.sleep(1)
                continue
                # break

            self.connectionChanged.emit(True)   
            intv = 1 / self.frameRate
            # self.cap1.set(cv2.CAP_PROP_FPS, self.frameRate)
            # self.cap2.set(cv2.CAP_PROP_FPS, self.frameRate)
            self.cap.set(cv2.CAP_PROP_FPS, self.frameRate)
            while True:
                self.mutex.lock()
                if not self.active:
                    self.mutex.unlock()
                    break
                self.mutex.unlock()

                # ret1, frame1 = self.cap1.read()
                # ret2, frame2 = self.cap2.read()
                ret, frame = self.cap.read()
                t_frame = time.time()
                # if not ret1 or not ret2: 
                #     self.connectionChanged.emit(False)
                #     break
                if not ret: 
                    self.connectionChanged.emit(False)
                    break

                # self.height1, self.width1, ch = frame1.shape
                # self.height2, self.width2, ch = frame2.shape
                # assert self.height1 == self.height2

                # # frame = np.concatenate([frame1, frame2], axis=1)
                # frame = np.concatenate([frame1[:, :-int(640 * 0.2), :], frame2[:, int(640 * 0.2):, :]], axis=1)
                # # frame = cv2.normalize(frame, None, alpha=32, beta=255, norm_type=cv2.NORM_MINMAX)

                # frame = cv2.normalize(frame, None, alpha=32, beta=255, norm_type=cv2.NORM_MINMAX)
                _, _, ch = frame.shape

                tmp = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                contrast = 1.5
                brightness = 30
                tmp[:, :, 2] = np.clip(contrast * tmp[:, :, 2] + brightness, 0, 255)
                # frame = cv2.cvtColor(tmp, cv2.COLOR_HSV2BGR)
                frame_annotated = frame.copy()

                if self.dlc_infer is None:
                    self.dlc_infer = self.dlc_live.init_inference(frame)
                pose = self.dlc_live.get_pose(frame)

                try: 
                    c_lear = pose[0, :2]   
                    c_rear = pose[1, :2]
                    c_earcenter = (c_lear + c_rear) / 2
                    c_demon = pose[3, :2]

                    v_vert_3d = np.array([0, 0, -1])
                    v_head = np.cross(v_vert_3d, np.append(c_rear - c_lear, 0))[:2]
                    v_earcenter2dem = c_demon - c_earcenter
                    v_head = v_head / np.linalg.norm(v_head)
                    v_earcenter2dem = v_earcenter2dem / np.linalg.norm(v_earcenter2dem)

                    cv2.circle(frame_annotated, c_lear.astype(int), 5, (0, 255, 0), -1)
                    cv2.circle(frame_annotated, c_rear.astype(int), 5, (0, 255, 0), -1)
                    
                    c_earcenter_int = c_earcenter.astype(int)
                    c_ear2demon_int = (c_earcenter + v_earcenter2dem * 70).astype(int)
                    c_head_int = (c_earcenter + v_head * 70).astype(int)
                    
                    cv2.line(frame_annotated, c_earcenter_int, c_ear2demon_int, (255, 0, 0), 5)
                    cv2.line(frame_annotated, c_earcenter_int, c_head_int, (0, 0, 255), 5)

                    angle = np.arccos((np.dot(v_head, v_earcenter2dem) / np.linalg.norm(v_head) / np.linalg.norm(v_earcenter2dem)))
                    self.gazingAngleUpdated.emit(t_frame, np.rad2deg(angle))
                except Exception:
                    pass
                    
                img = QImage(frame,
                            #  self.width1 * 2, self.height1, ch * self.width1 * 2,
                             frame.shape[1], frame.shape[0], ch * frame.shape[1],
                             QImage.Format_BGR888)
                
                scaled_img = img.scaled(frame.shape[1], frame.shape[0], Qt.KeepAspectRatio)
                # scaled_img = img.scaled(640 * 2, 480, Qt.KeepAspectRatio)
     
                self.frameUpdated.emit(scaled_img)
                    
                img_annotated = QImage(frame_annotated,
                                       #  self.width1 * 2, self.height1, ch * self.width1 * 2,
                                       frame_annotated.shape[1], frame_annotated.shape[0], ch * frame_annotated.shape[1],
                                       QImage.Format_BGR888)
                
                scaled_img_annotated = img_annotated.scaled(frame_annotated.shape[1], frame_annotated.shape[0], Qt.KeepAspectRatio)
                # scaled_img = img.scaled(640 * 2, 480, Qt.KeepAspectRatio)
     
                self.frameAnnotatedUpdated.emit(scaled_img_annotated)

                time.sleep(intv)
            self.dlc_infer = None

    @Slot()
    def stop(self):
        self.mutex.lock()
        self.active = False
        self.mutex.unlock()


class VideoWriter(QObject):
    @Slot()
    def initialize(self):
        # self.width = 640 * 2
        self.width = int(640 * 0.8) * 2
        self.height = 480
        self.frameRate = 15

        self.videoFile = None
        self.ts0 = 0
        self.ts = np.array([])
        self.iframe = 0

        self.p_postprocesses = []
        self.writer = None

    @Slot(QImage)
    def write(self, image):
        if not self.writer:
            return

        width = image.width()
        height = image.height()

        ptr = image.constBits()
        frame = np.array(ptr).reshape(height, width, 3)  #  Copies the data

        if self.iframe == 0:
            self.writer.write(frame)  # duplicated frame for t = 0
            self.ts0 = time.time() - self.ts0

        # self.ts[self.iframe] = self.cap.get(cv2.CAP_PROP_POS_MSEC)
        self.ts[self.iframe] = time.time()
        self.writer.write(frame)
        self.iframe += 1

    @Slot(str)
    def recordStart(self, videoFile):
        # videodir = os.path.dirname(videoFile)
        # if not os.path.exists(videodir):
        #     os.makedirs(videodir)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(
            videoFile.replace(".mp4", "_raw.mp4"),
            fourcc, self.frameRate, (self.width, self.height))

        self.videoFile = videoFile
        self.ts0 = time.time()  # ts of the 1st frame
        self.ts = np.zeros(15 * 60 * 60 * 3)  # max 3 hour
        self.iframe = 0

    @Slot()
    def recordStop(self):
        self.writer.release()
        self.writer = None

        self.ts = self.ts[:self.iframe]
        self.ts = (self.ts - self.ts[0] + self.ts0) * 1e3
        self.ts = np.append(0, self.ts)
        np.savetxt(self.videoFile.replace(".mp4", "_frametime.txt"),
                   self.ts, fmt="%.3f")
        try:
            # os.system("ffmpeg -y -i {} -c:v libx264 {}".format(
            #     self.videoFile.replace(".mp4", "_raw.mp4"),
            #     self.videoFile.replace(".mp4", "_transcode.mp4")
            # ))

            # os.system("mp4fpsmod -t {} -o {} {}".format(
            #     self.videoFile.replace(".mp4", "_frametime.txt"),
            #     self.videoFile,
            #     self.videoFile.replace(".mp4", "_transcode.mp4")
            # ))

            cmd_transcode = "ffmpeg -y -i {} -c:v libx264 {}".format(
                self.videoFile.replace(".mp4", "_raw.mp4"),
                self.videoFile.replace(".mp4", "_transcode.mp4")
            )

            cmd_tsfix = "mp4fpsmod -c -t {} -o {} {}".format(
                self.videoFile.replace(".mp4", "_frametime.txt"),
                self.videoFile,
                self.videoFile.replace(".mp4", "_transcode.mp4")
            )

            self.p_postprocesses.append(subprocess.Popen(
                "{} && {}".format(cmd_transcode, cmd_tsfix), shell=True))
            # self.p_postprocess.wait()

        except:
            pass
        # else:
        #     os.unlink(self.videoFile.replace(".mp4", "_transcode.mp4"))
        #     os.unlink(self.videoFile.replace(".mp4", "_raw.mp4"))
