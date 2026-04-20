# hr_learning_dashboards/run.py
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont

from widgets.login_dialog import LoginDialog
from widgets.main_window import MainWindow
# hr_learning_dashboards/run.py
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from widgets.login_dialog import LoginDialog
from widgets.main_window import MainWindow


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        self.main_window = None

        try:
            with open('styles/dark_theme.qss', 'r', encoding='utf-8') as f:
                self.app.setStyleSheet(f.read())
        except:
            pass

    def run(self):
        login_dialog = LoginDialog()

        login_dialog.login_successful.connect(self.start_main_window)

        result = login_dialog.exec_()

        if result != LoginDialog.Accepted:
            return

        sys.exit(self.app.exec_())

    def start_main_window(self, user_data):
        print(f"Запуск главного окна для {user_data['full_name']}")

        self.main_window = MainWindow(user_data)
        self.main_window.showMaximized()


if __name__ == "__main__":
    app = App()
    app.run()
