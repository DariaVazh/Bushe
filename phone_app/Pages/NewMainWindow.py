import sys
import os
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel, QWidget
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QIcon


# === Добавляем путь к текущей панке, чтобы импортировать локальные модули ===
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# === Импорт UI классов из той же папки (Pages/) ===
try:
    from enterWin import Ui_EntranceWindow
    from regWin import Ui_RegWindow
    from homeWin import Ui_MainWindow as Ui_HomeWindow
    from gameWin import Ui_MainWindow as Ui_GameWindow
    from guideWin import Ui_MainWindow as Ui_GuideWindow
    from ratingWin import Ui_MainWindow as Ui_RatingWindow
    from recallWin import Ui_MainWindow as Ui_RecallWindow
    from recipeWin import Ui_MainWindow as Ui_RecipeWindow
    from errRedWin import Ui_MainWindow as Ui_ErrRedWindow
    from errGreenWin import Ui_MainWindow as Ui_ErrGreenWindow
    from settingsWin import Ui_MainWindow as Ui_SettingsWindow  # ← импорт экрана настроек
except ImportError as e:
    print(f"❌ Не удалось импортировать UI: {e}")
    print("Убедитесь, что все *Win.py файлы находятся в папке Pages/")
    sys.exit(1)

# === Базовый путь к иконкам ===
ICONS_DIR = r"C:\Users\Фёдор\PycharmProjects\MyBushe\MyIcons"

if not os.path.exists(ICONS_DIR):
    print(f"⚠️ Папка с иконками не найдена: {ICONS_DIR}")
    print("Проверьте путь или скопируйте папку MyIcons в проект.")
    sys.exit(1)


def safe_pixmap_load(image_path: str) -> QPixmap:
    """Безопасная загрузка изображения"""
    full_path = os.path.join(ICONS_DIR, image_path)
    if os.path.exists(full_path):
        pixmap = QPixmap(full_path)
        if not pixmap.isNull():
            return pixmap
        else:
            print(f"🖼️ Изображение повреждено или не поддерживается: {full_path}")
    else:
        print(f"🖼️ Файл не найден: {full_path}")
    return None


