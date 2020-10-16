import os
from enum import IntEnum
from PyQt5.uic import loadUi
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from model import *


class PageIdx(IntEnum):
    MAIN_MENU = 0
    SELECT_SIDE = 1
    IN_GAME = 2


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.path.join(os.getcwd(), "view", "main_window.ui"), self)
        self.gameState = None
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

    def initBoardUI(self):
        for r, cellRow in enumerate(self.gameState.board.cells):
            for c, cell in enumerate(cellRow):
                button = QPushButton()
                button.clicked.connect(self.cellClickedHandler)
                button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                button.setStyleSheet(self.getCellStyleSheet(cell.cell_type))
                self.fields.addWidget(button, r, c)
        self.updatePionPositionUI()

    def updatePionPositionUI(self):
        for r, cellRow in enumerate(self.gameState.board.cells):
            for c, cell in enumerate(cellRow):
                button = self.fields.itemAtPosition(r, c).widget()
                if cell.pion == Pion.NONE:
                    button.setIcon(QIcon()); continue;
                icon_filename = "pion_red.png" if cell.pion == Pion.RED else "pion_green.png"
                icon_path = os.path.join(os.getcwd(), "resource", "image", icon_filename)
                button.setIcon(QIcon(icon_path))

    # Slot methods
    def startGame(self, humanPlayer: Player, boardSize=16):
        self.changePage(PageIdx.IN_GAME)
        self.initGameState(humanPlayer, boardSize)
        self.initBoardUI()

    def cellClickedHandler(self):
        button = self.sender()
        r, c, _, _ = self.fields.getItemPosition(self.fields.indexOf(button))
        print(r, c)

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
        message.setText(text)
        message.setInformativeText(subtext)
        message.setStandardButtons(QMessageBox.Ok)
        message.exec_()

    def getCellStyleSheet(self, cellType: CellType):
        bgColor = ("#ef5350" if cellType == CellType.RED_HOUSE else
                   "#66bb6a" if cellType == CellType.GREEN_HOUSE else
                   "#bdbdbd")
        stylesheet = """QPushButton {{
                            background-color: {bgColor};
                            border: 1px solid #1b1b1b;
                            border-radius: 0;
                        }}
                        QPushButton:hover {{
                            border: 2px solid yellow;
                        }}""".format(bgColor=bgColor)
        return stylesheet
