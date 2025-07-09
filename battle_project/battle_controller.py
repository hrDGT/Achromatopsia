
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from battle_logic import BattleState
from battle_graphic import BattleView


class BattleWindow(QMainWindow):
    """Glue‑layer that wires BattleState and BattleView together and
    implements the requested window behaviour (F11 / Esc toggling)."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Battle Scene")
        self._state = BattleState()
        self._view = BattleView(self._state)

        # ----------------------- Layout --------------------------- #
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._view)
        self.setCentralWidget(container)

        # ------------------ Window behaviour ---------------------- #
        self._fullscreen = False
        self.resize(self._view.GAME_WIDTH + 80, self._view.GAME_HEIGHT + 120)
        self.setMinimumSize(self._view.GAME_WIDTH, self._view.GAME_HEIGHT)

        # If enemy starts, give it a little delay to feel natural
        if self._state.current_turn == "enemy":
            QTimer.singleShot(1000, self._state.enemy_take_turn)

    # ================================================================= #
    #                             Key events                            #
    # ================================================================= #
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self._toggle_fullscreen()
            return
        if event.key() == Qt.Key_Escape and self._fullscreen:
            # Leave fullscreen but keep running
            self._toggle_fullscreen()
            return

        # Delegate everything else to the view so spells can be cast
        super().keyPressEvent(event)

    # ----------------------------------------------------------------- #
    #                      Fullscreen helper                            #
    # ----------------------------------------------------------------- #
    def _toggle_fullscreen(self):
        if self._fullscreen:
            self.showNormal()
            self._fullscreen = False
        else:
            self.showFullScreen()
            # Keep game area fixed & centred – layout already handles it
            self._fullscreen = True
