import sys
import os
import json
from PySide6.QtWidgets import QApplication, QStackedWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from scenes.StoryScene import StoryScene
from MainMenu import MainMenu
from PySide6.QtCore import QUrl  # ← Добавьте этот импорт

def load_autosave():
    try:
        if os.path.exists('.autosave'):
            with open('.autosave', 'r', encoding='utf-8') as f:
                scene_number = int(f.read().strip())
                return scene_number
    except Exception as e:
        print(f"Ошибка при загрузке .autosave: {e}")
    return 1

def load_enemies_data():
    try:
        with open('assets/characters/enemies.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при загрузке enemies.json: {e}")
        return {}
    
class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Achromatopsia")
        self.setWindowIcon(QIcon("assets/icon.png"))
        self.enemies_data = load_enemies_data()
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.main_menu = MainMenu(self)
        self.addWidget(self.main_menu)
        self.setCurrentWidget(self.main_menu)
        
        # Запускаем в оконном режиме с рамкой
        self.resize(1280, 720)
        self.show()
        
        # Центрируем окно
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            # Переключение между полноэкранным и оконным режимом
            if self.isFullScreen():
                self.showNormal()  # Возврат в оконный режим
            else:
                self.showFullScreen()  # Полноэкранный режим
                
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()  # В полноэкранном режиме - выход в оконный
            else:
                # В оконном режиме - возврат в главное меню
                self.return_to_main_menu()
                
        super().keyPressEvent(event)

    def return_to_main_menu(self):
        """Возврат в главное меню"""
        current_widget = self.currentWidget()
        
        if current_widget == self.main_menu:
            QApplication.instance().quit()
            return
            
        # Останавливаем музыку текущей сцены
        if hasattr(current_widget, 'media_player'):
            current_widget.media_player.stop()
            
        # Очищаем текущий виджет
        if hasattr(current_widget, 'cleanup'):
            current_widget.cleanup()
            
        # Удаляем текущий виджет из стека
        self.removeWidget(current_widget)
        current_widget.deleteLater()
        
        # Возвращаемся в главное меню
        self.setCurrentWidget(self.main_menu)
        
        # ВОТ ИСПРАВЛЕНИЕ - перезапускаем музыку меню правильно
        if hasattr(self.main_menu, 'media_player'):
            # Останавливаем предыдущую музыку если играла
            self.main_menu.media_player.stop()
            # Перезагружаем и запускаем музыку меню
            music_path = os.path.abspath("assets/sounds/menu_music.mp3")
            if os.path.exists(music_path):
                self.main_menu.media_player.setSource(QUrl.fromLocalFile(music_path))
                self.main_menu.media_player.setLoops(QMediaPlayer.Infinite)
                self.main_menu.media_player.play()

    def show_story_scene(self, scene_number=None):
        """Показ сцены истории с автозагрузкой из .autosave"""
        if scene_number is None:
            scene_number = load_autosave()
        
        initial_scene = StoryScene(
            scene_number=scene_number, 
            parent=self, 
            enemies_data=self.enemies_data,
            media_player=self.media_player,
            audio_output=self.audio_output 
        )
        self.addWidget(initial_scene)
        self.setCurrentWidget(initial_scene)

def cleanup(self):
    """Полная очистка ресурсов перед возвратом в меню"""
    # Останавливаем музыку
    if hasattr(self, 'media_player') and self.media_player:
        self.media_player.stop()
        self.media_player.setSource(QUrl())  # Очищаем источник
    
    # Останавливаем таймер
    if hasattr(self, 'text_timer') and self.text_timer:
        if self.text_timer.isActive():
            self.text_timer.stop()
        self.text_timer.deleteLater()
        self.text_timer = None
    
    # Очищаем графическую сцену
    if hasattr(self, 'scene') and self.scene:
        self.scene.clear()
        self.scene.deleteLater()
        self.scene = None
    
    # Очищаем view
    if hasattr(self, 'view') and self.view:
        self.view.deleteLater()
        self.view = None
    
    # Удаляем все графические элементы
    self.background_item = None
    self.character_item = None
    self.text_rect_item = None
    self.text_item = None
    self.arrow_item = None
    self.all_scenes_text_item = None
    self.scene_list_widget = None
    self.continue_hint_item = None
    
    print("StoryScene resources completely cleaned up")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())