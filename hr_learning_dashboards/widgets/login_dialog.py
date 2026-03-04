# hr_learning_dashboards/widgets/login_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton,
                             QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap
import json
import os


class LoginDialog(QDialog):
    # Сигнал, который передает данные успешного входа
    login_successful = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Авторизация - HR Learning Dashboard")
        self.showMaximized()
        # Центрируем окно на экране
        self.center()

        self.setup_ui()
        self.load_styles()

    def center(self):
        """Центрирует окно на экране"""
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def setup_ui(self):
        # Главный layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Заголовок
        title = QLabel("🔐 Вход в систему")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
        """)
        layout.addWidget(title)

        # Поле для логина
        layout.addWidget(QLabel("Имя пользователя:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        layout.addWidget(self.username_input)

        # Поле для пароля
        layout.addWidget(QLabel("Пароль:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        layout.addWidget(self.password_input)

        # Кнопка входа
        self.login_btn = QPushButton("Войти")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        # Кнопка отмены
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)

        # Надпись для демо-режима
        demo_label = QLabel("Демо: admin / admin123")
        demo_label.setAlignment(Qt.AlignCenter)
        demo_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-top: 10px;")
        layout.addWidget(demo_label)

        self.setLayout(layout)

    def load_styles(self):
        """Загружает общие стили из файла, если есть"""
        style_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'dark_theme.qss')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def handle_login(self):
        """Обработка попытки входа"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя")
            return

        # Здесь можно подключить проверку из БД
        if self.check_credentials(username, password):
            user_data = {
                'username': username,
                'role': 'admin' if username == 'admin' else 'user',
                'full_name': self.get_full_name(username)
            }
            self.login_successful.emit(user_data)
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверное имя пользователя или пароль")
            self.password_input.clear()
            self.password_input.setFocus()

    def check_credentials(self, username: str, password: str) -> bool:
        """Проверка логина и пароля через БД"""
        try:
            from Bushe.learning_platform_db.database import get_db
            from Bushe.learning_platform_db.models import User
            from sqlalchemy import text

            db_gen = get_db()
            db = next(db_gen)

            # Ищем пользователя
            user = db.query(User).filter(
                User.user_name == username,
                User.user_password_cash == password  # В реальном проекте - хеши!
            ).first()

            db.close()

            if user:
                print(f"✅ Найден пользователь: {user.user_name} (роль: {user.user_role})")
                return True
            else:
                print(f"❌ Пользователь {username} не найден или неверный пароль")
                return False

        except Exception as e:
            print(f"Ошибка проверки в БД: {e}")
            # fallback на демо-режим если БД не работает
            demo_users = {'admin': 'admin123', 'user': 'user123'}
            return username in demo_users and demo_users[username] == password

    def get_full_name(self, username: str) -> str:
        """Возвращает полное имя пользователя из БД"""
        try:
            from Bushe.learning_platform_db.database import get_db
            from Bushe.learning_platform_db.models import User

            db_gen = get_db()
            db = next(db_gen)

            user = db.query(User).filter(User.user_name == username).first()
            db.close()

            if user:
                return f"{user.user_name} {user.user_surname}"
        except:
            pass

        # fallback
        names = {
            'admin': 'Администратор Системы',
            'hr_specialist': 'HR Специалист',
            'manager': 'Управляющий',
            'trainer': 'Тренер'
        }
        return names.get(username, username)

    def get_full_name(self, username: str) -> str:
        """Возвращает полное имя пользователя"""
        names = {
            'admin': 'Администратор Системы',
            'user': 'Иванов Иван',
            'manager': 'Петров Петр',
            'hr': 'Сидорова Анна'
        }
        return names.get(username, username)

    def load_users_from_json(self, filepath='users.json'):
        """Загружает пользователей из JSON файла"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}")
        return {}