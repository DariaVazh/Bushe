# setup.py
from setuptools import setup, find_packages

setup(
    name="learning_platform_db",           # Имя пакета
    version="0.1.0",                        # Версия
    packages=find_packages(),                # Находит все пакеты (папки с __init__.py)
    install_requires=[                       # Зависимости
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pandas>=1.5.0",
    ],
    author="Ваше имя",
    author_email="ваш@email.com",
    description="База данных для платформы обучения",
    python_requires=">=3.8",
)