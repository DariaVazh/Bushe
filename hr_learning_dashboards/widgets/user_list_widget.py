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

import numpy as np

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

    def update_ml_stats(self):
        """Обновляет статистику (вызывается по кнопке)"""
        print("🔄 Обновление ML статистики...")

        # Очищаем старые данные
        self.clear_layout(self.stats_layout)
        self.pie_series.clear()

        # Проверяем наличие кэша
        if not hasattr(self, 'user_cache') or not self.user_cache:
            # Пробуем загрузить кэш
            self.load_ml_model()

            if not self.user_cache:
                QMessageBox.warning(
                    self,
                    "Нет данных",
                    "Кэш пользователей пуст.\nСначала обновите кэш в разделе 'Рейтинг сотрудников' (кнопка 'Обновить')."
                )
                self.show_no_data_message()
                return

        try:
            # Собираем статистику
            masteries = [u['mastery'] for u in self.user_cache]

            total = len(self.user_cache)
            avg_mastery = np.mean(masteries)
            median_mastery = np.median(masteries)
            min_mastery = min(masteries)
            max_mastery = max(masteries)

            # Распределение по уровням
            levels = {
                '🔥 Отлично (>50%)': sum(1 for m in masteries if m >= 50),
                '👍 Хорошо (30-50%)': sum(1 for m in masteries if 30 <= m < 50),
                '👌 Средне (10-30%)': sum(1 for m in masteries if 10 <= m < 30),
                '🔴 Критично (<10%)': sum(1 for m in masteries if m < 10)
            }

            # Добавляем статистику (как в предыдущем коде)
            stats_data = [
                ("👥 Всего сотрудников:", f"{total} чел.", "#26394D"),
                ("📊 Среднее усвоение:", f"{avg_mastery:.1f}%", "#23588C"),
                ("📈 Медиана:", f"{median_mastery:.1f}%", "#0066CC"),
                ("📉 Минимум:", f"{min_mastery:.1f}%", "#775928"),
                ("📈 Максимум:", f"{max_mastery:.1f}%", "#26394D"),
            ]

            for label_text, value_text, color in stats_data:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)

                label = QLabel(label_text)
                label.setStyleSheet("font-size: 16px; font-weight: bold; color: #26394D;")

                value = QLabel(value_text)
                value.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
                value.setAlignment(Qt.AlignRight)

                row_layout.addWidget(label)
                row_layout.addStretch()
                row_layout.addWidget(value)

                self.stats_layout.addWidget(row)

            # Разделитель
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: #26394D; height: 1px;")
            self.stats_layout.addWidget(line)

            # Добавляем уровни и строим диаграмму
            level_colors = {
                '🔥 Отлично (>50%)': QColor(35, 88, 140),  # #23588C
                '👍 Хорошо (30-50%)': QColor(0, 102, 204),  # #0066CC
                '👌 Средне (10-30%)': QColor(119, 89, 40),  # #775928
                '🔴 Критично (<10%)': QColor(38, 57, 77)  # #26394D
            }

            for level_name, count in levels.items():
                if count > 0:
                    percentage = (count / total) * 100

                    row = QWidget()
                    row_layout = QHBoxLayout(row)
                    row_layout.setContentsMargins(0, 0, 0, 0)

                    level_label = QLabel(level_name)
                    level_label.setStyleSheet("font-size: 14px; color: #26394D;")

                    count_label = QLabel(f"{count} чел. ({percentage:.1f}%)")
                    count_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #23588C;")
                    count_label.setAlignment(Qt.AlignRight)

                    row_layout.addWidget(level_label)
                    row_layout.addStretch()
                    row_layout.addWidget(count_label)

                    self.stats_layout.addWidget(row)

                    # Добавляем сегмент в диаграмму
                    slice_ = self.pie_series.append(level_name, count)
                    slice_.setColor(level_colors[level_name])
                    slice_.setLabelVisible(True)
                    slice_.setLabelPosition(QPieSlice.LabelOutside)
                    slice_.setLabelColor(QColor(38, 57, 77))

            QMessageBox.information(self, "Успех", "Статистика успешно обновлена!")

        except Exception as e:
            print(f"Ошибка при обновлении статистики: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить статистику: {str(e)}")
            self.show_no_data_message()