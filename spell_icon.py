"""
spell_icon.py
=============
Кликабельная иконка заклинания с hover-/press-эффектами.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor, QFont
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem


class SpellIconItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap, spell_id: str, spell_data: dict, parent=None) -> None:
        super().__init__(pixmap, parent)
        self.spell_id = spell_id
        self.spell_data = spell_data

        # прозрачности
        self._normal = 1.0
        self._hover = 0.85
        self._pressed = 0.7
        self.setOpacity(self._normal)
        
        # Таймер для отложенного показа описания
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(300)  # 0.3 секунды задержки
        self.hover_timer.timeout.connect(self.show_description)
        
        # Элементы для описания
        self.description_bg = None
        self.description_text = None

    def show_description(self):
        """Показать описание заклинания"""
        if not self.isEnabled() or not self.scene():
            return
            
        # Создаем фон для описания
        bg_pixmap = QPixmap("assets/gui/description_frame.png")
        if bg_pixmap.isNull():
            bg_pixmap = QPixmap(300, 200)
            bg_pixmap.fill(QColor(30, 30, 40, 230))
        
        self.description_bg = QGraphicsPixmapItem(bg_pixmap.scaled(300, 200, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        self.description_bg.setZValue(100)
        
        # Создаем текст описания
        description = self.spell_data.get('description', 'No description available')
        self.description_text = QGraphicsTextItem(description)
        self.description_text.setDefaultTextColor(Qt.white)
        self.description_text.setZValue(101)
        self.description_text.setTextWidth(240)  # Ширина текста с отступами
        self.description_text.setFont(QFont("Arial", 20))
        
        # Позиционируем описание
        scene_pos = self.mapToScene(self.boundingRect().center())
        panel_height = 100  # Примерная высота панели заклинаний
        description_y = scene_pos.y() - panel_height - 210  # 10px выше панели + высота описания
        
        self.description_bg.setPos(scene_pos.x() - 150, description_y)
        self.description_text.setPos(scene_pos.x() - 140, description_y + 10)
        
        # Добавляем на сцену
        self.scene().addItem(self.description_bg)
        self.scene().addItem(self.description_text)

    def hide_description(self):
        """Скрыть описание заклинания"""
        if self.description_bg and self.description_bg.scene():
            self.scene().removeItem(self.description_bg)
        if self.description_text and self.description_text.scene():
            self.scene().removeItem(self.description_text)
        
        self.description_bg = None
        self.description_text = None
        self.hover_timer.stop()

    # ---------------- события мыши ---------------- #
    def hoverEnterEvent(self, event):  # noqa: N802
        if self.isEnabled():
            self.setOpacity(self._hover)
            self.setCursor(Qt.PointingHandCursor)
            self.hover_timer.start()  # Запускаем таймер для показа описания
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # noqa: N802
        if self.isEnabled():
            self.setOpacity(self._normal)
            self.setCursor(Qt.ArrowCursor)
            self.hide_description()  # Скрываем описание
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):  # noqa: N802
        if self.isEnabled():
            self.setOpacity(self._pressed)
            self.setCursor(Qt.ArrowCursor)
            self.hide_description()  # Скрываем описание при клике
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if self.isEnabled():
            self.setOpacity(self._normal)
        super().mouseReleaseEvent(event)