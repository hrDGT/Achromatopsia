
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QGraphicsScene, 
                              QGraphicsView, QGraphicsPixmapItem, QApplication, QSizePolicy,
                              QLabel, QSlider)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QBrush, QColor
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl
from static_scene import StaticBattleWidget


class RoundedButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.icon().isNull():
            icon_size = self.iconSize()
            x = (self.width() - icon_size.width()) / 2
            y = (self.height() - icon_size.height()) / 2
            self.icon().paint(painter, int(x), int(y), icon_size.width(), icon_size.height())

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Используем медиаплеер из родителя
        if parent and hasattr(parent, 'media_player'):
            self.media_player = parent.media_player
            self.audio_output = parent.audio_output
        else:
            # Создаем новые только если родитель не предоставил
            self.audio_output = QAudioOutput()
            self.media_player = QMediaPlayer()
            self.media_player.setAudioOutput(self.audio_output)
            
        self.init_ui()
        
    def show_settings_window(self):
        self.settings_window = SettingsWindow(self)
        self.settings_window.setWindowFlags(Qt.FramelessWindowHint)
        self.settings_window.move(
            int(self.width() * 0.2), 
            int(self.height() * 0.1)   
        )
        self.settings_window.show()

    def init_ui(self):

        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)
        self.media_player.stop()
        music_path = os.path.abspath("assets/sounds/menu_music.mp3")
        if os.path.exists(music_path):
            self.media_player.setSource(QUrl.fromLocalFile(music_path))
            self.media_player.setLoops(QMediaPlayer.Infinite)
            self.media_player.play()
        else:
            print(f"Файл музыки не найден: {music_path}")

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.background_item = QGraphicsPixmapItem()
        pixmap = QPixmap("assets/backgrounds/main_menu.png")
        if not pixmap.isNull():
            self.background_item.setPixmap(pixmap)
            self.scene.addItem(self.background_item)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.button_container = QWidget(self)
        button_layout = QVBoxLayout(self.button_container)
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setSpacing(10)  
        button_layout.setContentsMargins(0, 0, 0, 0)

        button_width_percent = 0.20  
        button_height_percent = 0.10  

        self.play_button = RoundedButton(self.button_container)
        self.play_button.setIcon(QIcon("assets/gui/play.png"))
        self.play_button.setIconSize(QSize(200, 80))
        self.play_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.clicked.connect(self.start_game)
        button_layout.addWidget(self.play_button, stretch=1, alignment=Qt.AlignCenter)

        self.settings_button = RoundedButton(self.button_container)
        self.settings_button.setIcon(QIcon("assets/gui/settings.png"))
        self.settings_button.setIconSize(QSize(200, 80))
        self.settings_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self.show_settings_window)
        button_layout.addWidget(self.settings_button, stretch=1, alignment=Qt.AlignCenter)

        self.exit_button = RoundedButton(self.button_container)
        self.exit_button.setIcon(QIcon("assets/gui/exit.png"))
        self.exit_button.setIconSize(QSize(200, 80))
        self.exit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.exit_button.setCursor(Qt.PointingHandCursor)
        self.exit_button.clicked.connect(self.exit_game)
        button_layout.addWidget(self.exit_button, stretch=1, alignment=Qt.AlignCenter)

       
        self.button_container.setGeometry(0, 0, self.width(), self.height())
        self.button_container.setStyleSheet("background: transparent;")
    
        self.update_button_container_geometry()

    def update_button_container_geometry(self):
        """Обновляет геометрию контейнера с отступами 20% сверху и снизу"""
        top_margin = int(self.height() * 0.30)    
        bottom_margin = int(self.height() * 0.30) 
        container_height = self.height() - top_margin - bottom_margin
        
        self.button_container.setGeometry(
            0,                                  
            top_margin,                         
            self.width(),                       
            max(100, container_height)          
        )

    def resizeEvent(self, event):
        if hasattr(self, 'background_item') and self.background_item.pixmap():
            view_size = self.view.size()
            pixmap = self.background_item.pixmap()
            
            scale_x = view_size.width() / pixmap.width()
            scale_y = view_size.height() / pixmap.height()
            
            from PySide6.QtGui import QTransform
            transform = QTransform()
            transform.scale(scale_x, scale_y)
            self.background_item.setTransform(transform)
            
            self.scene.setSceneRect(0, 0, view_size.width(), view_size.height())
        
        button_width = int(self.width() * 0.20)
        button_height = int(self.height() * 0.10)
        
        if hasattr(self, 'play_button'):
            icon_size = QSize(min(200, button_width), min(80, button_height))
            self.play_button.setIconSize(icon_size)
            self.play_button.setMinimumSize(button_width, button_height)
            self.play_button.setMaximumSize(button_width, button_height)
            
        if hasattr(self, 'settings_button'):
            icon_size = QSize(min(200, button_width), min(80, button_height))
            self.settings_button.setIconSize(icon_size)
            self.settings_button.setMinimumSize(button_width, button_height)
            self.settings_button.setMaximumSize(button_width, button_height)
            
        if hasattr(self, 'exit_button'):
            icon_size = QSize(min(200, button_width), min(80, button_height))
            self.exit_button.setIconSize(icon_size)
            self.exit_button.setMinimumSize(button_width, button_height)
            self.exit_button.setMaximumSize(button_width, button_height)
        
        self.update_button_container_geometry()
        
        super().resizeEvent(event)

        if hasattr(self, 'settings_window') and self.settings_window.isVisible():
            self.settings_window.parent_resize_event()

    def start_game(self):
        if self.parent:
            self.media_player.stop()
            self.parent.show_story_scene(1)

    def exit_game(self):
        self.media_player.stop()
        QApplication.instance().quit()

