# This Python file uses the following encoding: utf-8

import sys
import os
from PySide6.QtWidgets import QApplication, QStackedWidget
from scenes.StoryScene import StoryScene
from PySide6.QtGui import QIcon

def load_autosave():
    try:
        if os.path.exists('.autosave'):
            with open('.autosave', 'r', encoding='utf-8') as f:
                scene_number = int(f.read().strip())
                return scene_number
    except Exception as e:
        print(f"Ошибка при загрузке .autosave: {e}")
    return 1

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QStackedWidget()
    start_scene_number = load_autosave()
    initial_scene = StoryScene(scene_number=start_scene_number)
    window.addWidget(initial_scene)
    window.setMinimumSize(800, 600)
    window.setWindowTitle("Achromatopsia")
    window.setWindowIcon(QIcon("assets/icon.png"))
    window.show()

    sys.exit(app.exec())
