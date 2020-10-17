import os
from enum import IntEnum
from PyQt5.uic import loadUi
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from model import *


class PageIdx(IntEnum):
    MAIN_MENU = 0
    SELECT_SIZE = 1
    SELECT_SIDE = 2
    IN_GAME = 3


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.path.join(os.getcwd(), "view", "main_window.ui"), self)
        self.gameState = None
        self.actCell = None
        self.boardSize = 0
        self.legalMoves = []
        # change page helper
        self.changePage = lambda idx: self.stackedWidget.setCurrentIndex(idx)
        # setup ui
        self.setupUI()

    def setupUI(self):
        # main menu page
        self.playGameBtn.clicked.connect(lambda: self.changePage(PageIdx.SELECT_SIZE))
        self.exitBtn.clicked.connect(lambda: self.close())
        # select board size page
        self.eight.clicked.connect(lambda:self.setBoardSize(8))
        self.ten.clicked.connect(lambda:self.setBoardSize(10))
        self.sixteen.clicked.connect(lambda:self.setBoardSize(16))
        
        # select side page
        self.pRedBtn.clicked.connect(lambda: self.startGame(Player.RED, self.boardSize))
        self.pGreenBtn.clicked.connect(lambda: self.startGame(Player.GREEN, self.boardSize))
        self.mainMenuNavBtn.clicked.connect(lambda: self.changePage(PageIdx.MAIN_MENU))
        


        # in game page
        self.quitGameBtn.clicked.connect(self.quitGame)

    def initBoardUI(self):
        for r, cellRow in enumerate(self.gameState.board.cells):
            for c, cell in enumerate(cellRow):
                button = QPushButton()
                button.clicked.connect(self.cellClickedHandler)
                button.setProperty("highlight", "none")
                button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                button.setStyleSheet(self.getCellStyleSheet(cell.owner))
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
    def startGame(self, humanPlayer: Player, boardSize):
        self.initGameState(humanPlayer, boardSize)
        self.initBoardUI()
        self.changePage(PageIdx.IN_GAME)

    def quitGame(self):
        for idx in reversed(range(self.fields.count())):
            self.fields.itemAt(idx).widget().deleteLater()
        self.gameState = None
        self.changePage(PageIdx.MAIN_MENU)

    def cellClickedHandler(self):
        button = self.sender()
        r, c, _, _ = self.fields.getItemPosition(self.fields.indexOf(button))
        # highlight helper
        def highlightBtn(btn, option):  # option: {none, yellow, red}
            btn.setProperty("highlight", option); btn.setStyle(btn.style());
        # update old active cell and old legal moves
        if self.actCell:
            highlightBtn(self.fields.itemAtPosition(*self.actCell).widget(), "none")
        for oldLegalMove in self.legalMoves:
            highlightBtn(self.fields.itemAtPosition(oldLegalMove[1].row, oldLegalMove[1].col).widget(), "none")
        # move or select pion
        if self.actCell and (self.gameState.board[self.actCell[0], self.actCell[1]], self.gameState.board[r, c]) in self.legalMoves:  # moving pion
            # move pion
            self.gameState.board.apply_step((self.gameState.board[self.actCell[0], self.actCell[1]], self.gameState.board[r, c]))
            self.updatePionPositionUI()
            # check winner
            winner = self.gameState.check_winner()
            if winner is not None:
                self.spawnDialogWindow("Game Ended", "The Winner is Player " + winner.name)
            else:
                self.gameState.next_turn()
                self.calculateAIMove()
            # update new active cell and new legal moves
            self.actCell = None
            self.legalMoves = []
        else:  # selecting pion
            # pion check if existing and owned
            cell = self.gameState.board[r, c]
            if not cell.occupied_by(self.gameState.act_player):
                highlightBtn(button, "none"); self.actCell = None; self.legalMoves = []; return;
            # update new active cell and new legal moves
            self.actCell = (r, c)
            self.legalMoves = self.gameState.board.legal_moves(r, c, self.gameState.act_player)
            highlightBtn(button, "yellow")
            for legalMove in self.legalMoves:
                highlightBtn(self.fields.itemAtPosition(legalMove[1].row, legalMove[1].col).widget(), "red")
        # just some debug, TODO: remove
        print(r, c)

    def setBoardSize(self, boardSize):
        self.boardSize = boardSize
        self.changePage(PageIdx.SELECT_SIDE)

    # Game methods
    def initGameState(self, humanPlayer, boardSize):
        board = Board(boardSize)
        self.gameState = GameState(board, humanPlayer)

    def calculateAIMove(self):
        # TODO: implement
        pass

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
                            border-radius: 0;
                        }}
                        QPushButton[highlight='none'] {{ border: 1px solid #1b1b1b; }}
                        QPushButton[highlight='yellow'] {{ border: 2px solid yellow; }}
                        QPushButton[highlight='red'] {{ border: 2px solid red; }}
                        QPushButton:hover {{
                            border: 2px solid yellow;
                        }}""".format(bgColor=bgColor)
        return stylesheet
