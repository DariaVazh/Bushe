# hr_learning_dashboards/widgets/user_details_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QGroupBox,
                             QGridLayout, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class UserDetailsDialog(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)

        self.user_data = user_data
        self.setWindowTitle(f"Детальная информация: {user_data['name']}")
        self.setMinimumSize(600, 500)

        # Центрируем окно
        self.center()

        self.setup_ui()

    def center(self):
        qr = self.frameGeometry()
        cp = self.parent().frameGeometry().center() if self.parent() else self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Заголовок
        title = QLabel(f"👤 {self.user_data['name']}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
        layout.addWidget(title)

        # Основная информация
        info_group = QGroupBox("Основная информация")
        info_layout = QGridLayout()

        labels = [
            ("Роль:", self.user_data['role']),
            ("Телефон:", self.user_data['phone']),
            ("Дата регистрации:", self.user_data['created']),
            ("Последняя активность:", self.user_data['last_active'])
        ]

        for i, (label, value) in enumerate(labels):
            info_layout.addWidget(QLabel(label), i, 0)
            value_label = QLabel(str(value))
            value_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            info_layout.addWidget(value_label, i, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Статистика
        stats_group = QGroupBox("Статистика обучения")
        stats_layout = QGridLayout()

        stats = self.user_data['stats']
        stat_items = [
            ("Всего ответов:", stats['total']),
            ("Правильных:", stats['correct']),
            ("Точность:", f"{stats['accuracy']}%"),
            ("Всего баллов:", stats['score']),
            ("Дней активности:", stats['days_active'])
        ]

        for i, (label, value) in enumerate(stat_items):
            stats_layout.addWidget(QLabel(label), i, 0)
            value_label = QLabel(str(value))
            value_label.setStyleSheet("font-weight: bold; color: #27ae60;")
            stats_layout.addWidget(value_label, i, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Прогресс по темам
        if self.user_data['topics']:
            topics_group = QGroupBox("Последние темы")
            topics_layout = QVBoxLayout()

            for topic in self.user_data['topics']:
                topic_widget = QFrame()
                topic_widget.setFrameShape(QFrame.StyledPanel)
                topic_layout = QHBoxLayout(topic_widget)

                topic_layout.addWidget(QLabel(f"Тема #{topic['item_id']}:"))

                # Прогресс бар в виде текста
                progress = topic['success_rate']
                color = "#27ae60" if progress >= 70 else "#f39c12" if progress >= 40 else "#e74c3c"
                progress_label = QLabel(f"{progress}% ({topic['review_count']} повтор.)")
                progress_label.setStyleSheet(f"font-weight: bold; color: {color};")
                topic_layout.addWidget(progress_label)

                topic_layout.addStretch()
                topics_layout.addWidget(topic_widget)

            topics_group.setLayout(topics_layout)
            layout.addWidget(topics_group)

        # Кнопка закрытия
        btn_close = QPushButton("Закрыть")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_close.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

        self.setLayout(layout)