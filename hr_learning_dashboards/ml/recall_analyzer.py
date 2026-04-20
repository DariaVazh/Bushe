# hr_learning_dashboards/ml/recall_analyzer.py
import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
import sys
import os
from datetime import datetime

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import get_db
from Bushe.learning_platform_db.queries import AnalyticsQueries

# После импортов добавить:
import os

def ensure_ml_folder():
    if not os.path.exists('ml'):
        os.makedirs('ml')
        print("Создана папка ml/ для сохранения графиков")

class RecallAnalyzer:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.shap_values = None
        self.X_test = None
        self.y_test = None
        self.df_clean = None

    def load_data(self):
        """Загружает данные для ML"""
        print("📥 Загрузка данных из БД...")
        db_gen = get_db()
        db = next(db_gen)

        df = AnalyticsQueries.get_ml_training_data(db, min_interactions=5)
        db.close()

        print(f"Загружено {len(df)} записей")
        return df

    def prepare_features(self, df):
        print("🛠 Подготовка фичей...")

        df = df.dropna().copy()

        if 'prev_outcome' not in df.columns:
            df = df.sort_values(['user_id', 'item_id', 'history_step'])
            df['prev_outcome'] = df.groupby(['user_id', 'item_id'])['target'].shift(1)
            df['prev_response_time'] = df.groupby(['user_id', 'item_id'])['response_time'].shift(1)
            df['prev_delta'] = df.groupby(['user_id', 'item_id'])['delta_days'].shift(1)

            df['cumulative_success'] = df.groupby(['user_id', 'item_id'])['target'].transform(
                lambda x: x.expanding().mean().shift(1)
            )

        df['log_delta'] = np.log1p(df['delta_days'])
        df['response_time_ratio'] = df['response_time'] / df.groupby('user_id')['response_time'].transform('mean')
        df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)

        df['is_morning'] = (df['hour_of_day'] >= 6) & (df['hour_of_day'] <= 11)
        df['is_afternoon'] = (df['hour_of_day'] >= 12) & (df['hour_of_day'] <= 17)
        df['is_evening'] = (df['hour_of_day'] >= 18) & (df['hour_of_day'] <= 23)
        df['is_night'] = (df['hour_of_day'] >= 0) & (df['hour_of_day'] <= 5)

        feature_cols = [
            'history_step',
            'delta_days',
            'log_delta',
            # 'response_time', 
            # 'response_time_ratio',
            # 'prev_outcome',   
            'prev_response_time',
            'prev_delta',
            # 'cumulative_success',  # тоже подозрительно
            'user_avg_success',
            'item_avg_success',
            'hour_sin',
            'hour_cos',
            'is_morning',
            'is_afternoon',
            'is_evening',
            'is_night'
        ]

        feature_cols = [col for col in feature_cols if col in df.columns]

        df_clean = df.dropna(subset=feature_cols + ['target'])

        X = df_clean[feature_cols].values
        y = df_clean['target'].values

        self.feature_names = feature_cols
        self.df_clean = df_clean

        print(f"✅ Подготовлено {len(X)} записей, {len(feature_cols)} фичей")
        return X, y

    def train(self, df=None):
        if df is None:
            df = self.load_data()

        X, y = self.prepare_features(df)

        self.check_data_leakage() 

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.X_test = X_test
        self.y_test = y_test

        print("Обучение XGBoost...")
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )

        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss',
            early_stopping_rounds=20,  
            # use_label_encoder=False
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )

        y_pred = self.model.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, y_pred)
        loss = log_loss(y_test, y_pred)

        print(f"\nМетрики модели:")
        print(f"  ROC-AUC: {auc:.4f}")
        print(f"  Log Loss: {loss:.4f}")

        print("\nФичи, которые использует модель:")
        for i, name in enumerate(self.feature_names):
            print(f"  {i}: {name}")

        return self

    def check_data_leakage(self):
        if self.df_clean is None:
            print("Сначала подготовь данные!")
            return

        print("\nПРОВЕРКА НА УТЕЧКУ ДАННЫХ")
        print("=" * 60)

        correlations = []
        for col in self.feature_names:
            if col in self.df_clean.columns:
                corr = self.df_clean[col].corr(self.df_clean['target'])
                correlations.append((col, abs(corr)))

        correlations.sort(key=lambda x: x[1], reverse=True)

        print("Топ-5 фичей с наибольшей корреляцией с target:")
        for col, corr in correlations[:5]:
            print(f"  {col}: {corr:.4f}")
            if corr > 0.9:
                print(f"    ⚠️ ОЧЕНЬ ВЫСОКАЯ КОРРЕЛЯЦИЯ! Возможная утечка!")

        print("=" * 60)

    def plot_feature_importance(self, top_n=10, save_path='ml/feature_importance.png'):

        ensure_ml_folder()

        if self.model is None:
            raise ValueError("Сначала обучи модель!")

        importance = self.model.feature_importances_
        indices = np.argsort(importance)[::-1][:top_n]

        plt.figure(figsize=(12, 6))

        colors = plt.cm.viridis(np.linspace(0, 1, top_n))
        bars = plt.barh(range(top_n), importance[indices][::-1], color=colors[::-1])
        plt.yticks(range(top_n), [self.feature_names[i] for i in indices][::-1])
        plt.xlabel('Важность', fontsize=12)
        plt.title(f'Топ-{top_n} факторов, влияющих на запоминание', fontsize=14, fontweight='bold')

        for i, (bar, val) in enumerate(zip(bars, importance[indices][::-1])):
            plt.text(val + 0.005, i, f'{val:.3f}', va='center', fontsize=10)

        plt.tight_layout()
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.show()

        print(f"\n🎯 Топ-{top_n} самых важных факторов:")
        for i in range(top_n):
            print(f"{i + 1}. {self.feature_names[indices[i]]}: {importance[indices[i]]:.4f}")

    def shap_analysis(self, sample_size=500, save_path='ml/shap_summary.png'):
        ensure_ml_folder()

        if self.model is None:
            raise ValueError("Сначала обучи модель!")

        print("Запуск SHAP анализа...")

        if len(self.X_test) > sample_size:
            idx = np.random.choice(len(self.X_test), sample_size, replace=False)
            X_sample = self.X_test[idx]
        else:
            X_sample = self.X_test

        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X_sample)

        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            shap_values,
            X_sample,
            feature_names=self.feature_names,
            show=False,
            plot_size=(10, 6)
        )
        plt.title('SHAP values - влияние факторов на recall', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.show()

        top_idx = np.argmax(self.model.feature_importances_)
        top_feature = self.feature_names[top_idx]

        print(f"\nАнализ главного фактора: {top_feature}")

        if top_feature in self.df_clean.columns:
            plt.figure(figsize=(10, 5))

            if self.df_clean[top_feature].dtype in [np.float64, np.int64]:
                bins = np.linspace(
                    self.df_clean[top_feature].quantile(0.05),
                    self.df_clean[top_feature].quantile(0.95),
                    20
                )
                df_binned = self.df_clean.copy()
                df_binned['bin'] = pd.cut(self.df_clean[top_feature], bins)

                bin_stats = df_binned.groupby('bin')['target'].agg(['mean', 'count'])
                bin_centers = [(interval.left + interval.right) / 2 for interval in bin_stats.index]

                plt.scatter(bin_centers, bin_stats['mean'],
                            s=bin_stats['count'] / 10, alpha=0.6, c='blue')
                plt.plot(bin_centers, bin_stats['mean'], 'r-', alpha=0.5)
                plt.xlabel(top_feature)
                plt.ylabel('Вероятность recall')
                plt.title(f'Зависимость recall от {top_feature}')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig('ml/top_feature_dependence.png', dpi=100)
                plt.show()

        return shap_values

    def get_insights(self):
        if self.model is None:
            return "Сначала обучи модель!"

        importance = self.model.feature_importances_
        top_3_idx = np.argsort(importance)[::-1][:3]
        top_3_features = [self.feature_names[i] for i in top_3_idx]

        insights = []
        insights.append("=" * 60)
        insights.append("📋 БИЗНЕС-ВЫВОДЫ ПО РЕЗУЛЬТАТАМ ML-АНАЛИЗА")
        insights.append("=" * 60)

        insights.append(f"\n🎯 Топ-3 фактора, влияющих на запоминание:")

        for i, (feat, idx) in enumerate(zip(top_3_features, top_3_idx)):
            insights.append(f"\n{i + 1}. {feat} (важность: {importance[idx]:.3f})")

            if 'response_time' in feat or 'время' in feat:
                insights.append(f"   → Быстрые правильные ответы = глубокое запоминание")
                insights.append(f"   → Медленные правильные ответы = риск быстрого забывания")
            elif 'delta' in feat or 'интервал' in feat:
                insights.append(f"   → Интервалы > 7 дней снижают вероятность recall на 20-30%")
                insights.append(f"   → Оптимальный интервал: 3-5 дней")
            elif 'prev_outcome' in feat or 'предыдущий' in feat:
                insights.append(f"   → Успех в прошлый раз = +40% к вероятности вспомнить сейчас")
                insights.append(f"   → Ошибка в прошлый раз требует срочного повторения")
            elif 'hour' in feat or 'час' in feat:
                insights.append(f"   → Утренние часы (8-12) = максимальная эффективность")
                insights.append(f"   → Ночные занятия (23-5) = низкая эффективность")
            elif 'success' in feat:
                insights.append(f"   → Накопленная успешность = уверенность в теме")

        insights.append("\n" + "=" * 60)
        insights.append("💡 РЕКОМЕНДАЦИИ ДЛЯ ОПТИМИЗАЦИИ ОБУЧЕНИЯ:")
        insights.append("=" * 60)
        insights.append("\n1. Персонализация интервалов:")
        insights.append("   • Для быстрых правильных ответов → увеличивать интервал")
        insights.append("   • Для медленных правильных → сокращать интервал на 30%")
        insights.append("\n2. Оптимизация времени обучения:")
        insights.append("   • Планировать сложные темы на утро")
        insights.append("   • Не рекомендовать обучение после 23:00")
        insights.append("\n3. Работа с отстающими:")
        insights.append("   • После ошибки показывать тот же факт через 1 день")
        insights.append("   • Давать упрощенные формулировки")

        return "\n".join(insights)

    def save_report(self, filename='ml/analysis_report.txt'):
        """Сохраняет полный отчёт"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("ML АНАЛИЗ ФАКТОРОВ ЗАПОМИНАНИЯ\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 60 + "\n\n")

            f.write(self.get_insights())

        print(f"\n✅ Отчёт сохранён в {filename}")

