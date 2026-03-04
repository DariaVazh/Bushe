# hr_learning_dashboards/widgets/main_window.py
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox,
                             QPushButton, QMessageBox, QStatusBar)
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

        self.user_data = user_data or {'username': 'Гость', 'role': 'guest'}

        self.setWindowTitle(f"HR Learning Dashboard - {self.user_data['full_name']}")

        # ПОЛНОЭКРАННЫЙ РЕЖИМ
        self.showMaximized()  # вместо setGeometry

        # Или если нужен реальный fullscreen (без заголовка):
        # self.showFullScreen()

        # Добавляем статус бар
        self.statusBar().showMessage(f"Пользователь: {self.user_data['full_name']} | Роль: {self.user_data['role']}")
        # Добавляем статус бар
        self.statusBar().showMessage(f"Пользователь: {self.user_data['full_name']} | Роль: {self.user_data['role']}")

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

        title = QLabel(f"📊 Аналитика обучения")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        panel_layout.addWidget(title)

        panel_layout.addStretch()

        # Добавляем метку с ролью
        role_label = QLabel(f"[{self.user_data['role']}]")
        role_label.setStyleSheet("color: #3498db; font-size: 14px;")
        panel_layout.addWidget(role_label)

        panel_layout.addWidget(QLabel("Сотрудник:"))
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(200)
        self.user_combo.currentIndexChanged.connect(self.on_user_changed)
        panel_layout.addWidget(self.user_combo)

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.refresh_data)
        panel_layout.addWidget(self.refresh_btn)

        # Кнопка выхода
        self.logout_btn = QPushButton("🚪 Выйти")
        self.logout_btn.clicked.connect(self.logout)
        panel_layout.addWidget(self.logout_btn)

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

            self.statusBar().showMessage(f"Загружены данные для пользователя {user_id}")

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

    def logout(self):
        """Выход из системы"""
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            'Вы действительно хотите выйти?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.close()
            # Запускаем новый экземпляр приложения с формой входа
            from .login_dialog import LoginDialog
            import sys
            from PyQt5.QtWidgets import QApplication

            dialog = LoginDialog()
            if dialog.exec_() == LoginDialog.Accepted:
                user_data = dialog.login_successful
                self.__init__(user_data)
                self.show()
            else:
                sys.exit()

    def create_charts(self):
        """Создает вкладки с графиками и рейтингом"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #34495e;
                background-color: #2c3e50;
            }
            QTabBar::tab {
                background-color: #34495e;
                color: white;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
            }
            QTabBar::tab:hover {
                background-color: #3d566e;
            }
        """)

        # Вкладка с графиком
        self.chart_tab = QWidget()
        chart_layout = QVBoxLayout(self.chart_tab)
        self.chart = LearningCurveChart()
        chart_layout.addWidget(self.chart)
        self.tab_widget.addTab(self.chart_tab, "📈 Кривая обучения")

        # Вкладка с рейтингом (только для админа)
        if self.user_data['role'] == 'admin':
            self.rating_tab = QWidget()
            rating_layout = QVBoxLayout(self.rating_tab)
            self.user_list = UserListWidget()
            self.user_list.set_user_role(self.user_data['role'])
            self.user_list.load_users()
            rating_layout.addWidget(self.user_list)
            self.tab_widget.addTab(self.rating_tab, "🏆 Рейтинг сотрудников")

        self.layout.addWidget(self.tab_widget)

    def refresh_rating(self):
        """Обновляет рейтинг (вызывается из кнопки обновления)"""
        if hasattr(self, 'user_list'):
            self.user_list.load_users()