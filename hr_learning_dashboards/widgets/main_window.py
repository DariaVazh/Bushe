# hr_learning_dashboards/widgets/main_window.py
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox,
                             QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

# Импортируем из пакета learning_platform_db
from Bushe.learning_platform_db.database import get_db
from Bushe.learning_platform_db.queries import AnalyticsQueries

from .learning_curve_chart import LearningCurveChart
from sqlalchemy import text


class MainWindow(QMainWindow):
    # ... весь код класса без изменений ...
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HR Learning Dashboard")
        self.setGeometry(100, 100, 1400, 900)

        central = QWidget()
        self.setCentralWidget(central)

        self.layout = QVBoxLayout(central)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self.create_top_panel()
        self.create_charts()

        self.load_users()

    def create_top_panel(self):
        panel = QWidget()
        panel_layout = QHBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("📊 Аналитика обучения")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        panel_layout.addWidget(title)

        panel_layout.addStretch()

        panel_layout.addWidget(QLabel("Сотрудник:"))
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(200)
        self.user_combo.currentIndexChanged.connect(self.on_user_changed)
        panel_layout.addWidget(self.user_combo)

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.refresh_data)
        panel_layout.addWidget(self.refresh_btn)

        self.layout.addWidget(panel)

    def create_charts(self):
        self.chart = LearningCurveChart()
        self.layout.addWidget(self.chart)

    def load_users(self):
        try:
            db_gen = get_db()
            db = next(db_gen)

            result = db.execute(
                text("SELECT user_id FROM users ORDER BY user_id LIMIT 20")
            )
            users = [str(row[0]) for row in result]

            self.user_combo.clear()
            self.user_combo.addItems(users)

            db.close()

            if users:
                self.load_user_data(int(users[0]))

        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}")
            self.user_combo.addItems(["1", "2", "3", "4", "5"])

    def load_user_data(self, user_id: int):
        try:
            db_gen = get_db()
            db = next(db_gen)

            df = AnalyticsQueries.get_user_learning_curve(db, user_id)
            self.chart.update_chart(df, user_id)

            db.close()

        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def on_user_changed(self, index):
        if index >= 0:
            user_id = int(self.user_combo.currentText())
            self.load_user_data(user_id)

    def refresh_data(self):
        if self.user_combo.count() > 0:
            user_id = int(self.user_combo.currentText())
            self.load_user_data(user_id)