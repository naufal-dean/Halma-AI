import os
from PyQt5.uic import loadUi
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.getcwd() + '/view/main_window.ui', self)
        self.setupUI()

    def setupUI(self):
        ## connect event and function handler here
        ## example
        # self.imageBtn.clicked.connect(self.imageBtnClickedHandler)
        # self.videoBtn.clicked.connect(self.videoBtnClickedHandler)
        # self.audioBtn.clicked.connect(self.audioBtnClickedHandler)
        pass
