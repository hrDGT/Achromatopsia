"""
battle_graphic.py
=================
Полный визуальный слой дуэли. Работает в паре с
battle_logic.BattleState (модель) и spell_icon.SpellIconItem (иконки).

• Игровое «полотно» фиксировано 1600 × 900 и центрируется
  внутри окна-контроллера.
• В конструкторе мы НЕ вызываем showFullScreen() и не ставим Frameless –
  этим управляет BattleWindow (F11 / Esc).
"""

from __future__ import annotations

import random
from typing import Dict, List

from PySide6.QtCore import Qt, QRectF, QSize, QTimer
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
    GAME_W, GAME_H = 1600, 900  # фиксированный «экран» игры

    # ---------------------------------------------------------------- #
    #                                init                              #
    # ---------------------------------------------------------------- #
    def __init__(self, state: BattleState) -> None:
        super().__init__()
        self.state = state

        # ---- базовые параметры окна / сцены ----
        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setFixedSize(self.GAME_W, self.GAME_H)  # главное: фиксированный размер

        # --------- геометрия (из исходника) ---------
        self.character_x, self.character_y = 0, 20
        self.character_width, self.character_height = 700, 700
        self.enemy_x, self.enemy_y = 800, 20
        self.enemy_width, self.enemy_height = 700, 700

        self.character_spell_x, self.character_spell_y = 90, 300
        self.character_spell_width, self.character_spell_height = 1350, 400
        self.enemy_spell_x, self.enemy_spell_y = 60, 250
        self.enemy_spell_width, self.enemy_spell_height = 1400, 270

        self.health_bar_width, self.health_bar_height = 336, 56
        self.mana_bar_width, self.mana_bar_height = 336, 28

        # ---------------- фон ----------------
        self.background_pixmap = QPixmap("assets/backgrounds/battle.png")
        if self.background_pixmap.isNull():
            self.background_pixmap = QPixmap(self.size())
            self.background_pixmap.fill(Qt.darkGray)

        self.background = QGraphicsPixmapItem()
        self.scene().addItem(self.background)

        # -------------- персонажи -------------
        self.character_item = QGraphicsPixmapItem()
        self.enemy_item = QGraphicsPixmapItem()
        self.scene().addItem(self.character_item)
        self.scene().addItem(self.enemy_item)

        # -------------- бары ------------------
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

        # ------------- спеллы / урон ----------
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

        # ------------- текст ------------------
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

        # -------------- сервисные поля ----------
        self.spell_icons: List[SpellIconItem] = []
        self.selected_spell: str | None = None
        self.spell_animations: Dict[str, QMovie] = {}

        self.is_attacking = self.is_casting = False
        self.is_enemy_attacking = self.is_enemy_casting = False
        self.is_enemy_taking_damage = self.is_character_taking_damage = False

        # -------------- запуск подсистем -------
        self.setup_animations()
        self.create_spell_panel()
        self.fit_background()
        self.update_text_values()
        self.set_spell_icons_active(self.state.turn == "player")

    # ====================================================================== #
    #                          ОБНОВЛЕНИЕ HUD                                #
    # ====================================================================== #
    def update_text_values(self) -> None:
        s = self.state
        self.character_health_text.setPlainText(str(s.player_hp))
        self.character_mana_text.setPlainText(str(s.player_mp))
        self.enemy_health_text.setPlainText(str(s.enemy_hp))
        self.enemy_mana_text.setPlainText(str(s.enemy_mp))

        self._update_bar(self.character_health_bar, s.player_hp, s.MAX_HEALTH, "health", "character")
        self._update_bar(self.enemy_health_bar, s.enemy_hp, s.MAX_HEALTH, "health", "enemy")
        self._update_bar(self.character_mana_bar, s.player_mp, s.MAX_MANA, "mana", "character")
        self._update_bar(self.enemy_mana_bar, s.enemy_mp, s.MAX_MANA, "mana", "enemy")

        self.update_health_bars_positions()
        self.update_mana_bars_positions()
        self.set_spell_icons_active(self.state.turn == "player")

    # ---- вспомогательный метод бара ----
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

    # ====================================================================== #
    #                       ПАНЕЛЬ СПЕЛЛОВ / ИКОНКИ                          #
    # ====================================================================== #
    def create_spell_panel(self) -> None:
        icon, margin, spacing = 96, 500, 15
        keys = list(self.state.spells.keys())
        panel_w = margin * 2 + icon * len(keys) + spacing * (len(keys) - 1)
        panel_h = icon + 30

        panel_pm = QPixmap("assets/gui/spell_panel.png")
        if panel_pm.isNull():
            panel_pm = QPixmap(panel_w, panel_h)
            panel_pm.fill(Qt.darkGray)
        self.spell_panel = QGraphicsPixmapItem(
            panel_pm.scaled(panel_w, panel_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        )
        self.scene().addItem(self.spell_panel)

        for i, key in enumerate(keys):
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

    # ====================================================================== #
    #                          АНИМАЦИИ / MOVIES                             #
    # ====================================================================== #
    def setup_animations(self) -> None:
        self.idle_movie = self._mk_movie("assets/animations/idle.gif", self.character_width, self.character_height)
        self.attack_movie = self._mk_movie("assets/animations/attack.gif", self.character_width, self.character_height)
        self.idle_movie.frameChanged.connect(lambda _: self.character_item.setPixmap(self.idle_movie.currentPixmap()))
        self.attack_movie.frameChanged.connect(self._update_attack_frame)
        self.idle_movie.start()

        self.enemy_movie = self._mk_movie("assets/animations/enemy_idle.gif", self.enemy_width, self.enemy_height)
        self.enemy_attack_movie = self._mk_movie("assets/animations/enemy_attack.gif", self.enemy_width, self.enemy_height)
        self.enemy_movie.frameChanged.connect(lambda _: self.enemy_item.setPixmap(self.enemy_movie.currentPixmap()))
        self.enemy_attack_movie.frameChanged.connect(self._update_enemy_attack_frame)
        self.enemy_movie.start()

        self.enemy_damage_movie = self._mk_movie("assets/animations/enemy_hurt.gif", self.enemy_width, self.enemy_height)
        self.enemy_damage_movie.frameChanged.connect(self._update_enemy_damage_frame)
        self.character_damage_movie = self._mk_movie("assets/animations/hurt.gif", self.character_width, self.character_height)
        self.character_damage_movie.frameChanged.connect(self._update_character_damage_frame)

        # позиции статичных айтемов
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

    # ------------------- клик по иконке -------------------
    def _handle_spell_click(self, k: str) -> None:
        if self.state.turn != "player" or self._any_anim_running():
            return
        if not self.state.can_cast(k):
            return
        self.selected_spell = k
        self.set_spell_icons_active(False)
        self._play_attack()

    # ------------------- атака персонажа ------------------
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

    # ------------------- спелл игрока ---------------------
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

    # ------------------- урон врагу -----------------------
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

    # ------------------- ход врага ------------------------
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

    # ------------------- урон игроку ----------------------
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

    # ====================================================================== #
    #                        ПОЗИЦИИ БАРОВ                                   #
    # ====================================================================== #
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

    # ====================================================================== #
    #                       фон и ресайз BattleView                           #
    # ====================================================================== #
    def resizeEvent(self, ev):  # noqa: N802
        super().resizeEvent(ev)
        if hasattr(self, "background_pixmap"):
            self.fit_background()

    def fit_background(self) -> None:
        vp_size = self.viewport().size()
        scaled = self.background_pixmap.scaled(
            vp_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        self.background.setPixmap(scaled)
        self.setSceneRect(QRectF(scaled.rect()))
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

    # ====================================================================== #
    #                   клавиши (цифры, F11/Esc передаём окну)                #
    # ====================================================================== #
    def keyPressEvent(self, e: QKeyEvent):  # noqa: N802
        if e.key() in (Qt.Key_F11, Qt.Key_Escape):
            self.window().keyPressEvent(e)
            return
        if Qt.Key_1 <= e.key() <= Qt.Key_5:
            idx = e.key() - Qt.Key_1
            keys = list(self.state.spells.keys())
            if idx < len(keys):
                self._handle_spell_click(keys[idx])
            return
        super().keyPressEvent(e)

    # ====================================================================== #
    #                       флаг «есть ли анимация»                           #
    # ====================================================================== #
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
