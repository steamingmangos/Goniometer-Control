import sys
import cv2

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot, Qt, QMutex, QWaitCondition
from PyQt5 import QtWidgets, QtCore, QtGui


# https://ru.stackoverflow.com/a/1150993/396441

class Thread1(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, mutex, condition):
        super().__init__()
        self.mutex = mutex
        self.condition = condition

    def run(self):
        self.cap1 = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        width = int(self.cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(width, height)

        self.cap1.set(3, 1280)
        self.cap1.set(4, 720)
        self.cap1.set(5, 30)
        while True:
            ret1, image1 = self.cap1.read()
            if ret1:
                im0 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
                gray = cv2.cvtColor(im0, cv2.COLOR_GRAY2RGB)
                # print(gray)
                height1, width1, channel1 = gray.shape
                step1 = channel1 * width1
                # print(channel1)
                qImg1 = QImage(gray.data, width1, height1, step1, QImage.Format_RGB888)
                # qImg1 = QImage.convertToFormat(QImage.Format_Grayscale16)
                # print(qImg1)
                # print(qImg1.isGrayscale())
                # print("junk")
                self.changePixmap.emit(qImg1)
                self.condition.wait(self.mutex)

    def stop(self):
        self.cap1.release()


class Thread2(QThread):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.active = True

    def run(self):
        if self.active:
            self.fourcc = cv2.VideoWriter_fourcc(*'MP4V')
            self.out1 = cv2.VideoWriter('output.mp4', self.fourcc, 30, (1280, 720))
            self.cap1 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            self.cap1.set(3, 1280)
            self.cap1.set(4, 720)
            self.cap1.set(5, 30)
            while self.active:
                ret1, image1 = self.cap1.read()
                if ret1:
                    # im2 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
                    # gray2 = cv2.cvtColor(im2, cv2.COLOR_GRAY2RGB)
                    self.out1.write(image1)
                #self.msleep(10)

    def stop(self):
        self.out1.release()


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.initUI()

    @QtCore.pyqtSlot(QImage)
    def setImage(self, qImg1):
        self.mutex.lock()
        try:
            self.image_label.setPixmap(QPixmap.fromImage(qImg1))
        finally:
            self.mutex.unlock()
            self.condition.wakeAll()

    def controlTimer(self):
        if not self.saveTimer.isActive():
            # write video
            self.saveTimer.start()
            self.th2 = Thread2(self)
            self.th2.active = True
            self.th2.start()
            # update control_bt text
            self.control_bt.setText("STOP")
        else:
            # stop writing
            self.saveTimer.stop()
            self.th2.active = False
            self.th2.stop()
            self.th2.terminate()
            # update control_bt text
            self.control_bt.setText("START")

    def closeEvent(self, event):
        self.th1.stop()
        self.th1.terminate()
        if self.th2.isRunning():
            self.th2.stop()
            self.th2.terminate()
        event.accept()

    def initUI(self):
        self.mutex.lock()
        self.resize(1280, 720)
        self.control_bt = QPushButton('START')
        self.control_bt.clicked.connect(self.controlTimer)
        self.image_label = QLabel()
        self.saveTimer = QTimer()
        self.th1 = Thread1(mutex=self.mutex, condition=self.condition)
        self.th1.changePixmap.connect(self.setImage)
        self.th1.start()

        vlayout = QVBoxLayout(self)
        vlayout.addWidget(self.image_label)
        vlayout.addWidget(self.control_bt)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
