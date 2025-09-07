from __future__ import annotations

import random
from typing import Dict, List

from PySide6.QtCore import Qt, QRectF, QSize, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeyEvent,
    QMovie,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)

from battle_logic import BattleState
from spell_icon import SpellIconItem


class BattleView(QGraphicsView):
    GAME_W, GAME_H = 1600, 800 
    battle_outcome = Signal(str)

    def __init__(self, state: BattleState, background="battle.png") -> None:
        super().__init__()
        self.state = state
        self.background = background

        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        # Убираем фиксированный размер и устанавливаем минимальный
        self.setMinimumSize(400, 300)

        self.character_x, self.character_y = 0, 20
        self.character_width, self.character_height = 700, 700
        self.enemy_x, self.enemy_y = 800, 20
        self.enemy_width, self.enemy_height = 700, 700

        self.character_spell_x, self.character_spell_y = 90, 300
        self.character_spell_width, self.character_spell_height = 1400, 400
        self.enemy_spell_x, self.enemy_spell_y = 70, 300
        self.enemy_spell_width, self.enemy_spell_height = 1400, 400

        self.health_bar_width, self.health_bar_height = 336, 56
        self.mana_bar_width, self.mana_bar_height = 336, 28

        self.background_pixmap = QPixmap(f"assets/backgrounds/{self.background}")
        if self.background_pixmap.isNull():
            self.background_pixmap = QPixmap(self.size())
            self.background_pixmap.fill(Qt.darkGray)

        self.background_item = QGraphicsPixmapItem()
        self.scene().addItem(self.background_item)

        self.character_item = QGraphicsPixmapItem()
        self.enemy_item = QGraphicsPixmapItem()
        self.scene().addItem(self.character_item)
        self.scene().addItem(self.enemy_item)

        self.character_health_bar = QGraphicsPixmapItem()
        self.enemy_health_bar = QGraphicsPixmapItem()
        self.character_mana_bar = QGraphicsPixmapItem()
        self.enemy_mana_bar = QGraphicsPixmapItem()
        for bar in (
            self.character_health_bar,
            self.enemy_health_bar,
            self.character_mana_bar,
            self.enemy_mana_bar,
        ):
            self.scene().addItem(bar)
            bar.setZValue(20)

        self.spell_item = QGraphicsPixmapItem()
        self.enemy_spell_item = QGraphicsPixmapItem()
        self.enemy_damage_item = QGraphicsPixmapItem()
        self.character_damage_item = QGraphicsPixmapItem()
        for itm in (
            self.spell_item,
            self.enemy_spell_item,
            self.enemy_damage_item,
            self.character_damage_item,
        ):
            self.scene().addItem(itm)
            itm.setVisible(False)
        self.enemy_damage_item.setZValue(10)
        self.character_damage_item.setZValue(10)

        self.character_health_text = QGraphicsTextItem()
        self.character_mana_text = QGraphicsTextItem()
        self.enemy_health_text = QGraphicsTextItem()
        self.enemy_mana_text = QGraphicsTextItem()
        for t in (
            self.character_health_text,
            self.character_mana_text,
            self.enemy_health_text,
            self.enemy_mana_text,
        ):
            self.scene().addItem(t)
            t.setZValue(30)

        self.text_font = QFont("Arial", 16, QFont.Bold)
        for t in (
            self.character_health_text,
            self.character_mana_text,
            self.enemy_health_text,
            self.enemy_mana_text,
        ):
            t.setFont(self.text_font)
        self.character_health_text.setDefaultTextColor(QColor(255, 50, 50))
        self.enemy_health_text.setDefaultTextColor(QColor(255, 50, 50))
        self.character_mana_text.setDefaultTextColor(QColor(50, 150, 255))
        self.enemy_mana_text.setDefaultTextColor(QColor(50, 150, 255))

        self.spell_icons: List[SpellIconItem] = []
        self.selected_spell: str | None = None
        self.spell_animations: Dict[str, QMovie] = {}

        self.is_attacking = self.is_casting = False
        self.is_enemy_attacking = self.is_enemy_casting = False
        self.is_enemy_taking_damage = self.is_character_taking_damage = False

        self.setup_animations()
        self.create_spell_panel()
        self.fit_background()
        self.update_text_values()
        self.set_spell_icons_active(self.state.turn == "player")

    def update_text_values(self) -> None:
        s = self.state
        self.character_health_text.setPlainText(str(s.player_hp))
        self.character_mana_text.setPlainText(str(s.player_mp))
        self.enemy_health_text.setPlainText(str(s.enemy_hp))
        self.enemy_mana_text.setPlainText(str(s.enemy_mp))

        if s.player_hp <= 0:
            self.battle_outcome.emit("lose")
            return
        elif s.enemy_hp <= 0:
            self.battle_outcome.emit("win")
            return

        self._update_bar(self.character_health_bar, s.player_hp, s.MAX_HEALTH, "health", "character")
        self._update_bar(self.enemy_health_bar, s.enemy_hp, s.MAX_HEALTH, "health", "enemy")
        self._update_bar(self.character_mana_bar, s.player_mp, s.MAX_MANA, "mana", "character")
        self._update_bar(self.enemy_mana_bar, s.enemy_mp, s.MAX_MANA, "mana", "enemy")

        self.update_health_bars_positions()
        self.update_mana_bars_positions()
        
        can_cast_any = any(self.state.player_mp >= spell.cost for spell in self.state.spells.values())
        if self.state.turn == "player" and not can_cast_any:
            self.set_spell_icons_active(False)
            QTimer.singleShot(1000, self._skip_player_turn)
        else:
            self.set_spell_icons_active(self.state.turn == "player")

    def _skip_player_turn(self) -> None:
        """Пропускаем ход игрока из-за недостатка маны"""
        if self.state.turn != "player" or self._any_anim_running():
            return
        
        self.state._end_turn()
        self.update_text_values()
        if self.state.turn == "enemy":
            QTimer.singleShot(1000, self.start_enemy_turn)

    def _update_bar(
        self,
        bar_item: QGraphicsPixmapItem,
        value: int,
        maximum: int,
        bar_type: str,
        owner: str,
    ) -> None:
        if value <= 0:
            idx = 5
        else:
            r = value / maximum
            idx = 1 if r > 0.75 else 2 if r >= 0.55 else 3 if r >= 0.3 else 4

        base = (
            ("enemy_hp_bar" if bar_type == "health" else "enemy_mana_bar")
            if owner == "enemy"
            else ("hp_bar" if bar_type == "health" else "mana_bar")
        )
        path = f"assets/gui/{base}{idx}.png"
        pm = QPixmap(path)
        if pm.isNull():
            pm = QPixmap(QSize(
                self.health_bar_width if bar_type == "health" else self.mana_bar_width,
                self.health_bar_height if bar_type == "health" else self.mana_bar_height,
            ))
            pm.fill(QColor(150, 150, 150))
        target = QSize(
            self.health_bar_width if bar_type == "health" else self.mana_bar_width,
            self.health_bar_height if bar_type == "health" else self.mana_bar_height,
        )
        bar_item.setPixmap(pm.scaled(target, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def create_spell_panel(self) -> None:

        spell_keys = list(self.state.spells.keys())

        MAX_SPELLS = 4
        if len(spell_keys) > MAX_SPELLS:
            spell_keys = spell_keys[:MAX_SPELLS]

        icon, margin, spacing = 96, 500, 15
        panel_w = margin * 2 + icon * len(spell_keys) + spacing * (len(spell_keys) - 1)
        panel_h = icon + 30

        panel_pm = QPixmap("assets/gui/spell_panel.png")
        if panel_pm.isNull():
            panel_pm = QPixmap(panel_w, panel_h)
            panel_pm.fill(Qt.darkGray)
        self.spell_panel = QGraphicsPixmapItem(
            panel_pm.scaled(panel_w, panel_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        )
        self.scene().addItem(self.spell_panel)

        for i, key in enumerate(spell_keys):
            sp = self.state.spells[key]
            icon_pm = QPixmap(f"assets/spells/{sp.icon}")
            if icon_pm.isNull():
                icon_pm = QPixmap(icon, icon)
                icon_pm.fill(Qt.red if i % 2 else Qt.blue)

            itm = SpellIconItem(
                icon_pm.scaled(icon, icon, Qt.IgnoreAspectRatio, Qt.SmoothTransformation),
                key,
                self.spell_panel,
            )
            x = margin + i * (icon + spacing)
            itm.setPos(x, 15)
            itm.setAcceptHoverEvents(True)
            itm.mousePressEvent = lambda e, k=key: self._handle_spell_click(k)
            self.spell_icons.append(itm)

    def set_spell_icons_active(self, active: bool) -> None:
        for ic in self.spell_icons:
            sp = self.state.spells[ic.spell_id]
            enabled = active and self.state.player_mp >= sp.cost
            ic.setEnabled(enabled)
            ic.setOpacity(1.0 if enabled else 0.5)

    def setup_animations(self) -> None:
        self.idle_movie = self._mk_movie("assets/animations/idle.gif", self.character_width, self.character_height)
        self.attack_movie = self._mk_movie("assets/animations/attack.gif", self.character_width, self.character_height)
        self.idle_movie.frameChanged.connect(lambda _: self.character_item.setPixmap(self.idle_movie.currentPixmap()))
        self.attack_movie.frameChanged.connect(self._update_attack_frame)
        self.idle_movie.start()

        enemy_idle = self.state.enemy_data.get("idle", "enemy_idle.gif")
        enemy_attack = self.state.enemy_data.get("attack", "enemy_attack.gif")
        enemy_hurt = self.state.enemy_data.get("hurt", "enemy_hurt.gif")

        self.enemy_movie = self._mk_movie(f"assets/animations/{enemy_idle}", self.enemy_width, self.enemy_height)
        self.enemy_attack_movie = self._mk_movie(f"assets/animations/{enemy_attack}", self.enemy_width, self.enemy_height)
        self.enemy_movie.frameChanged.connect(lambda _: self.enemy_item.setPixmap(self.enemy_movie.currentPixmap()))
        self.enemy_attack_movie.frameChanged.connect(self._update_enemy_attack_frame)
        self.enemy_movie.start()

        self.enemy_damage_movie = self._mk_movie(f"assets/animations/{enemy_hurt}", self.enemy_width, self.enemy_height)
        self.enemy_damage_movie.frameChanged.connect(self._update_enemy_damage_frame)
        self.character_damage_movie = self._mk_movie("assets/animations/hurt.gif", self.character_width, self.character_height)
        self.character_damage_movie.frameChanged.connect(self._update_character_damage_frame)

        self.character_item.setPos(self.character_x, self.character_y)
        self.character_damage_item.setPos(self.character_x, self.character_y)
        self.enemy_item.setPos(self.enemy_x, self.enemy_y)
        self.enemy_damage_item.setPos(self.enemy_x, self.enemy_y)
        self.spell_item.setPos(self.character_spell_x, self.character_spell_y)
        self.enemy_spell_item.setPos(self.enemy_spell_x, self.enemy_spell_y)

    @staticmethod
    def _mk_movie(path: str, w: int, h: int) -> QMovie:
        mv = QMovie(path)
        mv.setScaledSize(QSize(w, h))
        return mv

    def _handle_spell_click(self, k: str) -> None:
        if self.state.turn != "player" or self._any_anim_running():
            return
        if not self.state.can_cast(k):
            return
        self.selected_spell = k
        self.set_spell_icons_active(False)
        self._play_attack()

    def _play_attack(self) -> None:
        if self.is_attacking:
            return
        self.idle_movie.stop()
        self.attack_movie.start()
        self.attack_movie.jumpToFrame(0)
        self.is_attacking = True

    def _update_attack_frame(self, fr: int) -> None:
        self.character_item.setPixmap(self.attack_movie.currentPixmap())
        if fr == self.attack_movie.frameCount() - 1:
            self.attack_movie.stop()
            self.is_attacking = False
            self.idle_movie.start()
            self._play_player_spell()

    def _play_player_spell(self) -> None:
        if self.is_casting or self.selected_spell is None:
            return
        spell = self.state.spells[self.selected_spell]
        mv = self.spell_animations.get(spell.animation)
        if mv is None:
            mv = QMovie(f"assets/animations/{spell.animation}")
            mv.setScaledSize(QSize(self.character_spell_width, self.character_spell_height))
            self.spell_animations[spell.animation] = mv
        self.spell_movie = mv
        mv.frameChanged.connect(self._update_player_spell_frame)
        self.spell_item.setVisible(True)
        mv.start()
        mv.jumpToFrame(0)
        self.is_casting = True

    def _update_player_spell_frame(self, fr: int) -> None:
        self.spell_item.setPixmap(self.spell_movie.currentPixmap())
        if fr == self.spell_movie.frameCount() - 1:
            self.spell_movie.stop()
            self.spell_item.setVisible(False)
            self.is_casting = False
            self.state.player_cast(self.selected_spell)
            self.selected_spell = None
            self.update_text_values()
            self._play_enemy_hurt()

    def _play_enemy_hurt(self) -> None:
        if self.is_enemy_taking_damage:
            return
        self.enemy_item.setVisible(False)
        self.enemy_damage_item.setVisible(True)
        self.enemy_damage_movie.start()
        self.enemy_damage_movie.jumpToFrame(0)
        self.is_enemy_taking_damage = True

    def _update_enemy_damage_frame(self, fr: int) -> None:
        self.enemy_damage_item.setPixmap(self.enemy_damage_movie.currentPixmap())
        if fr == self.enemy_damage_movie.frameCount() - 1:
            self.enemy_damage_movie.stop()
            self.enemy_damage_item.setVisible(False)
            self.enemy_item.setVisible(True)
            self.is_enemy_taking_damage = False
            self._enemy_turn()

    def _enemy_turn(self) -> None:
        if self.state.turn != "enemy" or self._any_anim_running():
            return
        self.enemy_movie.stop()
        self.enemy_attack_movie.start()
        self.enemy_attack_movie.jumpToFrame(0)
        self.is_enemy_attacking = True

    def start_enemy_turn(self) -> None:
        """Вызывается контроллером через QTimer.singleShot."""
        self._enemy_turn()

    def _update_enemy_attack_frame(self, fr: int) -> None:
        self.enemy_item.setPixmap(self.enemy_attack_movie.currentPixmap())
        if fr == self.enemy_attack_movie.frameCount() - 1:
            self.enemy_attack_movie.stop()
            self.enemy_movie.start()
            self.is_enemy_attacking = False
            self._play_enemy_spell()

    def _play_enemy_spell(self) -> None:
        if self.is_enemy_casting:
            return
        spell = self.state.enemy_act()
        if spell is None:
            self.update_text_values()
            return
        mv = self.spell_animations.get(spell.animation)
        if mv is None:
            mv = QMovie(f"assets/animations/{spell.animation}")
            mv.setScaledSize(QSize(self.enemy_spell_width, self.enemy_spell_height))
            self.spell_animations[spell.animation] = mv
        self.enemy_spell_movie = mv
        mv.frameChanged.connect(self._update_enemy_spell_frame)
        self.enemy_spell_item.setVisible(True)
        mv.start()
        mv.jumpToFrame(0)
        self.is_enemy_casting = True

    def _update_enemy_spell_frame(self, fr: int) -> None:
        self.enemy_spell_item.setPixmap(self.enemy_spell_movie.currentPixmap())
        if fr == self.enemy_spell_movie.frameCount() - 1:
            self.enemy_spell_movie.stop()
            self.enemy_spell_item.setVisible(False)
            self.is_enemy_casting = False
            self.update_text_values()
            self._play_player_hurt()

    def _play_player_hurt(self) -> None:
        if self.is_character_taking_damage:
            return
        self.character_item.setVisible(False)
        self.character_damage_item.setVisible(True)
        self.character_damage_movie.start()
        self.character_damage_movie.jumpToFrame(0)
        self.is_character_taking_damage = True

    def _update_character_damage_frame(self, fr: int) -> None:
        self.character_damage_item.setPixmap(self.character_damage_movie.currentPixmap())
        if fr == self.character_damage_movie.frameCount() - 1:
            self.character_damage_movie.stop()
            self.character_damage_item.setVisible(False)
            self.character_item.setVisible(True)
            self.is_character_taking_damage = False
            self.update_text_values()
            self.set_spell_icons_active(True)

    def update_health_bars_positions(self) -> None:
        if not hasattr(self, "spell_panel"):
            return
        pos = self.spell_panel.pos()
        panel_w = self.spell_panel.pixmap().width()
        panel_h = self.spell_panel.pixmap().height()
        offset = 20

        char_x = pos.x() - self.health_bar_width - offset + 410
        char_y = pos.y() + (panel_h - self.health_bar_height - self.mana_bar_height - 5) / 2
        self.character_health_bar.setPos(char_x, char_y)
        self.character_health_text.setPos(char_x + self.health_bar_width + 5, char_y)

        enemy_x = pos.x() + panel_w + offset - 410
        enemy_y = char_y
        self.enemy_health_bar.setPos(enemy_x, enemy_y)
        self.enemy_health_text.setPos(
            enemy_x - self.enemy_health_text.boundingRect().width() - 5, enemy_y
        )

    def update_mana_bars_positions(self) -> None:
        if not hasattr(self, "spell_panel"):
            return
        char_hp = self.character_health_bar.pos()
        enemy_hp = self.enemy_health_bar.pos()

        char_x = char_hp.x()
        char_y = char_hp.y() + self.health_bar_height + 5
        self.character_mana_bar.setPos(char_x, char_y)
        self.character_mana_text.setPos(char_x + self.mana_bar_width + 5, char_y)

        enemy_x = enemy_hp.x()
        enemy_y = enemy_hp.y() + self.health_bar_height + 5
        self.enemy_mana_bar.setPos(enemy_x, enemy_y)
        self.enemy_mana_text.setPos(
            enemy_x - self.enemy_mana_text.boundingRect().width() - 5, enemy_y
        )

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if hasattr(self, "background_pixmap"):
            self.fit_background()
    def fit_background(self) -> None:
        vp_size = self.viewport().size()
        img_size = self.background_pixmap.size()
    
        scale_x = vp_size.width() / img_size.width()
        scale_y = vp_size.height() / img_size.height()
        scale = max(scale_x, scale_y)  
    
        scaled_size = QSize(
            int(img_size.width() * scale),
            int(img_size.height() * scale)
        )
        scaled = self.background_pixmap.scaled(
            scaled_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
    
        self.background_item.setPixmap(scaled)
    
        x = (vp_size.width() - scaled_size.width()) / 2
        y = (vp_size.height() - scaled_size.height()) / 2
        self.background_item.setPos(x, y)
    
        self.setSceneRect(QRectF(0, 0, vp_size.width(), vp_size.height()))
    
        self._update_panel_position()
        self.update_health_bars_positions()
        self.update_mana_bars_positions()

    def _update_panel_position(self) -> None:
        if not hasattr(self, "spell_panel"):
            return
        r = self.viewport().rect()
        pw = self.spell_panel.pixmap().width()
        ph = self.spell_panel.pixmap().height()
        self.spell_panel.setPos((r.width() - pw) / 2, r.height() - ph - 10)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in (Qt.Key_F11, Qt.Key_Escape):
            self.window().keyPressEvent(e)
            return

        if Qt.Key_1 <= e.key() <= Qt.Key_4:
            idx = e.key() - Qt.Key_1
            if idx < len(self.spell_icons):
                spell_key = self.spell_icons[idx].spell_id
                self._handle_spell_click(spell_key)
            return

        super().keyPressEvent(e)

    def _any_anim_running(self) -> bool:
        return any(
            (
                self.is_attacking,
                self.is_casting,
                self.is_enemy_attacking,
                self.is_enemy_casting,
                self.is_enemy_taking_damage,
                self.is_character_taking_damage,
            )
        )