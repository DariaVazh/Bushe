# hr_learning_dashboards/widgets/user_list_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QListWidget, QListWidgetItem,
                             QPushButton, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QSize  # или import QtCore
from PyQt5.QtChart import QChart, QPieSeries, QChartView
from PyQt5.QtGui import QPainter
from PyQt5.QtChart import QChart, QPieSeries, QChartView
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChart, QPieSeries, QChartView, QPieSlice

from Bushe.learning_platform_db.queries import AnalyticsQueries
from Bushe.learning_platform_db.database import get_db
from .user_details_dialog import UserDetailsDialog
import os
import numpy as np
import pickle

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

        title = QLabel("Рейтинг сотрудников")
        title.setStyleSheet("font-size: 30px; font-weight: bold; color: #26394D;")
        title_layout.addWidget(title)

        title_layout.addStretch()

        # Кнопка обновления
        self.refresh_btn = QPushButton("Обновить")
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
                background-color: #FFFFFE;
                border: 1px solid #34495e;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                color: #26394D;        /* ← ИСПРАВЛЕНО: текст цвета #26394D */
                padding: 8px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:selected {
                background-color: #e0e0e0;  /* чуть темнее при выделении */
                color: #26394D;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;  /* светлый при наведении */
                color: #26394D;
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
            print("🔄 Загружаю пользователей из БД...")
            db_gen = get_db()
            db = next(db_gen)

            self.users = AnalyticsQueries.get_all_users(db)
            db.close()

            print(f"✅ Загружено {len(self.users)} пользователей")

            # ПОСМОТРИМ, ЧТО В ПЕРВОМ ПОЛЬЗОВАТЕЛЕ
            if self.users:
                print("🔍 Пример данных первого пользователя:")
                for key, value in self.users[0].items():
                    print(f"   {key}: {value}")

            self.update_list()

            # СОХРАНЯЕМ КЭШ
            cache_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "ml",
                "user_cache.pkl"
            )

            print(f"💾 Сохраняю кэш в: {cache_path}")
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)

            with open(cache_path, 'wb') as f:
                pickle.dump(self.users, f)

            print(f"✅ Кэш сохранён!")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить список пользователей")

    def update_list(self):
        """Обновляет отображение списка"""
        self.list.clear()

        # Шрифт для элементов
        font = QFont()
        font.setPointSize(14)

        for i, user in enumerate(self.users, 1):
            # Формируем текст элемента
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text = f"{medal} {user['name']} | Роль: {user['role']} | Баллы: {user['score']} | Точность: {user['accuracy']}%"

            item = QListWidgetItem(text)
            item.setFont(font)
            item.setData(Qt.UserRole, user['user_id'])
            item.setSizeHint(QSize(0, 50))

            # Красим топ-3 (для них оставляем специальные цвета, для остальных #26394D)
            if i == 1:
                item.setForeground(QColor(255, 215, 0))  # золото
            elif i == 2:
                item.setForeground(QColor(192, 192, 192))  # серебро
            elif i == 3:
                item.setForeground(QColor(205, 127, 50))  # бронза
            else:
                item.setForeground(QColor(38, 57, 77))  # ← #26394D в RGB

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
