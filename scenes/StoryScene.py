# This Python file uses the following encoding: utf-8

import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget,
                              QListWidgetItem, QGraphicsScene, QGraphicsView,
                              QGraphicsPixmapItem, QGraphicsTextItem)
from PySide6.QtGui import QPixmap, QColor, QFont
from PySide6.QtCore import Qt, QUrl, QEvent, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtSvgWidgets import QGraphicsSvgItem

BATTLE_SCENES = [65, 87, 106, 125, 146, 159]

class StoryScene(QWidget):
    def __init__(self, scene_number=1, parent=None, media_player=None, audio_output=None,
                 min_allowed_scene=None, max_allowed_scene=None, enemies_data=None):
        super().__init__(parent)
        self.scene_number = scene_number
        self.scenes_data = self.load_scenes_data()
        self.enemies_data = enemies_data or {}
        self.background_item = None
        self.character_item = None
        self.text_rect_item = None
        self.text_item = None
        self.arrow_item = None
        self.all_scenes_text_item = None
        self.scene_list_widget = None
        self.continue_hint_item = None
        self.showing_all_scenes = False
        self.full_text = ""
        self.current_text = ""
        self.text_timer = QTimer(self)
        self.text_timer.setInterval(30)
        self.text_timer.timeout.connect(self.type_next_character)

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

        self.play_scene_music()


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

        scene_key = str(self.scene_number)
        character_filename = self.scenes_data.get(scene_key, {}).get('character', '')

        if character_filename.startswith('character1'):
            pos_x = view_size.width() * 0.05
        else:
            pos_x = view_size.width() * 0.55

        pos_y = (view_size.height() - orig_height * scale)
        self.character_item.setPos(pos_x, pos_y)


    def add_textbox_layer(self):
        scene_key = str(self.scene_number)
        text = self.scenes_data.get(scene_key, {}).get('text', '')
        if not text:
            return

        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtGui import QBrush

        self.text_rect_item = QGraphicsRectItem()
        self.text_rect_item.setBrush(QBrush(QColor(0, 0, 0, 180)))
        self.text_rect_item.setPen(Qt.NoPen)
        self.scene.addItem(self.text_rect_item)

        self.full_text = text
        self.current_text = ""
        self.text_item = QGraphicsTextItem("")
        self.text_timer.start()
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        self.scene.addItem(self.text_item)

        arrow_path = os.path.join('assets', 'misc', 'right_arrow.svg')
        if os.path.exists(arrow_path):
            self.arrow_item = QGraphicsSvgItem(arrow_path)
            self.arrow_item.setZValue(1)
            self.scene.addItem(self.arrow_item)
        else:
            print(f"SVG стрелки не найден: {arrow_path}")

        self.continue_hint_item = QGraphicsTextItem()
        hint_text = 'Нажмите <i>пробел</i> для продолжения или <i>tab</i> для просмотра истории'
        self.continue_hint_item.setHtml(f'<span style="color: orange;">{hint_text}</span>')
        self.continue_hint_item.setZValue(2)
        self.scene.addItem(self.continue_hint_item)
        self.continue_hint_item.setVisible(False)

        self.update_textbox_layout()


    def update_textbox_layout(self):
        if self.text_rect_item is None or self.text_item is None:
            return

        view_size = self.view.viewport().size()
        margin = int(view_size.width() * 0.03)
        padding = int(view_size.width() * 0.01)

        width = view_size.width() - 2 * margin
        height = view_size.height() * 0.15
        x = margin
        y = view_size.height() - height - margin

        self.text_rect_item.setRect(x, y, width, height)

        self.text_item.setTextWidth((width - 2 * padding) * 0.90)

        base_font_size = height * 0.15
        font = QFont("Arial", int(base_font_size))
        self.text_item.setFont(font)

        self.text_item.setPos(x + padding, y + padding * 1.5)

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

        if self.continue_hint_item:
            hint_font_size = height * 0.12
            font = QFont("Arial", int(hint_font_size))
            self.continue_hint_item.setFont(font)

            hint_text_width = self.continue_hint_item.boundingRect().width()
            hint_text_height = self.continue_hint_item.boundingRect().height()

            hint_x = x + (width - hint_text_width) / 2
            hint_y = y + height - hint_text_height - padding / 2

            self.continue_hint_item.setPos(hint_x, hint_y)


    def play_scene_music(self):
        scene_key = str(self.scene_number)
        music_filename = self.scenes_data.get(scene_key, {}).get('music', None)

        if music_filename:
            music_path = os.path.abspath(os.path.join('assets', 'sounds', music_filename))
            if os.path.exists(music_path):
                music_url = QUrl.fromLocalFile(music_path)
                current_url = self.media_player.source()

                if current_url == music_url and self.media_player.playbackState() == QMediaPlayer.PlayingState:
                    return

                self.media_player.setSource(music_url)
                self.audio_output.setVolume(0.5)
                self.media_player.setLoops(QMediaPlayer.Infinite)
                self.media_player.play()
            else:
                print(f"Музыкальный файл не найден: {music_path}")
        else:
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
        # Проверяем, является ли текущая сцена боевой
        if self.scene_number in BATTLE_SCENES:
            self.start_spell_selection()
        else:
            new_scene_number = self.scene_number + 1
            self.create_new_scene(new_scene_number)

    def create_new_scene(self, new_scene_number):

        new_scene = StoryScene(
            new_scene_number,
            parent=self.parent(),
            media_player=self.media_player,
            audio_output=self.audio_output,
            min_allowed_scene=self.min_allowed_scene,
            max_allowed_scene=self.max_allowed_scene,
            enemies_data=self.enemies_data
        )

        if self.parent() is not None:
            self.parent().addWidget(new_scene)
            self.parent().setCurrentWidget(new_scene)
        else:
            new_scene.show()
            self.close()

        self.save_autosave(scene_number=new_scene_number)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.text_timer.isActive():
                self.text_timer.stop()
                self.text_item.setPlainText(self.full_text)
                if self.continue_hint_item:
                    self.continue_hint_item.setVisible(True)
            else:
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
            if self.text_timer.isActive():
                self.text_timer.stop()
                self.text_item.setPlainText(self.full_text)
                if self.continue_hint_item:
                    self.continue_hint_item.setVisible(True)
            else:
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

        margin = 40
        width = self.view.width() - 2 * margin
        height = self.view.height() - 160
        self.scene_list_widget.setGeometry(margin, margin, width, height)

        self.scene_list_widget.show()
        self.scene_list_widget.setFocusPolicy(Qt.NoFocus)

        if self.continue_hint_item:
            self.continue_hint_item.hide()

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

        if self.continue_hint_item:
            self.continue_hint_item.show()

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

        new_scene = StoryScene(
            scene_number,
            parent=self.parent(),
            media_player=self.media_player,
            audio_output=self.audio_output,
            min_allowed_scene=self.min_allowed_scene,
            max_allowed_scene=self.max_allowed_scene,
            enemies_data=self.enemies_data
        )

        if self.parent() is not None:
            self.parent().addWidget(new_scene)
            self.parent().setCurrentWidget(new_scene)
        else:
            new_scene.show()
            self.close()

        self.save_autosave(scene_number=scene_number)


    def save_autosave(self, scene_number=None):
        try:
            if scene_number is None:
                scene_number = self.scene_number
            with open('.autosave', 'w', encoding='utf-8') as f:
                f.write(str(scene_number))
        except Exception as e:
            print(f"Ошибка при сохранении .autosave: {e}")


    def type_next_character(self):
        if len(self.current_text) < len(self.full_text):
            self.current_text += self.full_text[len(self.current_text)]
            self.text_item.setPlainText(self.current_text)
        else:
            self.text_timer.stop()
            if self.continue_hint_item:
                self.continue_hint_item.setVisible(True)


    def start_spell_selection(self):
        # Определяем номер врага на основе номера сцены
        battle_index = BATTLE_SCENES.index(self.scene_number)
        enemy_id = str(battle_index + 1)
        enemy_data = self.enemies_data.get(enemy_id, {})

        # Создаем виджет выбора заклинаний
        spell_selection_widget = StaticBattleWidget(
            enemy_data=enemy_data,
            parent=self.parent()
        )

        # Подключаем обработчик завершения выбора
        spell_selection_widget.battleReady.connect(
            lambda spells: self.start_battle(spells, enemy_data)
        )

        # Добавляем в стек и переключаемся
        if self.parent() is not None:
            self.parent().addWidget(spell_selection_widget)
            self.parent().setCurrentWidget(spell_selection_widget)

    def start_battle(self, selected_spells, enemy_data):
        # Создаем окно боя
        battle_window = BattleWindow(
            scene_number=self.scene_number,
            player_spells=selected_spells,
            enemy_data=enemy_data
        )

        # Подключаем обработчик завершения боя
        battle_window.battle_finished.connect(self.handle_battle_result)

        # Добавляем в стек и переключаемся
        if self.parent() is not None:
            self.parent().addWidget(battle_window)
            self.parent().setCurrentWidget(battle_window)

    def handle_battle_result(self, victory):
        # Определяем следующую сцену
        if victory:
            next_scene = self.scene_number + 1
        else:
            next_scene = max(1, self.scene_number - 5)

        # Создаем новую сцену истории
        new_scene = StoryScene(
            next_scene,
            parent=self.parent(),
            media_player=self.media_player,
            audio_output=self.audio_output,
            min_allowed_scene=self.min_allowed_scene,
            max_allowed_scene=self.max_allowed_scene,
            enemies_data=self.enemies_data
        )

        # Показываем новую сцену
        if self.parent() is not None:
            self.parent().addWidget(new_scene)
            self.parent().setCurrentWidget(new_scene)
        else:
            new_scene.show()

        # Сохраняем автосейв
        self.save_autosave(next_scene)
