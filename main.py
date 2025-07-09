"""
main_static.py – запускает статичную сцену (StaticScene).
"""

import sys
from PySide6.QtWidgets import QApplication
from static_scene import StaticScene


def main() -> None:
    app = QApplication(sys.argv)
    win = StaticScene()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
