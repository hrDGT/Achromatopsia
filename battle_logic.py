"""
battle_logic.py
===============
Содержит *только* игровую логику и данные, никакого Qt.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, List, Optional


# -------------------------------------------------------------------- #
#                              ДАННЫЕ                                  #
# -------------------------------------------------------------------- #
@dataclass(slots=True)
class Spell:
    icon: str
    animation: str
    damage: int
    cost: int


class StateError(RuntimeError):
    """Любая ошибка в логике (например, неправильный ход)."""


# -------------------------------------------------------------------- #
#                            BATTLE STATE                              #
# -------------------------------------------------------------------- #
class BattleState:
    """Чистая модель: здоровье, мана, чей ход, применение спеллов."""

    MAX_HEALTH = 20
    MAX_MANA = 20

    def __init__(
        self,
        spell_file: str = "assets/spells/spells.json",
        enemy_spell_file: str = "assets/spells/enemy_spells.json",
        player_spell_keys: Optional[List[str]] = None,
        enemy_data: Optional[Dict] = None,
        max_spells: int = 4
    ) -> None:
        # здоровье / мана
        self.player_hp = self.MAX_HEALTH
        self.player_mp = self.MAX_MANA

        # Данные врага
        self.enemy_data = enemy_data or {}
        self.enemy_hp = int(self.enemy_data.get('hp', 20))
        self.enemy_mp = int(self.enemy_data.get('mana', 20))

        # чей ход
        self.turn: str = random.choice(["player", "enemy"])

        # заклинания игрока
        all_spells = self._load_spells(spell_file)
        spell_keys = list(all_spells.keys())[:max_spells]  # Ограничиваем количество
        
        if player_spell_keys:
            self.spells = {k: v for k, v in all_spells.items() if k in player_spell_keys and k in spell_keys}
        else:
            self.spells = {k: all_spells[k] for k in spell_keys}

        # заклинания врага
        self.enemy_spells = self._load_enemy_spells(enemy_data, enemy_spell_file)

        # текущее выбранное (для анимации)
        self.last_player_spell: Tuple[str, Spell] | None = None
        self.last_enemy_spell: Tuple[str, Spell] | None = None

        # стартовый бонус маны стороне, что ходит первой
        if self.turn == "player":
            self.player_mp = min(self.MAX_MANA, self.player_mp + 2)
        else:
            self.enemy_mp = min(self.enemy_mp, self.enemy_mp + 2)

    # ---------------------------------------------------------------- #
    #                            PUBLIC API                            #
    # ---------------------------------------------------------------- #
    # ---- проверки ----
    def can_cast(self, spell_key: str) -> bool:
        """Достаточно ли маны у игрока для данного спелла?"""
        spell = self.spells.get(spell_key)
        return bool(spell and self.player_mp >= spell.cost)

    # ---- действия игрока ----
    def player_cast(self, spell_key: str) -> Spell:
        """Игрок кастует спелл. Возвращает объект Spell для анимации."""
        if self.turn != "player":
            raise StateError("Not player's turn")

        spell = self.spells.get(spell_key)
        if not spell:
            raise StateError("Unknown spell")
        if self.player_mp < spell.cost:
            raise StateError("Not enough mana")

        self.player_mp -= spell.cost
        self.enemy_hp = max(0, self.enemy_hp - spell.damage)
        self.last_player_spell = (spell_key, spell)

        self._end_turn()
        return spell

    # ---- ход врага ----
    def enemy_act(self) -> Spell | None:
        """
        Враг пытается кастовать. Если маны ни на что не хватает —
        он пропускает ход и возвращает None.
        """
        if self.turn != "enemy":
            raise StateError("Not enemy's turn")

        viable = [s for s in self.enemy_spells.values() if self.enemy_mp >= s.cost]
        if not viable:
            self._end_turn()
            return None

        spell = random.choice(viable)
        self.enemy_mp -= spell.cost
        self.player_hp = max(0, self.player_hp - spell.damage)
        self.last_enemy_spell = ("enemy_cast", spell)

        self._end_turn()
        return spell

    # ---------------------------------------------------------------- #
    #                         INTERNAL HELPERS                         #
    # ---------------------------------------------------------------- #
    @staticmethod
    def _load_spells(path: str) -> Dict[str, Spell]:
        """Чтение JSON → Dict[str, Spell]."""
        result: Dict[str, Spell] = {}
        try:
            with Path(path).open(encoding="utf-8") as f:
                raw = json.load(f)
            for key, val in raw.items():
                result[key] = Spell(
                    icon=val["icon"],
                    animation=val["animation"],
                    damage=int(val["damage"]),
                    cost=int(val["cost"]),
                )
        except Exception as exc:  # noqa: BLE001
            print(f"[BattleState] cannot read {path}: {exc}")
            result = {
                "fallback": Spell("default_icon.png", "default_animation.gif", 5, 3)
            }
        return result

    def _load_enemy_spells(self, enemy_data, enemy_spell_file: str):
        """Загружает заклинания врага из файла enemy_spells.json и фильтрует по enemy_data."""
        all_enemy_spells = self._load_spells(enemy_spell_file)

        if not enemy_data:
            return all_enemy_spells

        enemy_spells = {}
        for i in range(1, 5):
            spell_key = enemy_data.get(f'spell{i}')
            if spell_key and spell_key in all_enemy_spells:
                enemy_spells[spell_key] = all_enemy_spells[spell_key]

        return enemy_spells or all_enemy_spells

    def _end_turn(self) -> None:
        """Смена хода + +2 маны стороне, чей ход наступил."""
        self.turn = "enemy" if self.turn == "player" else "player"
        if self.turn == "player":
            self.player_mp = min(self.MAX_MANA, self.player_mp + 2)
        else:
            self.enemy_mp = min(self.enemy_mp, self.enemy_mp + 2)