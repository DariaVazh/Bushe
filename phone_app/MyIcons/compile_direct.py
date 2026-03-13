import os
import sys
from PyQt5 import pyrcc_main


def compile_resources():
    """Прямая компиляция с правильными путями"""

    qrc_file = "resources.qrc"
    output_file = "../resources_rc.py"

    print(f"🔧 Компиляция {qrc_file} -> {output_file}")

    # Читаем файл и заменяем пути на лету
    with open(qrc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Создаем временный файл с правильными путями
    temp_qrc = "temp_resources.qrc"
    with open(temp_qrc, 'w', encoding='utf-8') as f:
        # Убираем абсолютные пути
        fixed_content = content.replace(
            'C:/Users/Фёдор/PycharmProjects/Bushe/MyIcons/', ''
        ).replace(
            'C:\\Users\\Фёдор\\PycharmProjects\\Bushe\\MyIcons\\', ''
        )
        f.write(fixed_content)

    try:
        # Правильный вызов функции
        # processResourceFile принимает список файлов и опции
        result = pyrcc_main.processResourceFile(
            [temp_qrc],  # список файлов для обработки
            output_file,  # выходной файл
            False  # compress (сжимать или нет)
        )

        if result:
            print(f"✅ Ресурсы успешно скомпилированы в {output_file}")

            # Проверяем результат
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"📊 Размер файла: {size} байт")

                # Показываем первые несколько строк файла
                with open(output_file, 'r', encoding='utf-8') as f:
                    first_lines = f.readlines()[:5]
                    print("\n📄 Первые строки файла:")
                    for line in first_lines:
                        print(line.rstrip())
            else:
                print("❌ Файл не создан")
        else:
            print("❌ Ошибка при компиляции")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Удаляем временный файл
        if os.path.exists(temp_qrc):
            os.remove(temp_qrc)
            print("🧹 Временный файл удален")


if __name__ == "__main__":
    # Переходим в папку с ресурсами
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Рабочая папка: {os.getcwd()}")

    compile_resources()
    input("\nНажмите Enter для выхода...")