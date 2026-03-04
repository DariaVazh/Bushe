# hr_learning_dashboards/widgets/auth_window.py
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMessageBox
import sys
import os
import random

# Добавляем путь к learning_platform_db
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import get_db
from Bushe.learning_platform_db.models import User
from Bushe.learning_platform_db.crud import UserCRUD


class AuthWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация - HR Learning Dashboard")
        self.resize(385, 700)

        # Центрируем окно
        self.center()

        # Создаем stacked widget
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Создаем страницы
        self.entrance_page = QtWidgets.QWidget()
        self.reg_page = QtWidgets.QWidget()

        # Настраиваем интерфейсы на страницах
        self.setup_entrance_page()
        self.setup_reg_page()

        # Добавляем страницы в stacked widget
        self.stacked_widget.addWidget(self.entrance_page)  # индекс 0 - страница входа
        self.stacked_widget.addWidget(self.reg_page)  # индекс 1 - страница регистрации

        # Показываем страницу входа
        self.stacked_widget.setCurrentIndex(0)

    def center(self):
        """Центрирует окно на экране"""
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def setup_entrance_page(self):
        """Настройка страницы входа"""
        # Основной layout для страницы входа
        main_layout = QtWidgets.QVBoxLayout(self.entrance_page)

        # Заголовок
        label_entrance = QtWidgets.QLabel("Вход")
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setUnderline(True)
        label_entrance.setFont(font)
        label_entrance.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_entrance)

        # Верхний отступ
        main_layout.addSpacerItem(QtWidgets.QSpacerItem(
            20, 86,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding
        ))

        # Контейнер для полей ввода
        fields_layout = QtWidgets.QVBoxLayout()

        # Поле для логина/телефона
        self.entrance_lineEdit_login = QtWidgets.QLineEdit()
        self.entrance_lineEdit_login.setPlaceholderText("Введите логин или номер телефона")
        fields_layout.addWidget(self.entrance_lineEdit_login)

        # Поле для пароля
        self.entrance_lineEdit_password = QtWidgets.QLineEdit()
        self.entrance_lineEdit_password.setPlaceholderText("Введите пароль")
        self.entrance_lineEdit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        fields_layout.addWidget(self.entrance_lineEdit_password)

        main_layout.addLayout(fields_layout)

        # Отступ
        main_layout.addSpacerItem(QtWidgets.QSpacerItem(
            20, 26,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding
        ))

        # Разделитель "ИЛИ"
        separator_layout = QtWidgets.QHBoxLayout()

        line_left = QtWidgets.QFrame()
        line_left.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line_left.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        separator_layout.addWidget(line_left)

        label_or = QtWidgets.QLabel("ИЛИ")
        label_or.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        separator_layout.addWidget(label_or)

        line_right = QtWidgets.QFrame()
        line_right.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line_right.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        separator_layout.addWidget(line_right)

        main_layout.addLayout(separator_layout)

        # Отступ
        main_layout.addSpacerItem(QtWidgets.QSpacerItem(
            20, 36,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding
        ))

        # Кнопка регистрации
        self.entrance_btn_reg = QtWidgets.QPushButton("Регистрация")
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.entrance_btn_reg.setFont(font)
        self.entrance_btn_reg.clicked.connect(self.show_registration_page)
        main_layout.addWidget(self.entrance_btn_reg)

        # Нижний отступ
        main_layout.addSpacerItem(QtWidgets.QSpacerItem(
            20, 276,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding
        ))

        # Кнопка входа
        self.entrance_btn_login = QtWidgets.QPushButton("Войти")
        self.entrance_btn_login.clicked.connect(self.login)
        main_layout.addWidget(self.entrance_btn_login)

    def setup_reg_page(self):
        """Настройка страницы регистрации"""
        # Основной layout для страницы регистрации
        main_layout = QtWidgets.QVBoxLayout(self.reg_page)

        # Заголовок
        label_reg = QtWidgets.QLabel("Регистрация")
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setUnderline(True)
        label_reg.setFont(font)
        label_reg.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_reg)

        # Сетка для полей ввода
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)

        # Имя
        label_name = QtWidgets.QLabel("Имя")
        font = QtGui.QFont()
        font.setBold(True)
        label_name.setFont(font)
        label_name.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight |
            QtCore.Qt.AlignmentFlag.AlignTrailing |
            QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        grid_layout.addWidget(label_name, 0, 0, 1, 1)

        self.reg_lineEdit_name = QtWidgets.QLineEdit()
        self.reg_lineEdit_name.setPlaceholderText("Введите имя")
        self.reg_lineEdit_name.setStyleSheet(
            "QLineEdit { border-width: 1px; border-style: solid; border-radius: 5px; }")
        grid_layout.addWidget(self.reg_lineEdit_name, 0, 1, 1, 2)

        # Фамилия
        label_surname = QtWidgets.QLabel("Фамилия")
        font = QtGui.QFont()
        font.setBold(True)
        label_surname.setFont(font)
        label_surname.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight |
            QtCore.Qt.AlignmentFlag.AlignTrailing |
            QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        grid_layout.addWidget(label_surname, 1, 0, 1, 1)

        self.reg_lineEdit_surname = QtWidgets.QLineEdit()
        self.reg_lineEdit_surname.setPlaceholderText("Введите фамилию")
        self.reg_lineEdit_surname.setStyleSheet(
            "QLineEdit { border-width: 1px; border-style: solid; border-radius: 5px; }")
        grid_layout.addWidget(self.reg_lineEdit_surname, 1, 1, 1, 2)

        # Телефон
        label_phone = QtWidgets.QLabel("Номер телефона")
        font = QtGui.QFont()
        font.setBold(True)
        label_phone.setFont(font)
        label_phone.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight |
            QtCore.Qt.AlignmentFlag.AlignTrailing |
            QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        grid_layout.addWidget(label_phone, 2, 0, 1, 1)

        self.reg_lineEdit_phone = QtWidgets.QLineEdit()
        self.reg_lineEdit_phone.setPlaceholderText("Введите номер телефона")
        self.reg_lineEdit_phone.setStyleSheet(
            "QLineEdit { border-width: 1px; border-style: solid; border-radius: 5px; }")
        grid_layout.addWidget(self.reg_lineEdit_phone, 2, 1, 1, 2)

        # Должность
        label_role = QtWidgets.QLabel("Ваша должность")
        font = QtGui.QFont()
        font.setBold(True)
        label_role.setFont(font)
        label_role.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight |
            QtCore.Qt.AlignmentFlag.AlignTrailing |
            QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        grid_layout.addWidget(label_role, 3, 0, 1, 1)

        self.reg_comboBox_role = QtWidgets.QComboBox()
        self.reg_comboBox_role.addItems([
            "Работник торгового зала",
            "Продавец-кассир",
            "Администратор"
        ])
        self.reg_comboBox_role.setStyleSheet(
            "QComboBox { border-width: 1px; border-style: solid; border-radius: 5px; }")
        grid_layout.addWidget(self.reg_comboBox_role, 3, 1, 1, 2)

        # Пароль
        label_password = QtWidgets.QLabel("Пароль")
        font = QtGui.QFont()
        font.setBold(True)
        label_password.setFont(font)
        label_password.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight |
            QtCore.Qt.AlignmentFlag.AlignTrailing |
            QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        grid_layout.addWidget(label_password, 4, 0, 1, 1)

        # Создаем горизонтальный layout для поля пароля и кнопки показа
        password_layout = QtWidgets.QHBoxLayout()

        self.reg_lineEdit_password = QtWidgets.QLineEdit()
        self.reg_lineEdit_password.setPlaceholderText("Введите пароль")
        self.reg_lineEdit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.reg_lineEdit_password.setStyleSheet(
            "QLineEdit { border-width: 1px; border-style: solid; border-radius: 5px; }")
        password_layout.addWidget(self.reg_lineEdit_password)

        self.reg_btn_show_password = QtWidgets.QPushButton("👁")
        self.reg_btn_show_password.setFixedWidth(30)
        self.reg_btn_show_password.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.reg_btn_show_password)

        grid_layout.addLayout(password_layout, 4, 1, 1, 2)

        # Повтор пароля
        label_rep_password = QtWidgets.QLabel("Повтор пароля")
        font = QtGui.QFont()
        font.setBold(True)
        label_rep_password.setFont(font)
        label_rep_password.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight |
            QtCore.Qt.AlignmentFlag.AlignTrailing |
            QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        grid_layout.addWidget(label_rep_password, 5, 0, 1, 1)

        # Создаем горизонтальный layout для повтора пароля и кнопки показа
        rep_password_layout = QtWidgets.QHBoxLayout()

        self.reg_lineEdit_rep_password = QtWidgets.QLineEdit()
        self.reg_lineEdit_rep_password.setPlaceholderText("Повторите пароль")
        self.reg_lineEdit_rep_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.reg_lineEdit_rep_password.setStyleSheet(
            "QLineEdit { border-width: 1px; border-style: solid; border-radius: 5px; }")
        rep_password_layout.addWidget(self.reg_lineEdit_rep_password)

        self.reg_btn_show_rep_password = QtWidgets.QPushButton("👁")
        self.reg_btn_show_rep_password.setFixedWidth(30)
        self.reg_btn_show_rep_password.clicked.connect(self.toggle_rep_password_visibility)
        rep_password_layout.addWidget(self.reg_btn_show_rep_password)

        grid_layout.addLayout(rep_password_layout, 5, 1, 1, 2)

        # Чекбокс согласия
        self.reg_checkBox = QtWidgets.QCheckBox(
            "Я соглашаюсь на обработку моих персональных данных\n"
            "в соответствии с Политикой обработки персональных\n"
            "данных"
        )
        grid_layout.addWidget(self.reg_checkBox, 6, 0, 1, 3)

        main_layout.addLayout(grid_layout)

        # Растягивающийся отступ
        main_layout.addSpacerItem(QtWidgets.QSpacerItem(
            20, 298,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding
        ))

        # Горизонтальный layout для кнопок
        buttons_layout = QtWidgets.QHBoxLayout()

        self.reg_btn_cancel = QtWidgets.QPushButton("Отмена")
        self.reg_btn_cancel.clicked.connect(self.show_entrance_page)
        buttons_layout.addWidget(self.reg_btn_cancel)

        self.reg_btn_ok = QtWidgets.QPushButton("ОК")
        self.reg_btn_ok.clicked.connect(self.register)
        buttons_layout.addWidget(self.reg_btn_ok)

        main_layout.addLayout(buttons_layout)

    def show_entrance_page(self):
        """Переключение на страницу входа"""
        self.stacked_widget.setCurrentIndex(0)

    def show_registration_page(self):
        """Переключение на страницу регистрации"""
        self.stacked_widget.setCurrentIndex(1)

    def login(self):
        """Обработка входа"""
        login = self.entrance_lineEdit_login.text().strip()
        password = self.entrance_lineEdit_password.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        try:
            db_gen = get_db()
            db = next(db_gen)

            # Ищем пользователя по логину или телефону
            user = db.query(User).filter(
                (User.user_name == login) | (User.user_phone_number == login)
            ).first()

            if user and user.user_password_cash == password:
                QMessageBox.information(self, "Успех", f"Добро пожаловать, {user.user_name}!")

                user_data = {
                    'user_id': user.user_id,
                    'username': user.user_name,
                    'full_name': f"{user.user_name} {user.user_surname}",
                    'role': user.user_role,
                    'phone': user.user_phone_number
                }

                db.close()
                self.open_main_window(user_data)

            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль!")
                db.close()

        except Exception as e:
            print(f"Ошибка входа: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к БД: {str(e)}")

    def register(self):
        """Обработка регистрации"""
        # Собираем данные
        name = self.reg_lineEdit_name.text().strip()
        surname = self.reg_lineEdit_surname.text().strip()
        phone = self.reg_lineEdit_phone.text().strip()
        password = self.reg_lineEdit_password.text()
        rep_password = self.reg_lineEdit_rep_password.text()
        role_text = self.reg_comboBox_role.currentText()
        consent = self.reg_checkBox.isChecked()

        # Проверка заполнения
        if not all([name, surname, phone, password, rep_password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if password != rep_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают!")
            return

        if not consent:
            QMessageBox.warning(self, "Ошибка", "Необходимо согласие на обработку данных!")
            return

        # Преобразуем роль
        role_map = {
            "Работник торгового зала": "seller",
            "Продавец-кассир": "cashier",
            "Администратор": "admin"
        }
        role = role_map.get(role_text, "user")

        try:
            db_gen = get_db()
            db = next(db_gen)

            # Проверяем, нет ли уже такого телефона
            existing = db.query(User).filter(User.user_phone_number == phone).first()
            if existing:
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким телефоном уже существует!")
                db.close()
                return

            # Генерируем логин из имени
            username = name.lower() + str(random.randint(1, 999))

            # Создаем пользователя
            new_user = UserCRUD.create(
                db,
                user_name=username,
                user_surname=surname,
                user_role=role,
                user_phone_number=phone,
                user_password_cash=password
            )

            QMessageBox.information(
                self, "Успех",
                f"Регистрация выполнена!\nВаш логин: {username}\nЗапомните его для входа!"
            )

            db.close()

            # Очищаем поля
            self.reg_lineEdit_name.clear()
            self.reg_lineEdit_surname.clear()
            self.reg_lineEdit_phone.clear()
            self.reg_lineEdit_password.clear()
            self.reg_lineEdit_rep_password.clear()
            self.reg_checkBox.setChecked(False)

            # Возвращаемся на страницу входа
            self.show_entrance_page()

        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при регистрации: {str(e)}")

    def toggle_password_visibility(self):
        """Показать/скрыть пароль"""
        if self.reg_lineEdit_password.echoMode() == QtWidgets.QLineEdit.EchoMode.Password:
            self.reg_lineEdit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
            self.reg_btn_show_password.setText("🔒")
        else:
            self.reg_lineEdit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.reg_btn_show_password.setText("👁")

    def toggle_rep_password_visibility(self):
        """Показать/скрыть повтор пароля"""
        if self.reg_lineEdit_rep_password.echoMode() == QtWidgets.QLineEdit.EchoMode.Password:
            self.reg_lineEdit_rep_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
            self.reg_btn_show_rep_password.setText("🔒")
        else:
            self.reg_lineEdit_rep_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.reg_btn_show_rep_password.setText("👁")

    def open_main_window(self, user_data):
        """Открывает главное окно дашборда"""
        from .main_window import MainWindow
        self.main_window = MainWindow(user_data)
        self.main_window.showMaximized()
        self.close()