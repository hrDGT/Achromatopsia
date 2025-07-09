"""
Точка входа: QApplication + BattleWindow.
"""
import sys

from PySide6.QtWidgets import QApplication

from battle_controller import BattleWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = BattleWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
