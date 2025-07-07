import sys
from PySide6.QtWidgets import QApplication
from battle_scene import BattleScene

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = BattleScene()
    window.show()

    sys.exit(app.exec())
