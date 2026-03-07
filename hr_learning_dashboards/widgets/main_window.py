# hr_learning_dashboards/widgets/main_window.py
import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel,
                             QStackedWidget, QFrame, QMessageBox, QComboBox, QScrollArea, QListWidget)
from PyQt5.QtCore import Qt
from sqlalchemy import text
from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout
from .user_list_widget import UserListWidget
from Bushe.learning_platform_db.database import get_db
from Bushe.learning_platform_db.queries import AnalyticsQueries

from .learning_curve_chart import LearningCurveChart

import pickle
import numpy as np
from PyQt5.QtChart import QChart, QPieSeries, QChartView, QPieSlice, QDateTimeAxis, QValueAxis, QLineSeries
from PyQt5.QtGui import QPainter, QColor, QPen


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

        scroll_area.setMinimumHeight(800)

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

        # === НИЖНЯЯ ЧАСТЬ (графики и списки) ===
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(25)

        # --- Первый график (индивидуальный) ---
        individual_title = QLabel("📈 Индивидуальная кривая обучения")
        individual_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #26394D; margin-top: 20px;")
        bottom_layout.addWidget(individual_title)

        # Выбор пользователя для графика
        user_select_widget = QWidget()
        user_select_layout = QHBoxLayout(user_select_widget)
        user_select_layout.setContentsMargins(0, 10, 0, 15)

        user_select_layout.addWidget(QLabel("Выберите сотрудника:"))
        self.ml_user_combo = QComboBox()
        self.ml_user_combo.setMinimumWidth(250)
        user_select_layout.addWidget(self.ml_user_combo)

        self.ml_refresh_btn = QPushButton("🔄 Показать")
        self.ml_refresh_btn.clicked.connect(self.load_ml_user_data)
        user_select_layout.addWidget(self.ml_refresh_btn)

        user_select_layout.addStretch()
        bottom_layout.addWidget(user_select_widget)

        # Индивидуальный график
        self.ml_chart = LearningCurveChart()
        self.ml_chart.setMinimumHeight(300)
        self.ml_chart.setMaximumHeight(400)
        bottom_layout.addWidget(self.ml_chart)

        # Отступ
        bottom_layout.addSpacing(30)

        # --- Второй график (среднее по компании) ---
        average_title = QLabel("📊 Среднее усвоение по компании")
        average_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #26394D;")
        bottom_layout.addWidget(average_title)

        # Контейнер для графика среднего усвоения
        self.avg_chart = QChart()
        self.avg_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.avg_chart.setTheme(QChart.ChartThemeLight)
        self.avg_chart.setBackgroundVisible(False)

        self.avg_series = QLineSeries()
        self.avg_series.setName("Среднее усвоение")
        pen = QPen(QColor(35, 88, 140))
        pen.setWidth(3)
        self.avg_series.setPen(pen)

        self.avg_chart.addSeries(self.avg_series)

        # Оси
        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd.MM")
        axis_x.setTitleText("Дата")

        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTitleText("Усвоение (%)")

        self.avg_chart.addAxis(axis_x, Qt.AlignBottom)
        self.avg_chart.addAxis(axis_y, Qt.AlignLeft)
        self.avg_series.attachAxis(axis_x)
        self.avg_series.attachAxis(axis_y)

        avg_chart_view = QChartView(self.avg_chart)
        avg_chart_view.setMinimumHeight(250)
        avg_chart_view.setMaximumHeight(350)
        avg_chart_view.setRenderHint(QPainter.Antialiasing)
        bottom_layout.addWidget(avg_chart_view)

        # Кнопка обновления среднего графика
        self.refresh_avg_btn = QPushButton("🔄 Обновить среднее")
        self.refresh_avg_btn.setStyleSheet("""
            QPushButton {
                background-color: #23588C;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
                margin-top: 5px;
                margin-bottom: 15px;
            }
            QPushButton:hover {
                background-color: #0066CC;
            }
        """)
        self.refresh_avg_btn.clicked.connect(self.update_average_chart)
        bottom_layout.addWidget(self.refresh_avg_btn)

        # === ДВА СПИСКА ВОПРОСОВ (СЛОЖНЫЕ И ПРОСТЫЕ) ===
        questions_widget = QWidget()
        questions_layout = QHBoxLayout(questions_widget)
        questions_layout.setContentsMargins(0, 20, 0, 20)
        questions_layout.setSpacing(20)

        # Левый список - сложные вопросы
        hard_frame = QFrame()
        hard_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFE;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #775928;
            }
        """)
        hard_layout = QVBoxLayout(hard_frame)

        hard_title = QLabel("🔴 Топ-5 сложных вопросов")
        hard_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #775928; margin-bottom: 10px;")
        hard_layout.addWidget(hard_title)

        self.hard_list = QListWidget()
        self.hard_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
        """)
        hard_layout.addWidget(self.hard_list)

        # Правый список - простые вопросы
        easy_frame = QFrame()
        easy_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFE;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #23588C;
            }
        """)
        easy_layout = QVBoxLayout(easy_frame)

        easy_title = QLabel("🟢 Топ-5 простых вопросов")
        easy_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #23588C; margin-bottom: 10px;")
        easy_layout.addWidget(easy_title)

        self.easy_list = QListWidget()
        self.easy_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
        """)
        easy_layout.addWidget(self.easy_list)

        questions_layout.addWidget(hard_frame)
        questions_layout.addWidget(easy_frame)

        bottom_layout.addWidget(questions_widget)

        # Пояснительный текст
        info_label = QLabel(
            "📌 Сложные вопросы — с низким процентом правильных ответов (<30%)\n"
            "📌 Простые вопросы — с высоким процентом правильных ответов (>70%)"
        )
        info_label.setStyleSheet(
            "color: #775928; font-size: 12px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        info_label.setWordWrap(True)
        bottom_layout.addWidget(info_label)

        # Финальный отступ
        bottom_layout.addSpacing(30)

        content_layout.addWidget(bottom_widget)

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

        if index == 2 and hasattr(self, 'user_cache') and self.user_cache:
            self.update_average_chart()

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

    def update_average_chart(self):
        """Обновляет график среднего усвоения по компании"""
        if not hasattr(self, 'user_cache') or not self.user_cache:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите ML данные")
            return

        try:
            # Очищаем старые данные
            self.avg_series.clear()

            # Получаем данные из БД за последние 30 дней
            db_gen = get_db()
            db = next(db_gen)

            # Запрос для получения среднего усвоения по дням
            from sqlalchemy import text
            query = text("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(outcome) as daily_avg
                FROM interactions
                WHERE timestamp > NOW() - INTERVAL '30 days'
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)

            df = pd.read_sql(query, db.bind)
            db.close()

            if df.empty:
                QMessageBox.warning(self, "Нет данных", "Нет данных за последние 30 дней")
                return

            # Заполняем серию
            from PyQt5.QtCore import QDateTime

            for _, row in df.iterrows():
                date_str = str(row['date'])
                qdatetime = QDateTime.fromString(date_str, "yyyy-MM-dd")
                if qdatetime.isValid():
                    timestamp = qdatetime.toMSecsSinceEpoch()
                    self.avg_series.append(timestamp, row['daily_avg'] * 100)

            # Обновляем диапазон оси Y
            max_value = df['daily_avg'].max() * 100
            min_value = df['daily_avg'].min() * 100
            padding = (max_value - min_value) * 0.1
            axis_y = self.avg_chart.axes(Qt.Vertical)[0]
            axis_y.setRange(max(0, min_value - padding), min(100, max_value + padding))

            # Обновляем заголовок
            self.avg_chart.setTitle(f"Среднее усвоение: {df['daily_avg'].mean() * 100:.1f}%")

            QMessageBox.information(self, "Успех", "График среднего усвоения обновлён")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить график: {str(e)}")
            import traceback
            traceback.print_exc()

    def load_questions_lists(self):
        """Загружает топ-5 сложных и простых вопросов"""
        try:
            db_gen = get_db()
            db = next(db_gen)

            # Получаем статистику по вопросам
            query = text("""
                SELECT 
                    ki.item_id,
                    ki.domain,
                    COUNT(i.interaction_id) as attempts,
                    AVG(i.outcome) * 100 as success_rate
                FROM knowledge_items ki
                JOIN interactions i ON ki.item_id = i.item_id
                GROUP BY ki.item_id, ki.domain
                HAVING COUNT(i.interaction_id) > 10
                ORDER BY success_rate
            """)

            df = pd.read_sql(query, db.bind)
            db.close()

            if df.empty:
                return

            # Очищаем списки
            self.hard_list.clear()
            self.easy_list.clear()

            # Сложные вопросы (самый низкий процент)
            hard_questions = df.head(5)
            for _, row in hard_questions.iterrows():
                item_text = f"❓ {row['domain']} (вопрос #{row['item_id']}) — {row['success_rate']:.1f}%"
                self.hard_list.addItem(item_text)

            # Простые вопросы (самый высокий процент)
            easy_questions = df.tail(5).iloc[::-1]  # в обратном порядке
            for _, row in easy_questions.iterrows():
                item_text = f"✅ {row['domain']} (вопрос #{row['item_id']}) — {row['success_rate']:.1f}%"
                self.easy_list.addItem(item_text)

        except Exception as e:
            print(f"Ошибка загрузки вопросов: {e}")

    def load_ml_data_for_page(self):
        """Загружает ML данные только при нажатии кнопки"""
        cache_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ml",
            "user_cache.pkl"
        )

        if not os.path.exists(cache_path):
            QMessageBox.warning(
                self,
                "Нет данных",
                "Кэш не найден. Сначала обновите кэш в разделе 'Рейтинг сотрудников'"
            )
            return

        try:
            # Загружаем кэш
            with open(cache_path, 'rb') as f:
                self.user_cache = pickle.load(f)

            # Загружаем пользователей в комбобокс
            self.ml_user_combo.clear()
            for user in self.user_cache:
                user_id = str(user['user_id'])
                user_name = user['name'].split()[0]
                self.ml_user_combo.addItem(f"{user_name} (ID: {user_id})", user_id)

            # Обновляем статистику
            self.update_ml_stats()

            # Загружаем списки вопросов
            self.load_questions_lists()

            # Если есть пользователи, загружаем первого
            if self.ml_user_combo.count() > 0:
                self.load_ml_user_data()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