def set_background(widget: QWidget, image_path: str):
    """Устанавливает фон через QLabel"""
    pixmap = safe_pixmap_load(image_path)
    if pixmap:
        label = QLabel(widget)
        label.setPixmap(pixmap.scaled(
            widget.size(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        label.resize(widget.size())
        label.lower()
        widget.bg_label = label  # сохраняем ссылку
    else:
        widget.setStyleSheet("background-color: #f0f0f0;")


def set_image(widget: QWidget, image_path: str, mode="scale"):
    """Устанавливает изображение в QLabel / QPushButton"""
    pixmap = safe_pixmap_load(image_path)
    if not pixmap:
        return

    if isinstance(widget, QLabel):
        scaled = pixmap.scaled(
            widget.size(),
            Qt.AspectRatioMode.KeepAspectRatio if mode == "keep" else Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        widget.setPixmap(scaled)
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        widget.setText("")
    elif isinstance(widget, QtWidgets.QPushButton):
        icon = QIcon(pixmap)
        widget.setIcon(icon)
        widget.setIconSize(widget.size())
        widget.setStyleSheet("QPushButton { border: none; background-color: transparent; }")
    elif hasattr(widget, 'setStyleSheet'):
        url = f"file:///{os.path.join(ICONS_DIR, image_path)}".replace("\\", "/")
        widget.setStyleSheet(f"border-image: url('{url}');")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bushe App")
        self.resize(385, 700)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        try:
            self.entrance_window = EntranceWindow(self)
            self.reg_window = RegWindow(self)
            self.home_window = HomeWindow(self)
            self.game_window = GameWindow(self)
            self.guide_window = GuideWindow(self)
            self.rating_window = RatingWindow(self)
            self.recall_window = RecallWindow(self)
            self.recipe_window = RecipeWindow(self)
            self.err_red_window = ErrRedWindow(self)
            self.err_green_window = ErrGreenWindow(self)
            self.settings_window = SettingsWindow(self)  # ← добавлен экран настроек
        except Exception as e:
            print(f"❌ Ошибка при создании окна: {e}")
            sys.exit(1)

        # Добавляем все экраны
        self.stacked_widget.addWidget(self.entrance_window)
        self.stacked_widget.addWidget(self.reg_window)
        self.stacked_widget.addWidget(self.home_window)
        self.stacked_widget.addWidget(self.game_window)
        self.stacked_widget.addWidget(self.guide_window)
        self.stacked_widget.addWidget(self.rating_window)
        self.stacked_widget.addWidget(self.recall_window)
        self.stacked_widget.addWidget(self.recipe_window)
        self.stacked_widget.addWidget(self.err_red_window)
        self.stacked_widget.addWidget(self.err_green_window)
        self.stacked_widget.addWidget(self.settings_window)  # ← индекс 10

        self.stacked_widget.setCurrentWidget(self.entrance_window)


class BaseWindow(QMainWindow):
    switch_window = pyqtSignal(int)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.switch_window.connect(self.main_window.stacked_widget.setCurrentIndex)

    def navigate_to(self, index):
        self.switch_window.emit(index)


# === Общая функция для установки иконок нижней и верхней панели ===
def apply_nav_icons(window):
    """Устанавливает иконки нижней и верхней панелей, если они существуют"""
    ui = window.ui

    # --- Верхняя панель ---
    if hasattr(ui, 'ico_rating'):
        set_image(ui.ico_rating, r"фон+шрифты+верх.панель/рейтинг.ico")
    if hasattr(ui, 'ico_days'):
        set_image(ui.ico_days, r"фон+шрифты+верх.панель/огонёк.ico")

    # --- Нижняя панель (неактивные состояния) ---
    if hasattr(ui, 'btn_home'):
        set_image(ui.btn_home, r"нижняя панель/н.п. 1.1.ico")
    if hasattr(ui, 'btn_rating'):
        set_image(ui.btn_rating, r"нижняя панель/н.п. 2.1.ico")
    if hasattr(ui, 'btn_recall'):
        set_image(ui.btn_recall, r"нижняя панель/н.п. 3.1.ico")
    if hasattr(ui, 'btn_book'):
        set_image(ui.btn_book, r"нижняя панель/н.п. 4.1.ico")
    if hasattr(ui, 'btn_settings'):
        set_image(ui.btn_settings, r"нижняя панель/н.п. 5.1.ico")


# === Экран входа ===
class EntranceWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_EntranceWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.ui.pushButton_reg.clicked.connect(lambda: self.navigate_to(1))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки

    def _apply_styles(self):
        set_background(self.ui.frame_6, r"фон+шрифты+верх.панель/фон.png")
        set_image(self.ui.pushButton_reg, r"1. вход/книпка регистрации.ico")
        set_image(self.ui.frame, r"9. профиль/фон белый общий.ico")
        set_image(self.ui.lineEdit, r"1. вход/фон пол догин и пароль.ico")
        set_image(self.ui.lineEdit_2, r"1. вход/фон пол догин и пароль.ico")
        set_image(self.ui.label_2, r"1. вход/иконка _вход_.ico")
        set_image(self.ui.label, r"1. вход/плашка буше .ico")
        set_image(self.ui.btn_settings, r"1. вход/иконка готово.ico")


# === Экран регистрации ===
class RegWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_RegWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.ui.pushButton_Cancel.clicked.connect(lambda: self.navigate_to(0))
        self.ui.pushButton_Ok.clicked.connect(lambda: self.navigate_to(2))

    def _apply_styles(self):
        pass  # Нет стилей в этом окне


# === Главное меню ===
class HomeWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_HomeWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.setup_nav_buttons()

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_home'):
            set_image(self.ui.btn_home, r"нижняя панель/н.п. 1.2.ico")  # активная
        set_image(self.ui.btn_lvl_1, r"2. главное меню/иконка 1.3.ico")
        set_image(self.ui.btn_lvl_2, r"2. главное меню/иконка 2.1.ico")
        set_image(self.ui.btn_lvl_3, r"2. главное меню/иконка 3.1.ico")
        set_image(self.ui.btn_lvl_4, r"2. главное меню/иконка 4.1.ico")
        set_image(self.ui.btn_lvl_5, r"2. главное меню/иконка 5.1.ico")
        set_image(self.ui.btn_lvl_6, r"2. главное меню/иконка 6.1.ico")
        set_image(self.ui.btn_lvl_7, r"2. главное меню/иконка 7.1.ico")
        set_image(self.ui.btn_lvl_8, r"2. главное меню/иконка 8.1.ico")
        set_image(self.ui.btn_lvl_9, r"2. главное меню/иконка 2.1.ico")

    def setup_nav_buttons(self):
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_rating.clicked.connect(lambda: self.navigate_to(5))
        self.ui.btn_recall.clicked.connect(lambda: self.navigate_to(6))
        self.ui.btn_book.clicked.connect(lambda: self.navigate_to(4))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки
        self.ui.btn_lvl_1.clicked.connect(lambda: self.navigate_to(3))


# === Игра ===
class GameWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_GameWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.setup_nav_buttons()

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_home'):
            set_image(self.ui.btn_home, r"нижняя панель/н.п. 1.2.ico")
        if hasattr(self.ui, 'btn_help'):
            set_image(self.ui.btn_help, r"10-13. собери ингридиенты/кнопка спраки верхняя панель.ico")
        if hasattr(self.ui, 'btn_settings'):
            set_image(self.ui.btn_settings, r"10-13. собери ингридиенты/кнопка готово.ico")
        set_image(self.ui.label, r"10-13. собери ингридиенты/задание.ico")
        set_image(self.ui.label_2, r"10-13. собери ингридиенты/вензель.ico")
        set_image(self.ui.pushButton, r"10-13. собери ингридиенты/фисташки пустое.ico")
        set_image(self.ui.pushButton_2, r"10-13. собери ингридиенты/молоко пустое.ico")
        set_image(self.ui.pushButton_3, r"10-13. собери ингридиенты/брусника пустое.ico")
        set_image(self.ui.pushButton_4, r"10-13. собери ингридиенты/мука пустое.ico")
        set_image(self.ui.pushButton_5, r"10-13. собери ингридиенты/миндаль пустое.ico")

    def setup_nav_buttons(self):
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_help.clicked.connect(lambda: self.navigate_to(9))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки


# === Справочник ===
class GuideWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_GuideWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.setup_nav_buttons()

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_book'):
            set_image(self.ui.btn_book, r"нижняя панель/н.п. 4.2.ico")  # активная
        set_image(self.ui.label, r"5-8. справочник/название.ico")
        set_image(self.ui.frame_4, r"5-8. справочник/1.0.ico")
        set_image(self.ui.btn_1_1, r"5-8. справочник/1.1.ico")
        set_image(self.ui.btn_1_2, r"5-8. справочник/1.2.ico")
        set_image(self.ui.btn_1_3, r"5-8. справочник/1.3.ico")
        set_image(self.ui.btn_1_4, r"5-8. справочник/1.4.ico")
        set_image(self.ui.pushButton, r"5-8. справочник/2.ico")
        set_image(self.ui.pushButton_2, r"5-8. справочник/3.ico")
        set_image(self.ui.pushButton_3, r"5-8. справочник/4.ico")
        set_image(self.ui.pushButton_4, r"5-8. справочник/5.ico")

    def setup_nav_buttons(self):
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_rating.clicked.connect(lambda: self.navigate_to(5))
        self.ui.btn_recall.clicked.connect(lambda: self.navigate_to(6))
        self.ui.btn_book.clicked.connect(lambda: self.navigate_to(4))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки


# === Рейтинг ===
class RatingWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_RatingWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.setup_nav_buttons()

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_rating'):
            set_image(self.ui.btn_rating, r"нижняя панель/н.п. 2.2.ico")  # активная
        set_image(self.ui.label, r"3. рейтинг/медаль 1.ico")
        set_image(self.ui.label_3, r"3. рейтинг/медаль 2.ico")
        set_image(self.ui.label_4, r"3. рейтинг/медаль 3.ico")

    def setup_nav_buttons(self):
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_rating.clicked.connect(lambda: self.navigate_to(5))
        self.ui.btn_recall.clicked.connect(lambda: self.navigate_to(6))
        self.ui.btn_book.clicked.connect(lambda: self.navigate_to(4))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки


# === Воспоминания ===
class RecallWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_RecallWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.setup_nav_buttons()

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_recall'):
            set_image(self.ui.btn_recall, r"нижняя панель/н.п. 3.2.ico")  # активная
        set_image(self.ui.label, r"2. главное меню/1. текст .ico")
        set_image(self.ui.pushButton, r"2. главное меню/иконка 1.3.ico")
        set_image(self.ui.pushButton_2, r"2. главное меню/иконка 8.3.ico")
        set_image(self.ui.pushButton_3, r"2. главное меню/иконка 6.3.ico")
        set_image(self.ui.pushButton_4, r"2. главное меню/иконка 2.3.ico")
        set_image(self.ui.pushButton_5, r"2. главное меню/иконка 9.1.ico")
        set_image(self.ui.pushButton_6, r"2. главное меню/иконка 4.3.ico")
        set_image(self.ui.pushButton_7, r"2. главное меню/иконка 3.1.ico")
        set_image(self.ui.pushButton_8, r"2. главное меню/иконка 5.3.ico")
        set_image(self.ui.pushButton_9, r"2. главное меню/иконка 7.3.ico")

    def setup_nav_buttons(self):
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_rating.clicked.connect(lambda: self.navigate_to(5))
        self.ui.btn_recall.clicked.connect(lambda: self.navigate_to(6))
        self.ui.btn_book.clicked.connect(lambda: self.navigate_to(4))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки


# === Рецепты ===
class RecipeWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_RecipeWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.setup_nav_buttons()

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_book'):
            set_image(self.ui.btn_book, r"нижняя панель/н.п. 4.2.ico")  # активная
        set_image(self.ui.label, r"5-8. справочник/экраны справочника с инфой и ошибкой/название составы.ico")
        set_image(self.ui.label_2, r"5-8. справочник/экраны справочника с инфой и ошибкой/рецепт.ico")

    def setup_nav_buttons(self):
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_book.clicked.connect(lambda: self.navigate_to(4))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки


# === Ошибка (красная) ===
class ErrRedWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_ErrRedWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_home'):
            set_image(self.ui.btn_home, r"нижняя панель/н.п. 1.2.ico")  # активная
        set_image(self.ui.label, r"5-8. справочник/экраны справочника с инфой и ошибкой/ошибка 0.ico")
        set_image(self.ui.label_2, r"5-8. справочник/экраны справочника с инфой и ошибкой/ошибка 1.ico")


# === Ошибка (зелёная) ===
class ErrGreenWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_ErrGreenWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # → настройки

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_home'):
            set_image(self.ui.btn_home, r"нижняя панель/н.п. 1.2.ico")  # активная
        set_image(self.ui.label, r"5-8. справочник/экраны справочника с инфой и ошибкой/ошибка 2.ico")
        set_image(self.ui.label_2, r"5-8. справочник/экраны справочника с инфой и ошибкой/ошибка 3.ico")


# === Настройки ===
class SettingsWindow(BaseWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self)
        self._apply_styles()
        self.setup_nav_buttons()

    def _apply_styles(self):
        set_background(self.ui.frame_3, r"фон+шрифты+верх.панель/фон.png")
        apply_nav_icons(self)
        if hasattr(self.ui, 'btn_settings'):
            set_image(self.ui.btn_settings, r"нижняя панель/н.п. 5.2.ico")  # активная
        if hasattr(self.ui, 'photo_profile'):
            set_image(self.ui.photo_profile, r"9. профиль/иконка профиля.ico", mode="keep")
        if hasattr(self.ui, 'label'):
            set_image(self.ui.label, r"9. профиль/фон под фио.ico")
            self.ui.label.setText("Имя Кличка")
        if hasattr(self.ui, 'btn_chat'):
            set_image(self.ui.btn_chat, r"9. профиль/иконка чата.ico")
        if hasattr(self.ui, 'btn_exit'):
            set_image(self.ui.btn_exit, r"9. профиль/иконка выхода.ico")

    def setup_nav_buttons(self):
        self.ui.btn_home.clicked.connect(lambda: self.navigate_to(2))
        self.ui.btn_rating.clicked.connect(lambda: self.navigate_to(5))
        self.ui.btn_recall.clicked.connect(lambda: self.navigate_to(6))
        self.ui.btn_book.clicked.connect(lambda: self.navigate_to(4))
        self.ui.btn_settings.clicked.connect(lambda: self.navigate_to(10))  # остаёмся здесь
        self.ui.btn_exit.clicked.connect(lambda: self.navigate_to(0))  # выход в меню входа


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())