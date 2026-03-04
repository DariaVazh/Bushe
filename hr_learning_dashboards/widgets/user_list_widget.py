# hr_learning_dashboards/widgets/user_list_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QListWidget, QListWidgetItem,
                             QPushButton, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from Bushe.learning_platform_db.queries import AnalyticsQueries
from Bushe.learning_platform_db.database import get_db
from .user_details_dialog import UserDetailsDialog


class UserListWidget(QWidget):
    """Виджет со списком всех пользователей"""

    # Сигнал при выборе пользователя
    user_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.users = []  # список пользователей
        self.current_user_role = None  # роль текущего пользователя (админ/нет)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок
        title_layout = QHBoxLayout()

        title = QLabel("👥 Рейтинг сотрудников")
        title.setStyleSheet("font-size: 30px; font-weight: bold; color: #3498db;")
        title_layout.addWidget(title)

        title_layout.addStretch()

        # Кнопка обновления
        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_users)
        title_layout.addWidget(self.refresh_btn)

        layout.addLayout(title_layout)

        # Список пользователей
        self.list = QListWidget()
        self.list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                border: 1px solid #34495e;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                color: white;
                padding: 8px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:selected {
                background-color: #3498db;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
        """)
        self.list.itemDoubleClicked.connect(self.show_user_details)
        layout.addWidget(self.list)

    def set_user_role(self, role):
        """Устанавливает роль текущего пользователя"""
        self.current_user_role = role
        # Если не админ - скрываем кнопку обновления (опционально)
        if role != 'admin':
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setToolTip("Только администратор может обновлять список")

    def load_users(self):
        """Загружает список пользователей из БД"""
        try:
            db_gen = get_db()
            db = next(db_gen)

            self.users = AnalyticsQueries.get_all_users(db)
            db.close()

            self.update_list()

        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить список пользователей")

    def update_list(self):
        """Обновляет отображение списка"""
        self.list.clear()

        for i, user in enumerate(self.users, 1):
            # Формируем текст элемента
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

            text = f"{medal} {user['name']} | Роль: {user['role']} | Баллы: {user['score']} | Точность: {user['accuracy']}%"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, user['user_id'])

            # Красим топ-3
            if i == 1:
                item.setForeground(QColor(255, 215, 0))  # золото
            elif i == 2:
                item.setForeground(QColor(192, 192, 192))  # серебро
            elif i == 3:
                item.setForeground(QColor(205, 127, 50))  # бронза

            self.list.addItem(item)

    def show_user_details(self, item):
        """Показывает детальную информацию о пользователе"""
        user_id = item.data(Qt.UserRole)

        try:
            db_gen = get_db()
            db = next(db_gen)

            user_details = AnalyticsQueries.get_user_details(db, user_id)
            db.close()

            dialog = UserDetailsDialog(user_details, self)
            dialog.exec_()

        except Exception as e:
            print(f"Ошибка загрузки деталей: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить детальную информацию")