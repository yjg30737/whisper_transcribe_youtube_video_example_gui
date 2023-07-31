from PyQt5.QtWidgets import QMainWindow, QPushButton, QApplication, QVBoxLayout, QLineEdit, QTextBrowser, QWidget, \
    QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal

from loadingLbl import LoadingLabel
from script import installAudio, removeTrim, transcribeAudio


class Thread(QThread):
    transcribeFinished = pyqtSignal(str)

    def __init__(self, url):
        super(Thread, self).__init__()
        self.__url = url

    def run(self):
        try:
            downloaded_file = installAudio(self.__url)
            dst_filename = removeTrim(downloaded_file)
            result = transcribeAudio(dst_filename)
            self.transcribeFinished.emit(result)
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
            self.__t = Thread(url)
            self.__t.started.connect(self.__started)
            self.__t.transcribeFinished.connect(self.__transcribeFinished)
            self.__t.finished.connect(self.__finished)
            self.__t.start()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def __started(self):
        self.__loadingLbl.start()
        self.__btn.setEnabled(False)

    def __transcribeFinished(self, result_text):
        self.__browser.append(result_text)

    def __finished(self):
        self.__loadingLbl.stop()
        self.__btn.setEnabled(True)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())