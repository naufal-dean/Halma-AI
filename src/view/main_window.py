import os
import time
from enum import IntEnum
from PyQt5.uic import loadUi
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .worker import Worker
from model import *
from controller import *

class PageIdx(IntEnum):
    MAIN_MENU = 0
    SELECT_SIZE = 1
    SELECT_MODE = 2
    SELECT_SIDE = 3
    INPUT_MAX_TIME = 4
    IN_GAME = 5

class GameMode(IntEnum):
    HUMAN_MINIMAX = 1
    HUMAN_LOCAL = 2
    MINIMAX_LOCAL = 3

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.path.join(os.getcwd(), "view", "main_window.ui"), self)
        self.gameState = None
        self.actCell = None
        self.boardSize = 0
        self.gameMode = 0
        self.legalMoves = []
        # change page helper
        self.changePage = lambda idx: self.stackedWidget.setCurrentIndex(idx)
        # setup ui
        self.setupUI()
        self.humanPlayer = None
        # multithreader
        self.threadPool = QThreadPool()
        self.workerMinimax = None
        self.workerLocal = None
        # timer
        self.timerStart = 0
        self.timerMinimax = 0
        self.timerLocal = 0

    def setupUI(self):
        # main menu page
        self.playGameBtn.clicked.connect(lambda: self.changePage(PageIdx.SELECT_SIZE))
        self.exitBtn.clicked.connect(lambda: self.close())
        # select board size page
        self.eight.clicked.connect(lambda:self.setBoardSize(8))
        self.ten.clicked.connect(lambda:self.setBoardSize(10))
        self.sixteen.clicked.connect(lambda:self.setBoardSize(16))
        # select game mode paga
        self.humanVsMinimax.clicked.connect(lambda:self.setGameMode(GameMode.HUMAN_MINIMAX))
        self.humanVsLocalSearch.clicked.connect(lambda:self.setGameMode(GameMode.HUMAN_LOCAL))
        self.minimaxVsLocalSearch.clicked.connect(lambda:self.setGameMode(GameMode.MINIMAX_LOCAL))
        # select side page
        self.pRedBtn.clicked.connect(lambda: self.setHumanPlayer(Player.RED))
        self.pGreenBtn.clicked.connect(lambda: self.setHumanPlayer(Player.GREEN))
        self.mainMenuNavBtn.clicked.connect(lambda: self.changePage(PageIdx.MAIN_MENU))
        # max time page
        self.startGameButton.clicked.connect(lambda: self.startGame(self.humanPlayer, self.boardSize, self.maxTime.value()))
        # in game page
        quitConfirmation = lambda btn: self.quitGame() if btn.text() == "Yes" else None
        self.quitGameBtn.clicked.connect(lambda: self.spawnDialogWindow("Quit Game",
                                            "Are you sure you want to quit the game?",
                                            subtext="Your progress will be discarded",
                                            callback=quitConfirmation))

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
        self.updatePlayerTurnUI()

    def updatePionPositionUI(self):
        for r, cellRow in enumerate(self.gameState.board.cells):
            for c, cell in enumerate(cellRow):
                button = self.fields.itemAtPosition(r, c).widget()
                if cell.pion == Pion.NONE:
                    button.setIcon(QIcon()); continue;
                icon_filename = "pion_red.png" if cell.pion == Pion.RED else "pion_green.png"
                icon_path = os.path.join(os.getcwd(), "resource", "image", icon_filename)
                button.setIcon(QIcon(icon_path))

    def updatePlayerTurnUI(self):
        if self.gameState.act_player == Player.GREEN:
            self.curPlayer.setText("GREEN'S TURN")
        else:
            self.curPlayer.setText("RED'S TURN")

    def checkWinnerUI(self):
        winner = self.gameState.check_winner()
        if winner is not None:
            def restartOrQuitGame(btn):
                self.quitGame()
                if btn.text() == "Yes":
                    self.startGame(self.humanPlayer, self.boardSize, self.maxTime.value())
            # spawn winner window
            if self.gameMode == GameMode.HUMAN_MINIMAX:
                timeRecap = "Time Needed by Minimax Bot = " + str(self.timerMinimax) + " s."
            elif self.gameMode == GameMode.HUMAN_LOCAL:
                timeRecap = "Time Needed by Local Bot = " + str(self.timerLocal) + " s."
            else:
                timeRecap = "Time Needed by Minimax Bot = " + str(self.timerMinimax) + " s and Local Bot = " + str(self.timerLocal) + " s."
            self.spawnDialogWindow("Game Ended", "The Winner is Player " + winner.name + ". " + timeRecap,
                                   subtext="Restart Game?", callback=restartOrQuitGame)
            return True
        return False

    # Slot methods
    def startGame(self, humanPlayer: Player, boardSize :int, max_time :float):
        self.initGameState(humanPlayer, boardSize, max_time)
        self.initBoardUI()
        self.changePage(PageIdx.IN_GAME)
        self.timerMinimax = 0
        self.timerLocal = 0
        if self.gameMode == GameMode.MINIMAX_LOCAL:  # AI vs AI
            self.calculateAIMoveMinimax()
        elif self.gameMode == GameMode.HUMAN_LOCAL:  # Human vs AI local
            # AI move first not hum_player
            if self.gameState.act_player != self.gameState.hum_player:
                self.calculateAIMoveLocal()
        else:  # self.gameMode == GameMode.HUMAN_MINIMAX  # Human vs AI local
            # AI move first not hum_player
            if self.gameState.act_player != self.gameState.hum_player:
                self.calculateAIMoveMinimax()

    def quitGame(self):
        for idx in reversed(range(self.fields.count())):
            self.fields.itemAt(idx).widget().setParent(None)
        # disconnect worker signal
        if self.workerMinimax is not None:
            try:
                self.workerMinimax.signals.exception.disconnect(self.minimaxThreadException)
                self.workerMinimax.signals.result.disconnect(self.minimaxThreadResult)
                self.workerMinimax.signals.done.disconnect(self.minimaxThreadDone)
            except Exception as e:
                pass
        if self.workerLocal is not None:
            try:
                self.workerLocal.signals.exception.disconnect(self.minimaxThreadException)
                self.workerLocal.signals.result.disconnect(self.minimaxThreadResult)
                self.workerLocal.signals.done.disconnect(self.minimaxThreadDone)
            except Exception as e:
                pass
        # clean game state and return to main menu
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
            # update new active cell and new legal moves
            self.actCell = None
            self.legalMoves = []
            # check if human win
            if self.checkWinnerUI(): return
            # next turn: AI move
            self.gameState.next_turn()
            self.updatePlayerTurnUI()
            # calculate AI move
            if self.gameMode == GameMode.HUMAN_LOCAL:
                self.calculateAIMoveLocal()
            else:  # self.gameMode == GameMode.HUMAN_MINIMAX
                self.calculateAIMoveMinimax()
        else:  # selecting pion
            # pion check if existing and owned
            cell = self.gameState.board[r, c]
            if (not cell.occupied_by(self.gameState.hum_player)
                or self.gameState.act_player != self.gameState.hum_player
                or self.gameMode == GameMode.MINIMAX_LOCAL):
                highlightBtn(button, "none"); self.actCell = None; self.legalMoves = []; return;
            # update new active cell and new legal moves
            self.actCell = (r, c)
            self.legalMoves = self.gameState.board.legal_moves(r, c, self.gameState.hum_player)
            highlightBtn(button, "yellow")
            for legalMove in self.legalMoves:
                highlightBtn(self.fields.itemAtPosition(legalMove[1].row, legalMove[1].col).widget(), "red")
        # just some debug, TODO: remove
        print(r, c)

    def setBoardSize(self, boardSize):
        self.boardSize = boardSize
        self.changePage(PageIdx.SELECT_MODE)

    def setGameMode(self, gameMode):
        self.gameMode = gameMode
        if self.gameMode == GameMode.MINIMAX_LOCAL:
            self.setHumanPlayer(None)
        else:
            self.changePage(PageIdx.SELECT_SIDE)

    def setHumanPlayer(self, humanPlayer):
        self.humanPlayer = humanPlayer
        self.changePage(PageIdx.INPUT_MAX_TIME)

    # Game methods
    def initGameState(self, humanPlayer, boardSize, max_time):
        board = Board(boardSize, max_time=max_time)
        self.gameState = GameState(board, humanPlayer)

    def calculateAIMoveMinimax(self):
        print('ai move minimax')
        # Create worker instance
        self.workerMinimax = Worker(self.gameState.board.minimax, self.gameState.act_player)
        # Connect signals
        self.workerMinimax.signals.exception.connect(self.minimaxThreadException)
        self.workerMinimax.signals.result.connect(self.minimaxThreadResult)
        self.workerMinimax.signals.done.connect(self.minimaxThreadDone)
        # Run thread
        self.timerStart = time.time()
        self.threadPool.start(self.workerMinimax)

    def calculateAIMoveLocal(self):
        print('ai move local')
        # Create worker instance
        self.workerLocal = Worker(self.gameState.board.minimax_with_local, self.gameState.act_player)
        # Connect signals
        self.workerLocal.signals.exception.connect(self.minimaxThreadException)
        self.workerLocal.signals.result.connect(self.minimaxThreadResult)
        self.workerLocal.signals.done.connect(self.minimaxThreadDone)
        # Run thread
        self.timerStart = time.time()
        self.threadPool.start(self.workerLocal)

    def minimaxThreadException(self, exception):
        print(exception)

    def minimaxThreadResult(self, res):
        step = res[1]
        if step is None:
            print("No move available"); return
        self.gameState.board.apply_step(step)
        self.updatePionPositionUI()
        # check if AI win
        if self.checkWinnerUI(): return
        # next turn: human move
        self.gameState.next_turn()
        self.updatePlayerTurnUI()
        # next AI player if AI vs AI, else return control to human
        if self.gameMode == GameMode.MINIMAX_LOCAL:
            if self.gameState.act_player == Player.GREEN:
                self.timerMinimax += time.time() - self.timerStart
                self.calculateAIMoveLocal()
            else:
                self.timerLocal += time.time() - self.timerStart
                self.calculateAIMoveMinimax()
        elif self.gameMode == GameMode.HUMAN_LOCAL:
            self.timerLocal += time.time() - self.timerStart
        else:  # self.gameMode == GameMode.HUMAN_MINIMAX
            self.timerMinimax += time.time() - self.timerStart

    def minimaxThreadDone(self):
        print("AI move calculation done")

    # Helper methods
    def spawnDialogWindow(self, title, text, yesBtnLbl="Yes", noBtnLbl="No",
                          subtext="", type="Information", callback=None):
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
        message.addButton(yesBtnLbl, QMessageBox.YesRole)
        message.addButton(noBtnLbl, QMessageBox.NoRole)
        if callback: message.buttonClicked.connect(callback)
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
