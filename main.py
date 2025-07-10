# This Python file uses the following encoding: utf-8

import sys
import os
import json
from PySide6.QtWidgets import QApplication, QStackedWidget
from scenes.StoryScene import StoryScene
from PySide6.QtGui import QIcon
from MainMenu import MainMenu

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
        self.setMinimumSize(800, 600)
        self.setWindowTitle("Achromatopsia")
        self.setWindowIcon(QIcon("assets/icon.png"))
        
        # Создаем меню и сцену
        self.main_menu = MainMenu(self)
        self.addWidget(self.main_menu)
        
        # Показываем главное меню
        self.setCurrentWidget(self.main_menu)
        self.show()

    def show_story_scene(self, scene_number):
        # Создаем новую сцену или переключаемся на существующую
        initial_scene = StoryScene(scene_number=scene_number, parent=self)
        self.addWidget(initial_scene)
        self.setCurrentWidget(initial_scene)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     window = QStackedWidget()
#     start_scene_number = load_autosave()
#     enemies_data = load_enemies_data()
#     initial_scene = StoryScene(scene_number=start_scene_number, enemies_data=enemies_data)
#     window.addWidget(initial_scene)
#     window.setMinimumSize(800, 600)
#     window.setWindowTitle("Achromatopsia")
#     window.setWindowIcon(QIcon("assets/icon.png"))
#     window.show()

#     sys.exit(app.exec())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
