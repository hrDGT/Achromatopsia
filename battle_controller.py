"""
battle_controller.py
====================
Связывает together модель (`BattleState`) и представление (`BattleView`).

• Создаёт окно с обычной рамкой ОС (чтобы были кнопки «свернуть/развернуть/закрыть»).
• Поддерживает горячие клавиши:
      F11 – полноэкранный режим
      Esc – выйти из полноэкранного
• Центрирует `BattleView` фиксированного размера 1600×900.
• Запускает первый ход врага, если он выпал моделью случайно.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from battle_logic import BattleState
from battle_graphic import BattleView


class BattleWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Battle Scene")

        # ------------ модель + вид ------------ #
        self.state = BattleState()
        self.view = BattleView(self.state)

        # ------------ размещение -------------- #
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.view)
        self.setCentralWidget(container)

        # ------------ стартовый размер -------- #
        self.resize(self.view.GAME_W + 120, self.view.GAME_H + 120)
        self.setMinimumSize(self.view.GAME_W, self.view.GAME_H)
        self._fullscreen = False

        # ------------ ход врага (если первый) --#
        if self.state.turn == "enemy":
            # даём секунду «подумать»
            QTimer.singleShot(1000, self.view.start_enemy_turn)

    # ================================================================= #
    #                            shortcuts                              #
    # ================================================================= #
    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key_F11:
            self._toggle_fullscreen()
            return
        if event.key() == Qt.Key_Escape and self._fullscreen:
            self._toggle_fullscreen()
            return
        super().keyPressEvent(event)

    # ------------------------- helpers ------------------------------- #
    def _toggle_fullscreen(self) -> None:
        if self._fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self._fullscreen = not self._fullscreen
