from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer


class LoadingLabel(QLabel):
    def __init__(self):
        super(LoadingLabel, self).__init__()
        self.__initVal()
        self.__initUi()

    def __initVal(self):
        self.__default_text = 'Loading'

    def __initUi(self):
        self.__timer = QTimer(self)
        self.setText(self.__default_text)
        self.setVisible(False)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)

    def __timerInit(self):
        self.__timer.timeout.connect(self.__ticking)
        self.__timer.singleShot(0, self.__ticking)
        self.__timer.start(500)

    def __ticking(self):
        dot = '.'
        cur_text = self.text()
        cnt = cur_text.count(dot)
        if cnt % 3 == 0 and cnt != 0:
            self.setText(self.__default_text + dot)
        else:
            self.setText(cur_text + dot)

    def start(self):
        self.setVisible(True)
        self.__timerInit()

    def stop(self):
        self.setVisible(False)
        self.__timer.stop()