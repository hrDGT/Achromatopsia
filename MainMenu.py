# MainMenu.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QGraphicsScene, 
                              QGraphicsView, QGraphicsPixmapItem, QApplication, QSizePolicy,
                              QLabel, QSlider)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QBrush, QColor
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl
# В MainMenu.py добавляем новый импорт
from static_scene import StaticBattleWidget

class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.drag_position = None

    def init_ui(self):
        # Основные настройки окна
        self.setFixedSize(int(self.parent.width() * 0.6),
                         int(self.parent.height() * 0.8))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Главный контейнер с фоновым изображением
        self.background = QLabel(self)
        self.background.setGeometry(0, 0, self.width(), self.height())
        
        # Загрузка фонового изображения
        bg_path = "assets/gui/settings_background.png"
        if os.path.exists(bg_path):
            pixmap = QPixmap(bg_path)
            if not pixmap.isNull():
                # Масштабируем изображение под размер окна
                pixmap = pixmap.scaled(self.size(), Qt.IgnoreAspectRatio, 
                                     Qt.SmoothTransformation)
                self.background.setPixmap(pixmap)
            else:
                print("Не удалось загрузить фоновое изображение настроек")
        else:
            print(f"Файл фона не найден: {bg_path}")
            # Fallback - используем цветной фон
            self.background.setStyleSheet("""
                QLabel {
                    background-color: rgba(50, 50, 70, 0);
                }
            """)

        # Основной layout для элементов управления
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        # Заголовок настроек
        self.title_label = QLabel("Настройки", self)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                padding-bottom: 15px;
            }
        """)
        self.main_layout.addWidget(self.title_label, 0, Qt.AlignHCenter)

        # Группа настроек звука
        sound_group = QWidget()
        sound_group.setStyleSheet("""
            background-color: rgba(70, 70, 90, 150); 
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,30);
        """)
        sound_layout = QVBoxLayout(sound_group)
        sound_layout.setContentsMargins(20, 20, 20, 20)
        
        # Настройка громкости
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
        
        sound_layout.addWidget(QLabel("<font color='white'>Громкость музыки:</font>"))
        sound_layout.addWidget(self.volume_slider)
        self.main_layout.addWidget(sound_group)

        # Кнопка закрытия
        self.close_button = QPushButton("Закрыть", self)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(90, 90, 120, 180);
                color: white;
                border: 1px solid rgba(255,255,255,50);
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 16px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: rgba(110, 110, 140, 200);
            }
        """)
        self.close_button.clicked.connect(self.close)
        self.main_layout.addWidget(self.close_button, 0, Qt.AlignHCenter)
        self.main_layout.addStretch()

    def resizeEvent(self, event):
        # Обновляем размер фонового изображения при изменении окна
        if hasattr(self, 'background') and self.background.pixmap():
            pixmap = self.background.pixmap()
            pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, 
                                 Qt.SmoothTransformation)
            self.background.setPixmap(pixmap)
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


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
        
        # Центрирование иконки
        if not self.icon().isNull():
            icon_size = self.iconSize()
            x = (self.width() - icon_size.width()) / 2
            y = (self.height() - icon_size.height()) / 2
            self.icon().paint(painter, int(x), int(y), icon_size.width(), icon_size.height())

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.init_ui()
        
    def show_settings_window(self):
        """Показывает окно настроек"""
        self.settings_window = SettingsWindow(self)
        self.settings_window.setWindowFlags(Qt.FramelessWindowHint)
        self.settings_window.move(
            int(self.width() * 0.2),  # Центрирование по горизонтали
            int(self.height() * 0.1)   # Отступ сверху 10%
        )
        self.settings_window.show()

    def init_ui(self):
        # Настройка медиаплеера
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)
        
        # Загрузка и воспроизведение музыки
        music_path = os.path.abspath("assets/sounds/menu_music.mp3")
        if os.path.exists(music_path):
            self.media_player.setSource(QUrl.fromLocalFile(music_path))
            self.media_player.setLoops(QMediaPlayer.Infinite)
            self.media_player.play()
        else:
            print(f"Файл музыки не найден: {music_path}")

        # Графическая сцена для фона
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Загрузка фонового изображения
        self.background_item = QGraphicsPixmapItem()
        pixmap = QPixmap("assets/backgrounds/main_menu.png")
        if not pixmap.isNull():
            self.background_item.setPixmap(pixmap)
            self.scene.addItem(self.background_item)
        
        # Основной макет
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        # Контейнер для кнопок
        self.button_container = QWidget(self)
        button_layout = QVBoxLayout(self.button_container)
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setSpacing(10)  # Уменьшенное расстояние между кнопками
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Размеры кнопок (в процентах от ширины экрана)
        button_width_percent = 0.20  # 20% ширины экрана
        button_height_percent = 0.10  # 10% высоты экрана

        # Кнопка Play
        self.play_button = RoundedButton(self.button_container)
        self.play_button.setIcon(QIcon("assets/gui/play.png"))
        self.play_button.setIconSize(QSize(200, 80))
        self.play_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.clicked.connect(self.start_game)
        button_layout.addWidget(self.play_button, stretch=1, alignment=Qt.AlignCenter)

        # Кнопка Settings
        self.settings_button = RoundedButton(self.button_container)
        self.settings_button.setIcon(QIcon("assets/gui/settings.png"))
        self.settings_button.setIconSize(QSize(200, 80))
        self.settings_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self.show_settings_window)
        button_layout.addWidget(self.settings_button, stretch=1, alignment=Qt.AlignCenter)

        # Кнопка Exit
        self.exit_button = RoundedButton(self.button_container)
        self.exit_button.setIcon(QIcon("assets/gui/exit.png"))
        self.exit_button.setIconSize(QSize(200, 80))
        self.exit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.exit_button.setCursor(Qt.PointingHandCursor)
        self.exit_button.clicked.connect(self.exit_game)
        button_layout.addWidget(self.exit_button, stretch=1, alignment=Qt.AlignCenter)

        # Размещаем контейнер с кнопками поверх фона
        self.button_container.setGeometry(0, 0, self.width(), self.height())
        self.button_container.setStyleSheet("background: transparent;")
    # Первоначальное позиционирование контейнера с отступами
        self.update_button_container_geometry()

    def update_button_container_geometry(self):
        """Обновляет геометрию контейнера с отступами 20% сверху и снизу"""
        top_margin = int(self.height() * 0.30)    # 20% сверху
        bottom_margin = int(self.height() * 0.30) # 20% снизу
        container_height = self.height() - top_margin - bottom_margin
        
        self.button_container.setGeometry(
            0,                                  # X позиция
            top_margin,                         # Y позиция (отступ сверху)
            self.width(),                       # Ширина
            max(100, container_height)          # Высота (не менее 100px)
        )

    def resizeEvent(self, event):
        # Масштабируем фон
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
        
        # Обновляем размеры кнопок
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
        
        # Обновляем положение контейнера с новыми отступами
        self.update_button_container_geometry()
        
        super().resizeEvent(event)

    def start_game(self):
        if self.parent:
            self.media_player.stop()
            self.parent.show_story_scene(1)

    def exit_game(self):
        self.media_player.stop()
        QApplication.instance().quit()

        