"""
spell_icon.py
=============
Кликабельная иконка заклинания с hover-/press-эффектами.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem


class SpellIconItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap, spell_id: str, parent=None) -> None:
        super().__init__(pixmap, parent)
        self.spell_id = spell_id

        # прозрачности
        self._normal = 1.0
        self._hover = 0.85
        self._pressed = 0.7
        self.setOpacity(self._normal)

    # ---------------- события мыши ---------------- #
    def hoverEnterEvent(self, event):  # noqa: N802
        if self.isEnabled():
            self.setOpacity(self._hover)
            self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # noqa: N802
        if self.isEnabled():
            self.setOpacity(self._normal)
            self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):  # noqa: N802
        if self.isEnabled():
            self.setOpacity(self._pressed)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if self.isEnabled():
            self.setOpacity(self._normal)
        super().mouseReleaseEvent(event)
