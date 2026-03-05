# Временный скрипт test_ml.py
from recall_analyzer import RecallAnalyzer

analyzer = RecallAnalyzer()
analyzer.train()                    # обучить модель
analyzer.plot_feature_importance()  # показать важность признаков
analyzer.shap_analysis()            # SHAP анализ
print(analyzer.get_insights())      # бизнес-выводы
analyzer.save_report()              # сохранить отчёт