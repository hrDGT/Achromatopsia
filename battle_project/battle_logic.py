
import json
import random
from dataclasses import dataclass
from pathlib import Path
from PySide6.QtCore import QObject, Signal


@dataclass
class Spell:
    icon: str
    animation: str
    damage: int
    cost: int


class BattleState(QObject):
    """Pure game‑logic layer.
    Exposes Qt signals so the graphic layer can stay in sync."""

    healthChanged = Signal()
    manaChanged = Signal()
    turnChanged = Signal(str)        # 'player' | 'enemy'
    spellCast = Signal(str, int)     # spell_key, damage
    enemySpellCast = Signal(str, int)

    def __init__(self,
                 spells_file: str = "assets/spells/spells.json",
                 enemy_spells_file: str = "assets/spells/enemy_spells.json",
                 max_health: int = 20,
                 max_mana: int = 20):
        super().__init__()

        self.max_health = max_health
        self.max_mana = max_mana

        self.player_health = max_health
        self.player_mana = max_mana
        self.enemy_health = max_health
        self.enemy_mana = max_mana

        self.spells = self._load_spells(spells_file)
        self.enemy_spells = self._load_spells(enemy_spells_file)

        self.current_turn = random.choice(["player", "enemy"])
        self.turnChanged.emit(self.current_turn)

    # ------------------------------------------------------------------ #
    #                             Public API                             #
    # ------------------------------------------------------------------ #
    def can_cast(self, spell_key: str) -> bool:
        spell = self.spells.get(spell_key)
        return bool(spell and self.player_mana >= spell.cost)

    def cast_player_spell(self, spell_key: str):
        """Player attempts to cast a spell."""
        if self.current_turn != "player" or not self.can_cast(spell_key):
            return

        spell = self.spells[spell_key]
        self.player_mana -= spell.cost
        self.enemy_health = max(0, self.enemy_health - spell.damage)

        # Notify listeners
        self.manaChanged.emit()
        self.healthChanged.emit()
        self.spellCast.emit(spell_key, spell.damage)

        self._end_turn()

    def enemy_take_turn(self):
        """Enemy randomly chooses an available spell or skips the turn."""
        if self.current_turn != "enemy":
            return

        available = [(k, s) for k, s in self.enemy_spells.items()
                     if self.enemy_mana >= s.cost]

        if not available:
            # No mana – just end the turn
            self._end_turn()
            return

        spell_key, spell = random.choice(available)
        self.enemy_mana -= spell.cost
        self.player_health = max(0, self.player_health - spell.damage)

        self.manaChanged.emit()
        self.healthChanged.emit()
        self.enemySpellCast.emit(spell_key, spell.damage)

        self._end_turn()

    # ------------------------------------------------------------------ #
    #                          Internal helpers                          #
    # ------------------------------------------------------------------ #
    def _load_spells(self, path: str):
        result = {}
        try:
            with Path(path).open("r", encoding="utf‑8") as f:
                data = json.load(f)
            for k, v in data.items():
                result[k] = Spell(
                    icon=v["icon"],
                    animation=v["animation"],
                    damage=int(v["damage"]),
                    cost=int(v["cost"])
                )
        except Exception as exc:
            print(f"[BattleState] Failed to load spells from {path}: {exc}")
        return result

    def _end_turn(self):
        # Switch active side
        self.current_turn = "enemy" if self.current_turn == "player" else "player"

        # 2 mana at the start of each turn
        if self.current_turn == "player":
            self.player_mana = min(self.max_mana, self.player_mana + 2)
        else:
            self.enemy_mana = min(self.max_mana, self.enemy_mana + 2)

        self.turnChanged.emit(self.current_turn)
