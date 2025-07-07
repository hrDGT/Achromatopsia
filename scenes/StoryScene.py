# This Python file uses the following encoding: utf-8

import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget,
                              QListWidgetItem, QGraphicsScene, QGraphicsView,
                              QGraphicsPixmapItem, QGraphicsTextItem)
from PySide6.QtGui import QPixmap, QColor, QFont
from PySide6.QtCore import Qt, QUrl, QEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtSvgWidgets import QGraphicsSvgItem


class StoryScene(QWidget):
    def __init__(self, scene_number=1, parent=None, media_player=None, audio_output=None,
                 music_continue=False, min_allowed_scene=None, max_allowed_scene=None):
        super().__init__(parent)
        self.scene_number = scene_number
        self.scenes_data = self.load_scenes_data()
        self.background_item = None
        self.character_item = None
        self.text_rect_item = None
        self.text_item = None
        self.arrow_item = None
        self.all_scenes_text_item = None
        self.scene_list_widget = None
        self.showing_all_scenes = False

        if min_allowed_scene is None or max_allowed_scene is None:
            if self.scene_number < 15:
                self.min_allowed_scene = 1
                self.max_allowed_scene = self.scene_number
            else:
                self.min_allowed_scene = self.scene_number - 20 + 1
                self.max_allowed_scene = self.scene_number
        else:
            self.min_allowed_scene = min_allowed_scene
            self.max_allowed_scene = max_allowed_scene

        if media_player and audio_output:
            self.media_player = media_player
            self.audio_output = audio_output
        else:
            self.audio_output = QAudioOutput()
            self.media_player = QMediaPlayer()
            self.media_player.setAudioOutput(self.audio_output)

        self.init_ui()

        self.play_scene_music(music_continue)

    def load_scenes_data(self):
        try:
            with open(os.path.join('scenes', 'scenes_data.json'), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке scenes_data.json: {e}")
            return {}


    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.view = QGraphicsView()
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setFocusPolicy(Qt.NoFocus)

        self.add_background_layer()
        self.add_character_layer()
        self.add_textbox_layer()

        layout.addWidget(self.view, 4)

        self.setLayout(layout)

        self.view.resizeEvent = self.on_view_resize
        self.view.installEventFilter(self)

        self.setFocusPolicy(Qt.StrongFocus)


    def add_background_layer(self):
        self.background_item = QGraphicsPixmapItem()

        scene_key = str(self.scene_number)

        if scene_key in self.scenes_data:
            bg_filename = self.scenes_data[scene_key].get('background')
            if bg_filename:
                full_path = os.path.join('assets', 'backgrounds', bg_filename)
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        self.background_item.setPixmap(pixmap)
                        self.scene.addItem(self.background_item)
                        self.update_background_scale()
                        return
                    else:
                        print(f"Не удалось загрузить изображение: {full_path}")
                else:
                    print(f"Файл фона не найден: {full_path}")


    def update_background_scale(self):
        if self.background_item is None:
            return

        view_size = self.view.viewport().size()
        pixmap = self.background_item.pixmap()
        if pixmap.isNull():
            return

        scale_x = view_size.width() / pixmap.width()
        scale_y = view_size.height() / pixmap.height()

        from PySide6.QtGui import QTransform
        transform = QTransform()
        transform.scale(scale_x, scale_y)
        self.background_item.setTransform(transform)

        self.background_item.setPos(0, 0)

        self.scene.setSceneRect(0, 0, view_size.width(), view_size.height())


    def add_character_layer(self):
        scene_key = str(self.scene_number)
        character_filename = self.scenes_data.get(scene_key, {}).get('character', None)

        self.character_item = QGraphicsPixmapItem()

        if character_filename:
            full_path = os.path.join('assets', 'characters', character_filename)
            if os.path.exists(full_path):
                pixmap = QPixmap(full_path)
                if not pixmap.isNull():
                    self.character_item.setPixmap(pixmap)
                else:
                    print(f"Не удалось загрузить изображение персонажа: {full_path}")
            else:
                print(f"Файл персонажа не найден: {full_path}")
        else:
            pixmap = QPixmap(200, 300)
            color = QColor(200, 150, 100 + self.scene_number * 20)
            pixmap.fill(color)
            self.character_item.setPixmap(pixmap)

        self.scene.addItem(self.character_item)
        self.update_character_scale_and_position()


    def update_character_scale_and_position(self):
        if self.character_item is None:
            return

        view_size = self.view.viewport().size()

        max_width = view_size.width() * 0.25
        max_height = view_size.height() * 0.5

        pixmap = self.character_item.pixmap()
        if pixmap.isNull():
            return

        orig_width = pixmap.width()
        orig_height = pixmap.height()

        scale_w = max_width / orig_width * 1.75
        scale_h = max_height / orig_height * 1.75

        scale = min(scale_w, scale_h, 1.0)

        from PySide6.QtGui import QTransform
        transform = QTransform()
        transform.scale(scale, scale)
        self.character_item.setTransform(transform)

        pos_x = view_size.width() * 0.55
        pos_y = (view_size.height() - orig_height * scale)
        self.character_item.setPos(pos_x, pos_y)


    def add_textbox_layer(self):
        scene_key = str(self.scene_number)
        text = self.scenes_data.get(scene_key, {}).get('text', '')
        if not text:
            return

        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtGui import QColor, QBrush

        self.text_rect_item = QGraphicsRectItem()
        self.text_rect_item.setBrush(QBrush(QColor(0, 0, 0, 180)))
        self.text_rect_item.setPen(Qt.NoPen)
        self.scene.addItem(self.text_rect_item)

        self.text_item = QGraphicsTextItem(text)
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        self.text_item.setFont(QFont("Arial", 12))
        self.scene.addItem(self.text_item)

        arrow_path = os.path.join('assets', 'misc', 'right_arrow.svg')
        if os.path.exists(arrow_path):
            self.arrow_item = QGraphicsSvgItem(arrow_path)
            self.arrow_item.setZValue(1)
            self.scene.addItem(self.arrow_item)
        else:
            print(f"SVG стрелки не найден: {arrow_path}")


        self.update_textbox_layout()


    def update_textbox_layout(self):
        if self.text_rect_item is None or self.text_item is None:
            return

        view_size = self.view.viewport().size()
        margin = 40
        padding = 10

        width = view_size.width() - 2 * margin
        height = 100
        x = margin
        y = view_size.height() - height - margin

        self.text_rect_item.setRect(x, y, width, height)

        self.text_item.setTextWidth(width - 2 * padding)
        self.text_item.setPos(x + padding, y + padding)

        if self.arrow_item:
            arrow_width = 50
            arrow_height = 50

            bounds = self.arrow_item.boundingRect()
            scale_x = arrow_width / bounds.width()
            scale_y = arrow_height / bounds.height()
            self.arrow_item.setScale(min(scale_x, scale_y))

            arrow_x = x + width - arrow_width - padding
            arrow_y = y + padding
            self.arrow_item.setPos(arrow_x, arrow_y)


    def play_scene_music(self, music_continue=False):
        scene_key = str(self.scene_number)
        if scene_key in self.scenes_data:
            music_filename = self.scenes_data[scene_key].get('music')

            if music_filename:
                music_path = os.path.abspath(os.path.join('assets', 'sounds', music_filename))
                if os.path.exists(music_path):
                    url = QUrl.fromLocalFile(music_path)

                    current_source = self.media_player.source().toLocalFile()

                    if music_continue and current_source == music_path and \
                       self.media_player.playbackState() == QMediaPlayer.PlayingState:
                        return

                    self.media_player.setSource(url)
                    self.audio_output.setVolume(0.5)
                    self.media_player.play()
                else:
                    print(f"Музыкальный файл не найден: {music_path}")
            else:
                if not music_continue:
                    self.media_player.stop()


    def on_view_resize(self, event):
        self.update_background_scale()
        self.update_character_scale_and_position()
        self.update_textbox_layout()
        if self.scene_list_widget and self.scene_list_widget.isVisible():
            margin = 40
            width = self.view.width() - 2 * margin
            height = self.view.height() - 160
            self.scene_list_widget.setGeometry(margin, margin, width, height)
        super(QGraphicsView, self.view).resizeEvent(event)


    def go_to_next_scene(self):
        new_scene_number = self.scene_number + 1
        new_scene_key = str(new_scene_number)

        music_continue = False
        if new_scene_key in self.scenes_data:
            music_continue = self.scenes_data[new_scene_key].get('music_continue', False)

        if self.scene_number < 15:
            min_allowed = 1
            max_allowed = new_scene_number
        else:
            min_allowed = new_scene_number - 20 + 1
            max_allowed = new_scene_number

        new_scene = StoryScene(
            new_scene_number,
            parent=self.parent(),
            media_player=self.media_player,
            audio_output=self.audio_output,
            music_continue=music_continue,
            min_allowed_scene=min_allowed,
            max_allowed_scene=max_allowed
        )

        if self.parent() is not None:
            self.parent().addWidget(new_scene)
            self.parent().setCurrentWidget(new_scene)
        else:
            new_scene.show()
            self.close()

        self.save_autosave()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.go_to_next_scene()
        elif event.key() == Qt.Key_Tab:
            if self.showing_all_scenes:
                self.restore_scene_text()
                self.showing_all_scenes = False
            else:
                self.show_all_scenes_text()
                self.showing_all_scenes = True
        else:
            super().keyPressEvent(event)


    def mousePressEvent(self, event):
        if self.arrow_item and self.arrow_item.isUnderMouse():
            self.go_to_next_scene()
        else:
            super().mousePressEvent(event)


    def eventFilter(self, obj, event):
        if obj == self.view and event.type() == QEvent.KeyPress:
           key = event.key()
           if key == Qt.Key_Space:
               self.go_to_next_scene()
               return True
           elif key == Qt.Key_Tab:
               if self.showing_all_scenes:
                   self.restore_scene_text()
                   self.showing_all_scenes = False
               else:
                   self.show_all_scenes_text()
                   self.showing_all_scenes = True
               return True
        return super().eventFilter(obj, event)


    def show_all_scenes_text(self):
        if self.scene_list_widget is None:
            self.scene_list_widget = QListWidget(self)
            self.scene_list_widget.setStyleSheet("""
                QListWidget {
                    background-color: rgba(0, 0, 0, 200);
                    color: white;
                    font-size: 18px;
                    padding: 10px;
                }
                QListWidget::item {
                    margin: 8px 0;
                    padding: 8px;
                }
                QListWidget::item:selected {
                    background-color: rgba(255, 255, 255, 50);
                }
            """)
            self.scene_list_widget.itemClicked.connect(self.on_scene_list_item_clicked)

            for key in sorted(self.scenes_data.keys(), key=lambda x: int(x)):
                scene_id = int(key)
                if self.min_allowed_scene <= scene_id <= self.max_allowed_scene:
                    text = self.scenes_data[key].get('text', '').strip()
                    item = QListWidgetItem(text)
                    item.setData(Qt.UserRole, scene_id)
                    self.scene_list_widget.addItem(item)


        # Обновляем размер и позицию при каждом показе
        margin = 40
        width = self.view.width() - 2 * margin
        height = self.view.height() - 160
        self.scene_list_widget.setGeometry(margin, margin, width, height)

        self.scene_list_widget.show()
        self.scene_list_widget.setFocusPolicy(Qt.NoFocus)
        self.setFocus()
        self.text_item.hide()
        self.text_rect_item.hide()
        if self.arrow_item:
            self.arrow_item.hide()



    def restore_scene_text(self):
        if self.scene_list_widget:
            self.scene_list_widget.hide()

        self.text_item.show()
        self.text_rect_item.show()
        if self.arrow_item:
            self.arrow_item.show()

        scene_key = str(self.scene_number)
        text = self.scenes_data.get(scene_key, {}).get('text', '')
        self.text_item.setPlainText(text)
        self.text_item.setTextWidth(self.view.viewport().width() - 80)
        self.update_textbox_layout()

        self.setFocus()


    def on_scene_list_item_clicked(self, item: QListWidgetItem):
        scene_number = item.data(Qt.UserRole)
        self.scene_list_widget.hide()
        self.showing_all_scenes = False
        self.go_to_specific_scene(scene_number)


    def go_to_specific_scene(self, scene_number):
        if not (self.min_allowed_scene <= scene_number <= self.max_allowed_scene):
            print(f"Переход на сцену {scene_number} запрещен.")
            return

        music_continue = False
        scene_key = str(scene_number)
        if scene_key in self.scenes_data:
            music_continue = self.scenes_data[scene_key].get('music_continue', False)

        new_scene = StoryScene(
            scene_number,
            parent=self.parent(),
            media_player=self.media_player,
            audio_output=self.audio_output,
            music_continue=music_continue,
            min_allowed_scene=self.min_allowed_scene,
            max_allowed_scene=self.max_allowed_scene
        )

        if self.parent() is not None:
            self.parent().addWidget(new_scene)
            self.parent().setCurrentWidget(new_scene)
        else:
            new_scene.show()
            self.close()

        self.save_autosave()


    def save_autosave(self):
        try:
            with open('.autosave', 'w', encoding='utf-8') as f:
                f.write(str(self.scene_number))
        except Exception as e:
            print(f"Ошибка при сохранении .autosave: {e}")
