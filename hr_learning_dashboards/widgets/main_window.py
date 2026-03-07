# hr_learning_dashboards/widgets/main_window.py
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel,
                             QStackedWidget, QFrame, QMessageBox)
from PyQt5.QtCore import Qt
from sqlalchemy import text
from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout
from .user_list_widget import UserListWidget
from Bushe.learning_platform_db.database import get_db
from Bushe.learning_platform_db.queries import AnalyticsQueries

from .learning_curve_chart import LearningCurveChart


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
        layout3 = QVBoxLayout(self.page3)
        layout3.setContentsMargins(20, 20, 20, 20)

        title3 = QLabel("Аналитика")
        title3.setStyleSheet("font-size: 24px; font-weight: bold; color: #26394D;")
        layout3.addWidget(title3)

        # Место для ML аналитики
        ml_label = QLabel("Здесь будет ML аналитика")
        ml_label.setStyleSheet("font-size: 16px; color: ##26394D; padding: 50px;")
        ml_label.setAlignment(Qt.AlignCenter)
        layout3.addWidget(ml_label)

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