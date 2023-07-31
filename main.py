import psutil
import subprocess

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QPushButton, QApplication, QVBoxLayout, QLineEdit, QTextBrowser, QWidget, \
    QMessageBox

from loadingLbl import LoadingLabel
from script import install_audio, remove_trim


class Thread1(QThread):
    audioReadyFinished = pyqtSignal(str)

    def __init__(self, url):
        super(Thread1, self).__init__()
        self.__url = url

    def run(self):
        try:
            downloaded_file = install_audio(self.__url)
            dst_filename = remove_trim(downloaded_file)
            self.audioReadyFinished.emit(dst_filename)
        except Exception as e:
            raise Exception(e)

class Thread2(QThread):
    updated = pyqtSignal(str)
    stopped = pyqtSignal()

    def __init__(self, command):
        super(Thread2, self).__init__()
        self.__command = command
        self.__process = ''
        self.__stopped = False

    def run(self):
        try:
            process = subprocess.Popen(
                self.__command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self.__process = psutil.Process(process.pid)

            while True:
                if self.__stopped:
                    self.__stopped = False
                    self.stopped.emit()
                    return
                realtime_output = process.stdout.readline()
                if realtime_output == '' and process.poll() is not None:
                    break
                if realtime_output:
                    self.updated.emit(realtime_output.strip())
        except Exception as e:
            raise Exception(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.__initUi()

    def __initUi(self):
        self.setWindowTitle('PyQt app example of transcribing Youtube video with Whisper')
        self.__lineEdit = QLineEdit()
        self.__lineEdit.setPlaceholderText('Write Youtube video address...')
        self.__lineEdit.textChanged.connect(self.__textChanged)

        self.__loadingLbl = LoadingLabel()

        self.__btn = QPushButton('Transcribe the Video')
        self.__btn.clicked.connect(self.__run)
        self.__btn.setEnabled(False)
        self.__browser = QTextBrowser()

        lay = QVBoxLayout()
        lay.addWidget(self.__lineEdit)
        lay.addWidget(self.__btn)
        lay.addWidget(self.__loadingLbl)
        lay.addWidget(self.__browser)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

    def __textChanged(self, text):
        self.__btn.setEnabled(text.strip() != '')

    def __run(self):
        try:
            url = self.__lineEdit.text().strip()
            self.__t = Thread1(url)
            self.__t.started.connect(self.__started)
            self.__t.audioReadyFinished.connect(self.__audioReadyFinished)
            self.__t.finished.connect(self.__runSecondThread)
            self.__t.start()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def __started(self):
        self.__loadingLbl.start()
        self.__btn.setEnabled(False)

    def __audioReadyFinished(self, dst_filename):
        self.__dst_filename = dst_filename

    def __runSecondThread(self):
        self.__t = Thread2(f'python transcribe_audio.py "{self.__dst_filename}"')
        self.__t.started.connect(self.__started)
        self.__t.updated.connect(self.__updated)
        self.__t.finished.connect(self.__finished)
        self.__t.start()

    def __updated(self, text):
        self.__browser.append(text)

    def __finished(self):
        self.__loadingLbl.stop()
        self.__btn.setEnabled(True)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())