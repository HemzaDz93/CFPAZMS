#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
سكريبت إضافة الأعمدة الجديدة لدعم Multi-Tenant
Script to add new columns for Multi-Tenant support
"""

from app import create_app, db
from sqlalchemy import inspect, text
import sys

def add_columns_if_not_exists():
    """إضافة الأعمدة الجديدة إذا لم تكن موجودة"""
    
    app = create_app('development')
    
    with app.app_context():
        try:
            print("=" * 80)
            print("🔄 بدء إضافة الأعمدة الجديدة للـ Multi-Tenant")
            print("=" * 80)
            
            conn = db.engine.connect()
            inspector = inspect(db.engine)
            
            # قائمة الأعمدة المراد إضافتها
            columns_to_add = [
                # (اسم الجدول, اسم العمود, تعريف العمود)
                ('vocational_centers', 'meal_cost_per_unit', 'REAL DEFAULT 2.5'),
                ('vocational_centers', 'meal_alert_threshold', 'REAL DEFAULT 500.0'),
                ('vocational_centers', 'is_active', 'BOOLEAN DEFAULT 1'),
                ('vocational_centers', 'tax_id', 'VARCHAR(50)'),
                ('vocational_centers', 'registration_number', 'VARCHAR(100)'),
                ('vocational_centers', 'logo_path', 'VARCHAR(255)'),
                ('vocational_centers', 'website', 'VARCHAR(255)'),
                ('vocational_centers', 'notes', 'TEXT'),
                ('vocational_centers', 'created_by_id', 'VARCHAR(36)'),
                
                ('transactions', 'center_id', 'VARCHAR(36)'),
                ('recipes', 'center_id', 'VARCHAR(36)'),
                ('meal_records', 'center_id', 'VARCHAR(36)'),
                ('activity_logs', 'center_id', 'VARCHAR(36)'),
                ('suppliers', 'center_id', 'VARCHAR(36)'),
                ('purchase_orders', 'center_id', 'VARCHAR(36)'),
                ('asset_registrations', 'center_id', 'VARCHAR(36)'),
                ('user_permissions', 'center_id', 'VARCHAR(36)'),
            ]
            
            for table_name, column_name, column_def in columns_to_add:
                # التحقق من وجود الجدول
                if table_name not in inspector.get_table_names():
                    print(f"⚠️  الجدول {table_name} غير موجود")
                    continue
                
                # التحقق من وجود العمود
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                
                if column_name not in columns:
                    try:
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
                        conn.execute(text(alter_sql))
                        conn.commit()
                        print(f"✅ تم إضافة العمود {column_name} إلى {table_name}")
                    except Exception as e:
                        print(f"❌ خطأ في إضافة {column_name} إلى {table_name}: {str(e)}")
                else:
                    print(f"ℹ️  العمود {column_name} موجود بالفعل في {table_name}")
            
            conn.close()
            
            print("\n" + "=" * 80)
            print("✅ تم إضافة الأعمدة بنجاح!")
            print("=" * 80)
            
            return True
        
        except Exception as e:
            print(f"\n❌ خطأ: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = add_columns_if_not_exists()
    sys.exit(0 if success else 1)