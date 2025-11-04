"""
نظام التحليلات المتقدمة والتنبؤات
"""

import pandas as pd
import numpy as np
try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except Exception:
    # sklearn not available in this environment; related features will be disabled
    train_test_split = None
    StandardScaler = None
    RandomForestRegressor = None
    mean_squared_error = None
    r2_score = None
    SKLEARN_AVAILABLE = False
try:
    from prophet import Prophet
except Exception:
    Prophet = None
from datetime import datetime, timedelta
try:
    import tensorflow as tf
except Exception:
    tf = None

from sqlalchemy import text
from models import db, Transaction as InventoryTransaction, Item as InventoryItem, Supplier, PurchaseOrder
from collections import defaultdict

class AnalyticsEngine:
    """محرك التحليلات والتنبؤات"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.prophet_models = {}
        
    def prepare_inventory_data(self, days=365):
        """تحضير بيانات المخزون للتحليل"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # جلب بيانات المعاملات
        transactions = db.session.query(
            InventoryTransaction.item_id,
            InventoryTransaction.quantity,
            InventoryTransaction.transaction_type,
            InventoryTransaction.timestamp,
            InventoryItem.name,
            InventoryItem.unit_price
        ).join(
            InventoryItem,
            InventoryTransaction.item_id == InventoryItem.id
        ).filter(
            InventoryTransaction.timestamp >= cutoff_date
        ).all()
        
        # تحويل إلى DataFrame
        df = pd.DataFrame([{
            'item_id': t.item_id,
            'item_name': t.name,
            'quantity': t.quantity if t.transaction_type == 'in' else -t.quantity,
            'amount': t.quantity * t.unit_price,
            'timestamp': t.timestamp,
            'day_of_week': t.timestamp.dayofweek,
            'month': t.timestamp.month,
            'year': t.timestamp.year
        } for t in transactions])
        
        return df
    
    def train_inventory_prediction_model(self, item_id):
        """تدريب نموذج التنبؤ بالمخزون"""
        df = self.prepare_inventory_data()
        item_data = df[df['item_id'] == item_id]
        
        if len(item_data) < 30:  # نحتاج لبيانات كافية
            return False
        
        # إعداد البيانات للتنبؤ
        X = item_data[['day_of_week', 'month', 'year']].values
        y = item_data['quantity'].values
        
        # تقسيم البيانات
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # تطبيع البيانات
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # تدريب النموذج
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # تقييم النموذج
        y_pred = model.predict(X_test_scaled)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # حفظ النموذج
        self.models[item_id] = model
        self.scalers[item_id] = scaler
        
        return {
            'r2_score': r2,
            'rmse': rmse,
            'training_size': len(X_train)
        }
    
    def predict_inventory_demand(self, item_id, days=30):
        """التنبؤ بالطلب المستقبلي"""
        if item_id not in self.models:
            if not self.train_inventory_prediction_model(item_id):
                return None
        
        # توليد التواريخ المستقبلية
        future_dates = pd.date_range(
            start=datetime.now(),
            periods=days,
            freq='D'
        )
        
        # إعداد بيانات التنبؤ
        X_future = np.array([
            [d.dayofweek, d.month, d.year] for d in future_dates
        ])
        
        # التنبؤ
        X_future_scaled = self.scalers[item_id].transform(X_future)
        predictions = self.models[item_id].predict(X_future_scaled)
        
        return pd.DataFrame({
            'date': future_dates,
            'predicted_demand': predictions
        })
    
    def train_prophet_model(self, item_id):
        """تدريب نموذج Prophet للتنبؤ"""
        if Prophet is None:
            # Prophet غير متوفر في البيئة الحالية
            return False

        df = self.prepare_inventory_data()
        item_data = df[df['item_id'] == item_id]
        
        if len(item_data) < 30:
            return False
        
        # إعداد البيانات لـ Prophet
        prophet_df = pd.DataFrame({
            'ds': item_data['timestamp'],
            'y': item_data['quantity']
        })
        
        # تدريب النموذج
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        model.fit(prophet_df)
        
        self.prophet_models[item_id] = model
        return True
    
    def predict_seasonal_trends(self, item_id, days=90):
        """التنبؤ بالاتجاهات الموسمية"""
        if Prophet is None:
            return None

        if item_id not in self.prophet_models:
            if not self.train_prophet_model(item_id):
                return None
        
        # إنشاء تواريخ التنبؤ
        future = self.prophet_models[item_id].make_future_dataframe(
            periods=days,
            freq='D'
        )
        
        # التنبؤ
        forecast = self.prophet_models[item_id].predict(future)
        
        return {
            'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
            'components': self.prophet_models[item_id].plot_components(forecast)
        }
    
    def analyze_supplier_performance(self, days=180):
        """تحليل أداء الموردين"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # جلب بيانات أوامر الشراء
        orders = db.session.query(
            PurchaseOrder.supplier_id,
            PurchaseOrder.order_date,
            PurchaseOrder.delivery_date,
            PurchaseOrder.status,
            PurchaseOrder.total_amount,
            Supplier.name
        ).join(
            Supplier,
            PurchaseOrder.supplier_id == Supplier.id
        ).filter(
            PurchaseOrder.order_date >= cutoff_date
        ).all()
        
        # تحليل الأداء
        supplier_metrics = defaultdict(lambda: {
            'total_orders': 0,
            'on_time_delivery': 0,
            'late_delivery': 0,
            'total_amount': 0,
            'avg_delivery_time': []
        })
        
        for order in orders:
            metrics = supplier_metrics[order.supplier_id]
            metrics['total_orders'] += 1
            metrics['total_amount'] += order.total_amount
            
            if order.delivery_date:
                delivery_time = (order.delivery_date - order.order_date).days
                metrics['avg_delivery_time'].append(delivery_time)
                
                if delivery_time <= 7:  # معيار التسليم في الوقت المحدد
                    metrics['on_time_delivery'] += 1
                else:
                    metrics['late_delivery'] += 1
        
        # حساب المقاييس النهائية
        results = []
        for supplier_id, metrics in supplier_metrics.items():
            avg_delivery_time = np.mean(metrics['avg_delivery_time']) if metrics['avg_delivery_time'] else 0
            on_time_ratio = metrics['on_time_delivery'] / metrics['total_orders'] if metrics['total_orders'] > 0 else 0
            
            results.append({
                'supplier_id': supplier_id,
                'supplier_name': next(o.name for o in orders if o.supplier_id == supplier_id),
                'total_orders': metrics['total_orders'],
                'total_amount': metrics['total_amount'],
                'avg_delivery_time': avg_delivery_time,
                'on_time_delivery_ratio': on_time_ratio,
                'performance_score': (on_time_ratio * 0.7 + (1 - min(avg_delivery_time / 14, 1)) * 0.3) * 100
            })
        
        return pd.DataFrame(results)
    
    def generate_insights(self):
        """توليد رؤى وتوصيات ذكية"""
        insights = []
        
        # تحليل المخزون
        low_stock_items = self.analyze_low_stock_items()
        if low_stock_items:
            insights.append({
                'type': 'warning',
                'category': 'inventory',
                'title': 'تنبيه المخزون المنخفض',
                'items': low_stock_items
            })
        
        # تحليل الموردين
        supplier_performance = self.analyze_supplier_performance()
        poor_performers = supplier_performance[
            supplier_performance['performance_score'] < 70
        ]
        if not poor_performers.empty:
            insights.append({
                'type': 'alert',
                'category': 'suppliers',
                'title': 'أداء الموردين المنخفض',
                'items': poor_performers.to_dict('records')
            })
        
        # تحليل الاتجاهات
        trending_items = self.analyze_trending_items()
        if trending_items:
            insights.append({
                'type': 'info',
                'category': 'trends',
                'title': 'الأصناف الأكثر طلباً',
                'items': trending_items
            })
        
        return insights
    
    def analyze_low_stock_items(self):
        """تحليل الأصناف منخفضة المخزون"""
        items = db.session.query(InventoryItem).filter(
            InventoryItem.current_quantity <= InventoryItem.reorder_point
        ).all()
        
        return [{
            'id': item.id,
            'name': item.name,
            'current_quantity': item.current_quantity,
            'reorder_point': item.reorder_point,
            'unit': item.unit,
            'supplier_id': item.supplier_id
        } for item in items]
    
    def analyze_trending_items(self, days=30):
        """تحليل الأصناف الأكثر طلباً"""
        df = self.prepare_inventory_data(days)
        
        # تجميع البيانات حسب الصنف
        item_trends = df.groupby('item_id').agg({
            'quantity': 'sum',
            'amount': 'sum',
            'item_name': 'first'
        }).reset_index()
        
        # ترتيب الأصناف حسب الكمية
        trending = item_trends.nlargest(10, 'quantity')
        
        return trending.to_dict('records')
    
    def generate_analytics_report(self, report_type='daily'):
        """توليد تقرير تحليلي"""
        if report_type == 'daily':
            period = 1
        elif report_type == 'weekly':
            period = 7
        elif report_type == 'monthly':
            period = 30
        else:
            period = 90  # quarterly
        
        report = {
            'period': report_type,
            'generated_at': datetime.now(),
            'inventory_summary': self.get_inventory_summary(period),
            'transactions_summary': self.get_transactions_summary(period),
            'supplier_performance': self.analyze_supplier_performance(period),
            'trends': self.analyze_trending_items(period),
            'predictions': self.get_demand_predictions(),
            'insights': self.generate_insights()
        }
        
        return report
    
    def get_inventory_summary(self, days):
        """ملخص المخزون"""
        items = db.session.query(InventoryItem).all()
        
        summary = {
            'total_items': len(items),
            'total_value': sum(item.current_quantity * item.unit_price for item in items),
            'low_stock_items': len([item for item in items if item.current_quantity <= item.reorder_point]),
            'out_of_stock_items': len([item for item in items if item.current_quantity == 0])
        }
        
        return summary
    
    def get_transactions_summary(self, days):
        """ملخص المعاملات"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        transactions = db.session.query(InventoryTransaction).filter(
            InventoryTransaction.timestamp >= cutoff_date
        ).all()
        
        summary = {
            'total_transactions': len(transactions),
            'incoming': len([t for t in transactions if t.transaction_type == 'in']),
            'outgoing': len([t for t in transactions if t.transaction_type == 'out']),
            'total_value': sum(t.quantity * t.unit_price for t in transactions)
        }
        
        return summary
    
    def get_demand_predictions(self):
        """توقعات الطلب"""
        items = db.session.query(InventoryItem).all()
        predictions = {}
        
        for item in items:
            pred = self.predict_inventory_demand(item.id)
            if pred is not None:
                predictions[item.id] = {
                    'item_name': item.name,
                    'predictions': pred.to_dict('records')
                }
        
        return predictions