class Window(QWidget):
    """Базовое масштабируемое окно с фоновым изображением и кнопкой выхода"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.drag_position = None
        self.init_ui()
        
        self.width_percent = 0.6
        self.height_percent = 0.8
        
        self.update_size()

    def init_ui(self):

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.background = QLabel(self)
        self.update_background()

        self.exit_button = RoundedButton(self)
        self.exit_button.setIcon(QIcon("assets/gui/exit.png"))
        self.exit_button.setCursor(Qt.PointingHandCursor)
        self.exit_button.clicked.connect(self.close)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)
        self.main_layout.addStretch()
        
        self.main_layout.addWidget(self.exit_button, 0, Qt.AlignHCenter | Qt.AlignBottom)

    def update_size(self):
        """Обновляет размеры окна в процентах от родительского"""
        if self.parent:
            width = int(self.parent.width() * self.width_percent)
            height = int(self.parent.height() * self.height_percent)
            self.setFixedSize(width, height)
            self.move(
                int(self.parent.width() * (1 - self.width_percent) / 2),
                int(self.parent.height() * (1 - self.height_percent) / 2)
            )
            self.update_background()
            self.update_button_size()

    def update_button_size(self):
        """Обновляет размер кнопки в зависимости от размера окна"""
        btn_width = int(self.width() * 0.25) 
        btn_height = int(btn_width * 0.4)     
        self.exit_button.setIconSize(QSize(btn_width, btn_height))
        self.exit_button.setFixedSize(btn_width, btn_height)

    def update_background(self):
        """Обновляет фоновое изображение"""
        bg_path = "assets/gui/settings_background.png"
        if os.path.exists(bg_path):
            pixmap = QPixmap(bg_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                self.background.setPixmap(pixmap)
                self.background.setGeometry(0, 0, self.width(), self.height())
            else:
                print("Не удалось загрузить фоновое изображение настроек")
        else:
            print(f"Файл фона не найден: {bg_path}")
            self.background.setStyleSheet("background-color: rgba(50, 50, 70, 200);")

    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        self.update_background()
        self.update_button_size()
        super().resizeEvent(event)

    def parent_resize_event(self):
        """Вызывается при изменении размера родительского окна"""
        self.update_size()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


from PySide6.QtGui import QFont

class SettingsWindow(Window):
    """Масштабируемое окно настроек с ползунком громкости"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_settings_ui()

    def init_settings_ui(self):
        self.title_label = QLabel("Settings", self)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                padding-bottom: 15px;
            }
        """)
        self.main_layout.insertWidget(0, self.title_label, 0, Qt.AlignHCenter)

        sound_group = QWidget()
        sound_group.setStyleSheet("""
            background-color: rgba(70, 70, 90, 0); 
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0);
        """)
        sound_layout = QVBoxLayout(sound_group)
        sound_layout.setContentsMargins(20, 20, 20, 20)
        
        music_label = QLabel("Music:")
        music_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 20px;
                font-weight: bold;
                padding-bottom: 10px;
            }
        """)
        sound_layout.addWidget(music_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.parent.audio_output.volume() * 100))
        self.volume_slider.setStyleSheet("""
            QSlider {
                height: 30px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: rgba(100,100,120,150);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 20px;
                margin: -7px 0;
                border-radius: 10px;
                background: white;
                border: 1px solid #aaa;
            }
        """)
        
        self.volume_slider.valueChanged.connect(self.change_volume)
        sound_layout.addWidget(self.volume_slider)
        self.main_layout.insertWidget(1, sound_group)

    def change_volume(self, value):
        """Изменяет громкость аудио"""
        volume = value / 100.0
        self.parent.audio_output.setVolume(volume)

    def showEvent(self, event):
        """Обновляем размеры при показе окна"""
        self.update_size()
        super().showEvent(event)

        
