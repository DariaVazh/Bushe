# hr_learning_dashboard/widgets/learning_curve_chart.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QColor, QPen, QPainter
import pandas as pd


class LearningCurveChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel("Кривая обучения сотрудника")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        self.layout.addWidget(self.title)

        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(400)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.layout.addWidget(self.chart_view)

    def update_chart(self, df: pd.DataFrame, user_id: int = None):
        if df.empty:
            chart = QChart()
            chart.setTitle(f"Нет данных для пользователя #{user_id}" if user_id else "Нет данных")
            chart.setTheme(QChart.ChartThemeDark)
            self.chart_view.setChart(chart)
            return

        # Создаем серию
        series = QLineSeries()
        series.setName("Успешность")

        for _, row in df.iterrows():
            date_str = str(row['date'])
            qdatetime = QDateTime.fromString(date_str, "yyyy-MM-dd")
            if qdatetime.isValid():
                timestamp = qdatetime.toMSecsSinceEpoch()
                series.append(timestamp, row['daily_success_rate'] * 100)

        # Настраиваем график
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"Динамика успешности обучения - Пользователь #{user_id}")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTheme(QChart.ChartThemeDark)
        chart.setBackgroundVisible(False)

        # Ось X
        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd.MM")
        axis_x.setTitleText("Дата")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        # Ось Y
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTitleText("Успешность (%)")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        # Стиль линии
        pen = QPen(QColor(46, 204, 113))
        pen.setWidth(3)
        series.setPen(pen)
        series.setPointsVisible(True)

        self.chart_view.setChart(chart)