# hr_learning_dashboards/run.py
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont

from widgets.login_dialog import LoginDialog
from widgets.main_window import MainWindow


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')

        # Загружаем стили
        try:
            with open('styles/dark_theme.qss', 'r', encoding='utf-8') as f:
                self.app.setStyleSheet(f.read())
        except:
            pass  # Если нет стилей - не страшно

    def run(self):
        # Показываем окно авторизации
        login_dialog = LoginDialog()

        # Подключаем сигнал успешного входа
        login_dialog.login_successful.connect(self.start_main_window)

        # Если пользователь нажал "Отмена" или закрыл окно - выходим
        if login_dialog.exec_() != LoginDialog.Accepted:
            return

        sys.exit(self.app.exec_())

    def start_main_window(self, user_data):
        """Запускает главное окно после успешного входа"""
        self.main_window = MainWindow(user_data)
        self.main_window.show()


if __name__ == "__main__":
    app = App()
    app.run()