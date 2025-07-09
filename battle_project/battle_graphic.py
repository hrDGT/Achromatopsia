
from pathlib import Path
from typing import Callable, Dict

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsTextItem, QGraphicsView)

from battle_logic import BattleState


class SpellIconItem(QGraphicsPixmapItem):
    """Clickable icon representing a spell."""

    def __init__(self, pixmap: QPixmap, spell_key: str,
                 click_cb: Callable[[str], None]):
        super().__init__(pixmap)
        self.spell_key = spell_key
        self._click_cb = click_cb

        self.setAcceptHoverEvents(True)
        self.setOpacity(1.0)

    # ------------------------------ Events --------------------------- #
    def hoverEnterEvent(self, _):
        self.setOpacity(0.85)

    def hoverLeaveEvent(self, _):
        self.setOpacity(1.0)

    def mousePressEvent(self, _):
        if self._click_cb:
            self._click_cb(self.spell_key)

# ==================================================================== #
#                              BattleView                              #
# ==================================================================== #
class BattleView(QGraphicsView):
    """Presentation‑layer. Renders everything based on BattleState."""

    GAME_WIDTH = 1600
    GAME_HEIGHT = 900
    ICON_SIZE = 96

    def __init__(self, state: BattleState):
        super().__init__()

        self.state = state
        self.setFixedSize(self.GAME_WIDTH, self.GAME_HEIGHT)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

        # ------------- Scene & background ------------- #
        self.setScene(QGraphicsScene(self))
        bg_path = Path("assets/backgrounds/battle.png")
        self._bg_pixmap = (QPixmap(str(bg_path))
                           if bg_path.exists()
                           else QPixmap(self.GAME_WIDTH, self.GAME_HEIGHT))
        self._bg_item = QGraphicsPixmapItem()
        self.scene().addItem(self._bg_item)
        self._update_background()

        # ----------------- Text overlays -------------- #
        self._font = QFont("Arial", 18, QFont.Bold)

        self._player_hp_text = self._make_text_item()
        self._player_mp_text = self._make_text_item()
        self._enemy_hp_text = self._make_text_item()
        self._enemy_mp_text = self._make_text_item()

        self._layout_text()

        # ---------------- Spell panel ----------------- #
        self._spell_icons = []
        self._build_spell_panel()

        # --------- React on state signals ------------- #
        self.state.healthChanged.connect(self._update_text)
        self.state.manaChanged.connect(self._update_text)
        self.state.turnChanged.connect(self._on_turn_changed)

        self._update_text()

    # ------------------------------------------------------------------ #
    #                          Private helpers                           #
    # ------------------------------------------------------------------ #
    def _make_text_item(self) -> QGraphicsTextItem:
        item = QGraphicsTextItem()
        item.setFont(self._font)
        item.setDefaultTextColor(QColor(255, 255, 255))
        self.scene().addItem(item)
        return item

    def _layout_text(self):
        gap = 12
        self._player_hp_text.setPos(20, 20)
        self._player_mp_text.setPos(20, 20 + self._font.pointSize() * 2 + gap)

        right = self.GAME_WIDTH - 180
        self._enemy_hp_text.setPos(right, 20)
        self._enemy_mp_text.setPos(right, 20 + self._font.pointSize() * 2 + gap)

    def _update_text(self):
        self._player_hp_text.setPlainText(f"HP: {self.state.player_health}")
        self._player_mp_text.setPlainText(f"MP: {self.state.player_mana}")
        self._enemy_hp_text.setPlainText(f"Enemy HP: {self.state.enemy_health}")
        self._enemy_mp_text.setPlainText(f"Enemy MP: {self.state.enemy_mana}")

    def _on_turn_changed(self, turn: str):
        # Dim unavailable icons depending on whose turn it is
        active = (turn == "player")
        for icon in self._spell_icons:
            spell_available = self.state.can_cast(icon.spell_key)
            icon.setEnabled(active and spell_available)
            icon.setOpacity(1.0 if (active and spell_available) else 0.4)

    # --------------------- Spell panel --------------------------- #
    def _build_spell_panel(self):
        margin = 30
        spacing = 18
        keys = list(self.state.spells.keys())

        panel_width = (margin * 2 +
                       len(keys) * self.ICON_SIZE +
                       (len(keys) - 1) * spacing)
        panel_height = self.ICON_SIZE + 30

        # Background panel asset or simple rectangle
        panel_pixmap = QPixmap(panel_width, panel_height)
        panel_pixmap.fill(QColor(0, 0, 0, 150))
        self._panel_item = QGraphicsPixmapItem(panel_pixmap)
        self.scene().addItem(self._panel_item)

        # Center panel horizontally near bottom
        px = (self.GAME_WIDTH - panel_width) / 2
        py = self.GAME_HEIGHT - panel_height - 20
        self._panel_item.setPos(px, py)

        # Spell icons
        for i, key in enumerate(keys):
            spell = self.state.spells[key]
            icon_path = Path(f"assets/spells/{spell.icon}")
            icon_pixmap = (QPixmap(str(icon_path))
                           if icon_path.exists()
                           else QPixmap(self.ICON_SIZE, self.ICON_SIZE))
            icon_pixmap = icon_pixmap.scaled(
                self.ICON_SIZE, self.ICON_SIZE,
                Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )

            x = px + margin + i * (self.ICON_SIZE + spacing)
            y = py + 15

            item = SpellIconItem(icon_pixmap, key, self._on_spell_clicked)
            item.setPos(x, y)
            self.scene().addItem(item)
            self._spell_icons.append(item)

    def _on_spell_clicked(self, spell_key: str):
        self.state.cast_player_spell(spell_key)

    # ---------------------- Background --------------------------- #
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_background()

    def _update_background(self):
        scaled = self._bg_pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )
        self._bg_item.setPixmap(scaled)
        self.setSceneRect(QRectF(scaled.rect()))
