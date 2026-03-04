# hr_auth_app/run.py
import sys
from PyQt6.QtWidgets import QApplication
from widgets.auth_window import AuthWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Загружаем стили (если есть)
    try:
        with open('styles/auth_style.qss', 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except:
        pass

    window = AuthWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()