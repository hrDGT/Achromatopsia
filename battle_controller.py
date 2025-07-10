"""
battle_controller.py
====================
Связывает together модель (`BattleState`) и представление (`BattleView`).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout

from battle_logic import BattleState
from battle_graphic import BattleView


class BattleWindow(QWidget):
    battle_finished = Signal(bool)

    def __init__(self, scene_number, player_spells, enemy_data, parent=None) -> None:
        super().__init__(parent)
        self.scene_number = scene_number
        self.player_spells = player_spells
        self.enemy_data = enemy_data

        # ------------ модель + вид ------------ #
        self.state = BattleState(
            player_spell_keys=player_spells,
            enemy_data=enemy_data
        )
        self.view = BattleView(self.state, self.enemy_data.get('background', 'battle.png'))

        # ------------ размещение -------------- #
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        # ------------ стартовый размер -------- #
        self.setMinimumSize(800, 450)

        # Подключаем обработчик результата боя
        self.view.battle_outcome.connect(self.handle_battle_outcome)

        # ------------ ход врага (если первый) --#
        if self.state.turn == "enemy":
            # даём секунду «подумать»
            QTimer.singleShot(1000, self.view.start_enemy_turn)

    def handle_battle_outcome(self, outcome):
        """Обработка результата боя (победа или поражение)"""
        victory = outcome == "win"
        self.battle_finished.emit(victory)
