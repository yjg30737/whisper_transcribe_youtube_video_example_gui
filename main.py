import psutil, os
import subprocess

from PyQt5.QtCore import QThread, pyqtSignal, QSettings, QCoreApplication, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QPushButton, QApplication, QVBoxLayout, QLineEdit, QTextBrowser, QWidget, \
    QMessageBox, QGroupBox, QHBoxLayout, QRadioButton, QFrame

from apiWidget import ApiWidget
from findPathWidget import FindPathWidget
from loadingLbl import LoadingLabel
from script import install_audio, remove_trim, GPTTranscribeWrapper


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)  # HighDPI support

QApplication.setFont(QFont('Arial', 12))


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
    afterGenerated = pyqtSignal(list)

    def __init__(self, wrapper, dst_filename):
        super(Thread2, self).__init__()
        self.__wrapper = wrapper
        self.__dst_filename = dst_filename

    def run(self):
        try:
            result_obj_lst = self.__wrapper.transcribe_audio(self.__dst_filename, response_format='verbose_json', timestamp_granularities=['segment'])
            self.afterGenerated.emit(result_obj_lst)
        except Exception as e:
            raise Exception(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.__initVal()
        self.__initUi()

    def __initVal(self):
        self.__settings_ini = QSettings(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'settings.ini'), QSettings.Format.IniFormat)
        if not self.__settings_ini.contains('API_KEY'):
            self.__settings_ini.setValue('API_KEY', '')
        self.__api_key = self.__settings_ini.value('API_KEY', type=str)

        self.__wrapper = GPTTranscribeWrapper(self.__api_key)
        self.__is_local = True

    def __initUi(self):
        self.setWindowTitle('PyQt app example of transcribing Youtube video with Whisper')

        # Top
        # API input
        self.__apiWidget = ApiWidget(self.__api_key, wrapper=self.__wrapper, settings=self.__settings_ini)
        self.__apiWidget.apiKeyAccepted.connect(self.__api_key_accepted)

        self.__fromYoutubeWidget = QLineEdit()
        self.__fromYoutubeWidget.setPlaceholderText('Write Youtube video address...')
        self.__fromYoutubeWidget.textChanged.connect(self.__setAiEnabled)

        self.__fromLocalWidget = FindPathWidget()
        self.__fromLocalWidget.setExtOfFiles('Audio Files (*.mp3);; Video Files (*.mp4)')
        self.__fromLocalWidget.getLineEdit().setPlaceholderText('Select a file...')
        self.__fromLocalWidget.added.connect(self.__setAiEnabled)

        fromLocalRadioBtn = QRadioButton('From local')
        fromYoutubeRadioBtn = QRadioButton('From Youtube')

        fromLocalRadioBtn.toggled.connect(self.__toggleWidgets)
        fromYoutubeRadioBtn.toggled.connect(self.__toggleWidgets)
        fromLocalRadioBtn.toggle()

        lay = QHBoxLayout()
        lay.addWidget(fromLocalRadioBtn)
        lay.addWidget(fromYoutubeRadioBtn)

        self.__fromWhereGrpBox = QGroupBox()
        self.__fromWhereGrpBox.setTitle('From where?')
        self.__fromWhereGrpBox.setLayout(lay)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)

        lay = QHBoxLayout()
        lay.addWidget(self.__fromLocalWidget)
        lay.addWidget(sep)
        lay.addWidget(self.__fromYoutubeWidget)
        
        getFromWidget = QWidget()
        getFromWidget.setLayout(lay)

        self.__loadingLbl = LoadingLabel()

        self.__btn = QPushButton('Transcribe the Video')
        self.__btn.clicked.connect(self.__run)
        self.__btn.setEnabled(False)
        self.__browser = QTextBrowser()
        self.__browser.setPlaceholderText('Result would be shown here...')

        lay = QVBoxLayout()
        lay.addWidget(self.__apiWidget)
        lay.addWidget(self.__fromWhereGrpBox)
        lay.addWidget(getFromWidget)
        lay.addWidget(self.__btn)
        lay.addWidget(self.__loadingLbl)
        lay.addWidget(self.__browser)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

        self.__setAiEnabled(self.__wrapper.is_available())

    def __api_key_accepted(self, api_key, f):
        # Enable AI related features if API key is valid
        self.__setAiEnabled(f)

    def get_current_url(self):
        if self.__is_local:
            url = self.__fromLocalWidget.getFileName()
        else:
            url = self.__fromYoutubeWidget.text()
        url = url.strip()
        return url

    def __setAiEnabled(self, f):
        text = self.get_current_url() != ''
        self.__btn.setEnabled(f and text)

    def __toggleWidgets(self):
        self.__is_local = self.sender().text() == 'From local'
        self.__fromLocalWidget.setEnabled(self.__is_local)
        self.__fromYoutubeWidget.setEnabled(not self.__is_local)

    def __run(self):
        try:
            url = self.get_current_url()
            if self.__is_local:
                self.__audioReadyFinished(url)
                self.__runSecondThread()
            else:
                self.__t = Thread1(url)
                self.__t.started.connect(self.__started)
                self.__t.audioReadyFinished.connect(self.__audioReadyFinished)
                self.__t.finished.connect(self.__runSecondThread)
                self.__t.start()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def __started(self):
        self.__loadingLbl.start()
        self.__browser.clear()
        self.__btn.setEnabled(False)

    def __audioReadyFinished(self, dst_filename):
        self.__dst_filename = dst_filename

    def __runSecondThread(self):
        self.__t = Thread2(self.__wrapper, self.__dst_filename)
        self.__t.started.connect(self.__started)
        self.__t.afterGenerated.connect(self.__afterGenerated)
        self.__t.start()

    def __afterGenerated(self, result_obj_lst):
        self.__loadingLbl.stop()
        self.__btn.setEnabled(True)
        for result_obj in result_obj_lst:
            print(f"Transcription language: {result_obj['language']}")
            print(f"Transcription duration: {result_obj['duration']}")
            segments = result_obj['segments']
            for segment in segments:
                start = segment['start']
                end = segment['end']
                text = segment['text']
                self.__browser.append(f"[{start} --> {end}] {text}")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())