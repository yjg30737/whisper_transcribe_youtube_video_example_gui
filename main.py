import os
from collections import Counter

from PyQt5.QtCore import QThread, pyqtSignal, QSettings, QCoreApplication, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QMainWindow, QPushButton, QApplication, QVBoxLayout, QLineEdit, QTextBrowser, QWidget, \
    QMessageBox, QGroupBox, QHBoxLayout, QRadioButton, QFrame, QLabel, QMenu, QAction, QSystemTrayIcon

from apiWidget import ApiWidget
from findPathWidget import FindPathWidget
from loadingLbl import LoadingLabel
from notifier import NotifierWidget
from script import install_audio, GPTTranscribeWrapper, remove_trim

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
            # If you want to trim the video from specific time to specific time, you can use the following line
            # But we don't need it currently
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
            result_obj_lst, result_audio_file_paths = self.__wrapper.transcribe_audio(self.__dst_filename, response_format='verbose_json', timestamp_granularities=['segment'])
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

        self.__used_language_list = []
        self.__duration = 0
        self.__is_stopped = False

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

        fromLocalRadioBtn.toggled.connect(self.__toggleFromWhereRadioWidgets)
        fromYoutubeRadioBtn.toggled.connect(self.__toggleFromWhereRadioWidgets)
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

        resultGrpBox = QGroupBox()
        resultGrpBox.setTitle('Result')

        self.__transcriptionLanguageLbl = QLabel('Transcription language: ')
        self.__transcriptionDurationLbl = QLabel('Transcription duration: ')

        self.__stopBtn = QPushButton('Stop')
        self.__stopBtn.clicked.connect(self.__stop)
        self.__stopBtn.setVisible(False)

        lay = QVBoxLayout()
        lay.addWidget(self.__transcriptionLanguageLbl)
        lay.addWidget(self.__transcriptionDurationLbl)

        descriptionWidget = QWidget()
        descriptionWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(descriptionWidget)
        lay.addWidget(self.__browser)
        resultGrpBox.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(self.__apiWidget)
        lay.addWidget(self.__fromWhereGrpBox)
        lay.addWidget(getFromWidget)
        lay.addWidget(self.__btn)
        lay.addWidget(self.__loadingLbl)
        lay.addWidget(resultGrpBox)
        lay.addWidget(self.__stopBtn)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

        self.__setAiEnabled(self.__wrapper.is_available())

        self.__setTrayMenu()
        QApplication.setQuitOnLastWindowClosed(False)

    def __setTrayMenu(self):
        # background app
        menu = QMenu()

        action = QAction("Quit", self)
        action.setIcon(QIcon('ico/close.svg'))

        action.triggered.connect(app.quit)

        menu.addAction(action)

        tray_icon = QSystemTrayIcon(app)
        tray_icon.setIcon(QIcon('logo.png'))
        tray_icon.activated.connect(self.__activated)

        tray_icon.setContextMenu(menu)

        tray_icon.show()

    def __activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

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
        if isinstance(f, str):
            f = f.strip() != ''
        text = self.get_current_url() != ''
        self.__btn.setEnabled(f and text)

    def __toggleWidgets(self, f):
        self.__btn.setEnabled(f)
        self.__fromLocalWidget.setEnabled(f)
        self.__fromYoutubeWidget.setEnabled(f)
        self.__stopBtn.setVisible(not f)

    def __toggleFromWhereRadioWidgets(self):
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
        self.__transcriptionLanguageLbl.setText('Transcription language: ')
        self.__transcriptionDurationLbl.setText('Transcription duration: ')
        self.__toggleWidgets(False)

    def __audioReadyFinished(self, dst_filename):
        self.__dst_filename = dst_filename

    def __runSecondThread(self):
        if self.__is_stopped:
            self.__is_stopped = False
        else:
            self.__t = Thread2(self.__wrapper, self.__dst_filename)
            self.__t.started.connect(self.__started)
            self.__t.afterGenerated.connect(self.__afterGenerated)
            self.__t.finished.connect(self.__finished)
            self.__t.start()

    def __afterGenerated(self, result_obj_lst):
        self.__loadingLbl.stop()
        self.__btn.setEnabled(True)
        for result_obj in result_obj_lst:
            self.__used_language_list.append(result_obj['language'])
            self.__duration += result_obj['duration']
            segments = result_obj['segments']
            for segment in segments:
                start = segment['start']
                end = segment['end']
                text = segment['text']
                self.__browser.append(f"[{start} --> {end}] {text}")

    def __finished(self):
        if self.__is_stopped:
            self.__is_stopped = False
        else:
            mostCommonUsedLanguage = Counter(self.__used_language_list).most_common(1)[0][0]
            self.__transcriptionLanguageLbl.setText(f'Transcription language (Most commonly used): {mostCommonUsedLanguage}')
            self.__transcriptionDurationLbl.setText(f'Transcription duration: {str(round(self.__duration, 2))} seconds')
            self.__btn.setEnabled(True)
            self.__fromLocalWidget.setEnabled(True)
            self.__fromYoutubeWidget.setEnabled(True)

            if not self.isVisible():
                self.__notifierWidget = NotifierWidget(informative_text='Transcription Complete 💻', detailed_text='Click this!')
                self.__notifierWidget.show()
                self.__notifierWidget.doubleClicked.connect(self.show)

    def __stop(self):
        self.__is_stopped = True
        self.__t.terminate()
        self.__loadingLbl.stop()
        self.__toggleWidgets(True)

    def __beforeClose(self):
        message = 'Would you like to exit the application? If you won\'t, it will be running in the background.'
        closeMessageBox = QMessageBox(self)
        closeMessageBox.setWindowTitle('Exit')
        closeMessageBox.setText(message)
        closeMessageBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        reply = closeMessageBox.exec()
        # Cancel
        if reply == QMessageBox.StandardButton.Cancel:
            return True
        else:
            # Yes
            if reply == QMessageBox.StandardButton.Yes:
                app = QApplication.instance()
                app.quit()
            # No
            elif reply == QMessageBox.StandardButton.No:
                self.close()

    def closeEvent(self, e):
        f = self.__beforeClose()
        if f:
            e.ignore()
        else:
            return super().closeEvent(e)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    QApplication.setWindowIcon(QIcon('logo.png'))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())