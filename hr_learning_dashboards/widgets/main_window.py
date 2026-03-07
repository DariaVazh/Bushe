# hr_learning_dashboards/widgets/main_window.py
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel,
                             QStackedWidget, QFrame, QMessageBox, QComboBox, QScrollArea)
from PyQt5.QtCore import Qt
from sqlalchemy import text
from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout
from .user_list_widget import UserListWidget
from Bushe.learning_platform_db.database import get_db
from Bushe.learning_platform_db.queries import AnalyticsQueries

from .learning_curve_chart import LearningCurveChart

import pickle
import numpy as np
from PyQt5.QtChart import QChart, QPieSeries, QChartView, QPieSlice
from PyQt5.QtGui import QPainter, QColor


class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()

        self.user_data = user_data or {'username': 'Гость', 'role': 'guest', 'full_name': 'Гость'}

        self.setWindowTitle(f"HR Learning Dashboard - {self.user_data['full_name']}")
        self.showMaximized()

        # Статус бар
        self.statusBar().showMessage(f"Пользователь: {self.user_data['full_name']} | Роль: {self.user_data['role']}")

        # ===== СОЗДАЁМ ЦЕНТРАЛЬНЫЙ ВИДЖЕТ =====
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # ===== ГЛАВНЫЙ ГОРИЗОНТАЛЬНЫЙ LAYOUT =====
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== ЛЕВАЯ ПАНЕЛЬ (МЕНЮ) =====
        self.menu_panel = QFrame()
        self.menu_panel.setFixedWidth(350)
        self.menu_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFEF;
                border: none;
            }
        """)

        # Layout для меню
        menu_layout = QVBoxLayout(self.menu_panel)
        menu_layout.setContentsMargins(10, 20, 10, 20)
        menu_layout.setSpacing(10)

        # Заголовок меню
        menu_title = QLabel(f"{self.user_data['full_name']}")
        menu_title.setStyleSheet("color: #26394D; font-size: 22px; font-weight: bold; padding: 10px;")
        menu_title.setAlignment(Qt.AlignCenter)
        menu_layout.addWidget(menu_title)

        # Роль пользователя
        role_label = QLabel(f"[{self.user_data['role']}]")
        role_label.setStyleSheet("color: #26394D; font-size: 14px;")
        role_label.setAlignment(Qt.AlignCenter)
        menu_layout.addWidget(role_label)

        # Линия-разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #775928;")
        menu_layout.addWidget(line)

        # Кнопки меню
        self.btn_page1 = self.create_menu_button("Кривая обучения")
        self.btn_page2 = self.create_menu_button("Рейтинг сотрудников")
        self.btn_page3 = self.create_menu_button("ML Аналитика")

        menu_layout.addWidget(self.btn_page1)
        menu_layout.addWidget(self.btn_page2)
        menu_layout.addWidget(self.btn_page3)

        # Кнопка выхода
        menu_layout.addStretch()

        self.btn_logout = QPushButton("Выйти")
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #23588C;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_logout.clicked.connect(self.logout)
        menu_layout.addWidget(self.btn_logout)

        # ===== ПРАВАЯ ПАНЕЛЬ (СТРАНИЦЫ) =====
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: #FFFFEF;
            }
        """)

        # Создаём страницы
        self.create_pages()

        # Добавляем страницы в стек
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)

        # ===== ДОБАВЛЯЕМ ПАНЕЛИ В ГЛАВНЫЙ LAYOUT =====
        main_layout.addWidget(self.menu_panel)
        main_layout.addWidget(self.stacked_widget, 1)

        # ===== ПОДКЛЮЧАЕМ КНОПКИ =====
        self.btn_page1.clicked.connect(lambda: self.switch_page(0))
        self.btn_page2.clicked.connect(lambda: self.switch_page(1))
        self.btn_page3.clicked.connect(lambda: self.switch_page(2))

        # Показываем первую страницу
        self.switch_page(0)

    def create_menu_button(self, text):
        """Создаёт стилизованную кнопку для меню"""
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #23588C;
                color: #FFFFFE;
                border: none;
                padding: 12px;
                font-size: 22px;
                text-align: left;
                border-radius: 5px;
                height: 150px;
            }
            QPushButton:hover {
                background-color: #3d566e;
            }
        """)
        return btn

    def create_pages(self):
        """Создаёт страницы с контентом"""

        # Страница 1: Кривая обучения
        self.page1 = QWidget()
        layout1 = QVBoxLayout(self.page1)
        layout1.setContentsMargins(20, 20, 20, 20)

        # Заголовок страницы
        title1 = QLabel("Кривая обучения")
        title1.setStyleSheet("font-size: 24px; font-weight: bold; color: #26394D;")
        layout1.addWidget(title1)

        # График
        self.chart = LearningCurveChart()
        layout1.addWidget(self.chart)

        # Страница 2: Рейтинг сотрудников
        self.page2 = QWidget()
        layout2 = QVBoxLayout(self.page2)
        layout2.setContentsMargins(20, 20, 20, 20)

        # Виджет рейтинга
        self.user_list = UserListWidget()
        self.user_list.set_user_role(self.user_data['role'])
        self.user_list.load_users()
        layout2.addWidget(self.user_list)

        # Страница 3: ML Аналитика
        self.page3 = QWidget()
        # Используем QVBoxLayout для всей страницы
        page3_layout = QVBoxLayout(self.page3)
        page3_layout.setContentsMargins(0, 0, 0, 0)
        page3_layout.setSpacing(0)

        # Создаём скролл-область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FFFFFE;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #23588C;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #0066CC;
            }
        """)

        # Создаём контейнер для всего контента
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # === ВЕРХНЯЯ ЧАСТЬ (статистика и диаграмма) ===
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)

        # Левая панель (текст)
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFE;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)

        title3 = QLabel("ML Аналитика")
        title3.setStyleSheet("font-size: 24px; font-weight: bold; color: #26394D;")
        left_layout.addWidget(title3)

        # Кнопка загрузки
        self.load_ml_btn = QPushButton("📥 Загрузить ML данные")
        self.load_ml_btn.setStyleSheet("""
            QPushButton {
                background-color: #23588C;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                margin: 10px 0;
            }
            QPushButton:hover {
                background-color: #0066CC;
            }
        """)
        self.load_ml_btn.clicked.connect(self.load_ml_data_for_page)
        left_layout.addWidget(self.load_ml_btn)

        # Контейнер для статистики
        self.stats_container = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_container)
        left_layout.addWidget(self.stats_container)
        left_layout.addStretch()

        # Правая панель (диаграмма)
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFE;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)

        chart_title = QLabel("Распределение сотрудников")
        chart_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #26394D;")
        right_layout.addWidget(chart_title)

        # Диаграмма
        self.pie_chart = QChart()
        self.pie_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.pie_series = QPieSeries()
        self.pie_chart.addSeries(self.pie_series)

        chart_view = QChartView(self.pie_chart)
        chart_view.setMinimumHeight(300)
        chart_view.setRenderHint(QPainter.Antialiasing)
        right_layout.addWidget(chart_view)

        # Добавляем панели в верхнюю часть
        top_layout.addWidget(left_panel, 1)
        top_layout.addWidget(right_panel, 1)

        content_layout.addWidget(top_widget)

        # === РАЗДЕЛИТЕЛЬ ===
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #26394D; height: 2px; margin: 10px 0;")
        content_layout.addWidget(separator)

        # === НИЖНЯЯ ЧАСТЬ (кривая обучения) ===
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        bottom_title = QLabel("📈 Кривая обучения (по всем сотрудникам)")
        bottom_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #26394D; margin-top: 10px;")
        bottom_layout.addWidget(bottom_title)

        # Выбор пользователя для графика
        user_select_widget = QWidget()
        user_select_layout = QHBoxLayout(user_select_widget)
        user_select_layout.setContentsMargins(0, 10, 0, 10)

        user_select_layout.addWidget(QLabel("Выберите сотрудника:"))
        self.ml_user_combo = QComboBox()
        self.ml_user_combo.setMinimumWidth(200)
        user_select_layout.addWidget(self.ml_user_combo)

        self.ml_refresh_btn = QPushButton("🔄 Показать")
        self.ml_refresh_btn.clicked.connect(self.load_ml_user_data)
        user_select_layout.addWidget(self.ml_refresh_btn)

        user_select_layout.addStretch()
        bottom_layout.addWidget(user_select_widget)

        # Добавляем график (новый экземпляр для ML страницы)
        self.ml_chart = LearningCurveChart()
        self.ml_chart.setMaximumHeight(300)
        bottom_layout.addWidget(self.ml_chart)

        content_layout.addWidget(bottom_widget)

        # Добавляем растяжку внизу
        content_layout.addStretch()

        # Устанавливаем контент в скролл-область
        scroll_area.setWidget(content_widget)

        # Добавляем скролл-область на страницу
        page3_layout.addWidget(scroll_area)

        # Показываем пустую страницу
        self.show_empty_ml_page()

    def switch_page(self, index):
        """Переключает страницу и обновляет стили кнопок"""
        # Переключаем страницу
        self.stacked_widget.setCurrentIndex(index)

        # Сбрасываем стили всех кнопок
        default_style = """
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                text-align: left;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3d566e;
            }
        """
        self.btn_page1.setStyleSheet(default_style)
        self.btn_page2.setStyleSheet(default_style)
        self.btn_page3.setStyleSheet(default_style)

        # Подсвечиваем активную кнопку
        active_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                text-align: left;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        [self.btn_page1, self.btn_page2, self.btn_page3][index].setStyleSheet(active_style)

    def logout(self):
        """Выход из системы"""
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            'Вы действительно хотите выйти?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.close()
            # Запускаем новый экземпляр приложения с формой входа
            from .login_dialog import LoginDialog
            self.login_dialog = LoginDialog()
            self.login_dialog.login_successful.connect(self.__init__)
            self.login_dialog.show()

    def show_empty_ml_page(self):
        """Показывает пустую страницу ML с сообщением"""
        # Очищаем контейнер
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Добавляем сообщение
        msg = QLabel("👆 Нажмите кнопку 'Загрузить ML данные'\nдля отображения статистики")
        msg.setStyleSheet("color: #775928; font-size: 16px; padding: 40px;")
        msg.setAlignment(Qt.AlignCenter)
        self.stats_layout.addWidget(msg)

        # Очищаем диаграмму
        self.pie_series.clear()
        self.pie_series.append("Ожидание данных", 1)
        if self.pie_series.slices():
            self.pie_series.slices()[0].setColor(QColor(200, 200, 200))
            self.pie_series.slices()[0].setLabelVisible(False)

    def update_ml_stats(self):
        """Обновляет статистику на странице"""
        if not hasattr(self, 'user_cache') or not self.user_cache:
            self.show_empty_ml_page()
            return

        try:
            # ОЧИЩАЕМ КОНТЕЙНЕР (без вызова clear_layout)
            while self.stats_layout.count():
                item = self.stats_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            self.pie_series.clear()

            # Собираем статистику
            masteries = [u['accuracy'] for u in self.user_cache]
            total = len(self.user_cache)

            if total == 0:
                self.show_empty_ml_page()
                return

            # Метрики
            stats_data = [
                ("👥 Всего сотрудников:", f"{total} чел.", "#26394D"),
                ("📊 Среднее усвоение:", f"{np.mean(masteries):.1f}%", "#23588C"),
                ("📈 Медиана:", f"{np.median(masteries):.1f}%", "#0066CC"),
                ("📉 Минимум:", f"{min(masteries):.1f}%", "#775928"),
                ("📈 Максимум:", f"{max(masteries):.1f}%", "#26394D"),
            ]

            for label_text, value_text, color in stats_data:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)

                label = QLabel(label_text)
                label.setStyleSheet("font-size: 14px; font-weight: bold; color: #26394D;")

                value = QLabel(value_text)
                value.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
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

            # Уровни
            levels = {
                '🔥 Отлично (>50%)': sum(1 for m in masteries if m >= 50),
                '👍 Хорошо (30-50%)': sum(1 for m in masteries if 30 <= m < 50),
                '👌 Средне (10-30%)': sum(1 for m in masteries if 10 <= m < 30),
                '🔴 Критично (<10%)': sum(1 for m in masteries if m < 10)
            }

            # Цвета для уровней
            colors = {
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
                    level_label.setStyleSheet("font-size: 13px; color: #26394D;")

                    count_label = QLabel(f"{count} чел. ({percentage:.1f}%)")
                    count_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #23588C;")
                    count_label.setAlignment(Qt.AlignRight)

                    row_layout.addWidget(level_label)
                    row_layout.addStretch()
                    row_layout.addWidget(count_label)

                    self.stats_layout.addWidget(row)

                    # Диаграмма
                    slice_ = self.pie_series.append(level_name, count)
                    slice_.setColor(colors[level_name])
                    slice_.setLabelVisible(True)
                    slice_.setLabelPosition(QPieSlice.LabelOutside)
                    slice_.setLabelColor(QColor(38, 57, 77))

            QMessageBox.information(self, "Успех",
                                    f"Статистика загружена!\nСреднее усвоение: {np.mean(masteries):.1f}%")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_empty_ml_page()

    def load_ml_user_data(self):
        """Загружает данные для выбранного пользователя в график на ML странице"""
        if self.ml_user_combo.count() == 0:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите ML данные")
            return

        try:
            # Получаем ID пользователя из данных элемента
            user_id = int(self.ml_user_combo.currentData())

            print(f"📊 Загружаем данные для пользователя ID: {user_id}")

            db_gen = get_db()
            db = next(db_gen)

            df = AnalyticsQueries.get_user_learning_curve(db, user_id)

            if df.empty:
                QMessageBox.warning(self, "Нет данных", f"Нет данных обучения для пользователя {user_id}")
            else:
                self.ml_chart.update_chart(df, user_id)
                print(f"✅ Загружено {len(df)} записей")

            db.close()

        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def load_ml_data_for_page(self):
        """Загружает ML данные только при нажатии кнопки"""
        cache_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ml",
            "user_cache.pkl"
        )

        print(f"🔍 Ищем кэш по пути: {cache_path}")

        if not os.path.exists(cache_path):
            QMessageBox.warning(
                self,
                "Нет данных",
                f"Кэш не найден. Сначала обновите кэш в разделе 'Рейтинг сотрудников'"
            )
            return

        try:
            # Загружаем кэш
            with open(cache_path, 'rb') as f:
                self.user_cache = pickle.load(f)

            print(f"✅ Загружено {len(self.user_cache)} записей")

            # Загружаем пользователей в комбобокс
            self.ml_user_combo.clear()
            for user in self.user_cache:
                # Используем user_id напрямую
                user_id = str(user['user_id'])
                user_name = user['name'].split()[0]  # Берём только имя
                self.ml_user_combo.addItem(f"{user_name} (ID: {user_id})", user_id)

            # Обновляем статистику
            self.update_ml_stats()

            # Если есть пользователи, загружаем первого
            if self.ml_user_combo.count() > 0:
                self.load_ml_user_data()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            import traceback
            traceback.print_exc()