import os
from enum import IntEnum
from PyQt5.uic import loadUi
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from model import Board, GameState, Player


class PageIdx(IntEnum):
    MAIN_MENU = 0
    SELECT_SIDE = 1
    IN_GAME = 2


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.getcwd() + '/view/main_window.ui', self)
        # change page helper
        self.changePage = lambda idx: self.stackedWidget.setCurrentIndex(idx)
        # setup ui
        self.setupUI()

    def setupUI(self):
        # main menu page
        self.playGameBtn.clicked.connect(lambda: self.changePage(PageIdx.SELECT_SIDE))
        self.exitBtn.clicked.connect(lambda: self.close())
        # select side page
        self.pRedBtn.clicked.connect(lambda: self.startGame(Player.RED))
        self.pGreenBtn.clicked.connect(lambda: self.startGame(Player.GREEN))
        self.mainMenuNavBtn.clicked.connect(lambda: self.changePage(PageIdx.MAIN_MENU))
        # in game page
        self.quitGameBtn.clicked.connect(lambda: self.changePage(PageIdx.MAIN_MENU))

    # Slot methods
    def startGame(self, humanPlayer: Player, boardSize=16):
        self.changePage(PageIdx.IN_GAME)
        self.initGameState(humanPlayer, boardSize)

    # Game methods
    def initGameState(self, humanPlayer, boardSize=16):
        board = Board(boardSize)
        self.gameState = GameState(board, humanPlayer)

    # Helper methods
    def spawnDialogWindow(self, title, text, subtext="", type="Information"):
        message = QMessageBox()
        if type == "Question":
            message.setIcon(QMessageBox.Question)
        elif type == "Warning":
            message.setIcon(QMessageBox.Warning)
        elif type == "Critical":
            message.setIcon(QMessageBox.Critical)
        else:
            message.setIcon(QMessageBox.Information)
        message.setWindowTitle(title)
        message.setWindowIcon(QIcon("icon/qmessage_icon.png"))
        message.setText(text)
        message.setInformativeText(subtext)
        message.setStandardButtons(QMessageBox.Ok)
        message.exec_()
