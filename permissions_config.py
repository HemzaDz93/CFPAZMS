# قائمة الصلاحيات الشاملة للنظام
# Comprehensive Permissions Configuration

PERMISSIONS = {
    # === لوحة التحكم (Dashboard) ===
    'dashboard': {
        'name': 'لوحة التحكم',
        'permissions': {
            'dashboard_view': 'عرض لوحة التحكم الإدارية',
            'employee_dashboard_view': 'عرض لوحة التحكم الخاصة بالموظفين',
        }
    },
    
    # === إدارة المخزون (Inventory) ===
    'inventory': {
        'name': 'إدارة المخزون',
        'permissions': {
            'inventory_view_items': 'عرض قائمة الأصناف',
            'inventory_add_item': 'إضافة صنف جديد',
            'inventory_edit_item': 'تعديل الأصناف',
            'inventory_delete_item': 'حذف الأصناف',
            'inventory_view_categories': 'عرض التصنيفات',
            'inventory_add_category': 'إضافة تصنيف جديد',
            'inventory_edit_category': 'تعديل التصنيفات',
            'inventory_delete_category': 'حذف التصنيفات',
            'inventory_view_transactions': 'عرض العمليات',
            'inventory_add_transaction': 'تسجيل عملية جديدة',
            'inventory_edit_transaction': 'تعديل العمليات',
            'inventory_delete_transaction': 'حذف العمليات',
            'inventory_export': 'تصدير البيانات',
            # Advanced Features
            'inventory_view_warehouses': 'عرض المستودعات',
            'inventory_add_warehouse': 'إضافة مستودع جديد',
            'inventory_edit_warehouse': 'تعديل المستودعات',
            'inventory_view_warehouse_items': 'عرض مخزون المستودع',
            'inventory_view_counts': 'عرض عمليات الجرد الدوري',
            'inventory_add_count': 'إنشاء عملية جرد جديدة',
            'inventory_view_abc_analysis': 'عرض تحليل ABC',
            'inventory_edit_abc_analysis': 'تحديث تحليل ABC',
            'inventory_view_cost_analysis': 'عرض تحليل التكاليف',
            'inventory_edit_cost_analysis': 'تحديث تحليل التكاليف',
            'inventory_view_recommendations': 'عرض التوصيات',
            'inventory_approve_recommendation': 'الموافقة على التوصيات',
            'inventory_view_forecasts': 'عرض التنبؤات',
            'inventory_view_price_history': 'عرض سجل الأسعار',
            'inventory_view_supplier_performance': 'عرض أداء الموردين',
            'inventory_view_qrbarcode': 'عرض إعدادات QR/الباركود',
            'inventory_scan_qrbarcode': 'مسح QR/الباركود',
            'inventory_view_smart_alerts': 'عرض الإنذارات الذكية',
            'inventory_resolve_alert': 'حل الإنذارات',
        }
    },
    
    # === إدارة الموردين (Suppliers) ===
    'suppliers': {
        'name': 'إدارة الموردين',
        'permissions': {
            'suppliers_view': 'عرض قائمة الموردين',
            'suppliers_add': 'إضافة مورد جديد',
            'suppliers_edit': 'تعديل بيانات الموردين',
            'suppliers_delete': 'حذف الموردين',
            'suppliers_view_orders': 'عرض أوامر الشراء',
            'suppliers_add_order': 'إنشاء أمر شراء جديد',
            'suppliers_edit_order': 'تعديل أوامر الشراء',
            'suppliers_delete_order': 'حذف أوامر الشراء',
        }
    },
    
    # === إدارة الأصول (Equipment/Assets) ===
    'equipment': {
        'name': 'إدارة الأصول',
        'permissions': {
            'equipment_view_assets': 'عرض قائمة الأصول',
            'equipment_add_asset': 'تسجيل أصل جديد',
            'equipment_edit_asset': 'تعديل الأصول',
            'equipment_delete_asset': 'حذف الأصول',
            'equipment_view_issues': 'عرض تسليمات الأصول',
            'equipment_add_issue': 'تسجيل تسليم أصل',
            'equipment_return_issue': 'استرجاع أصل مسلم',
        }
    },
    
    # === إدارة المطعم (Restaurant) ===
    'restaurant': {
        'name': 'إدارة المطعم',
        'permissions': {
            'restaurant_view_recipes': 'عرض الوصفات',
            'restaurant_add_recipe': 'إضافة وصفة جديدة',
            'restaurant_edit_recipe': 'تعديل الوصفات',
            'restaurant_delete_recipe': 'حذف الوصفات',
            'restaurant_view_meals': 'عرض الوجبات اليومية',
            'restaurant_add_meal': 'تسجيل وجبة جديدة',
            'restaurant_edit_meal': 'تعديل الوجبات',
            'restaurant_delete_meal': 'حذف الوجبات',
            # === الميزات المتقدمة ===
            # إدارة الفاقد والهدر
            'restaurant_view_waste': 'عرض سجلات الفاقد والهدر',
            'restaurant_add_waste': 'تسجيل فاقد جديد',
            'restaurant_edit_waste': 'تعديل سجلات الفاقد',
            'restaurant_approve_waste': 'الموافقة على الفاقد',
            'restaurant_view_waste_reports': 'عرض تقارير الفاقد',
            # توقعات الطلب والاستهلاك
            'restaurant_view_forecast': 'عرض توقعات الطلب',
            'restaurant_add_forecast': 'إضافة توقع جديد',
            'restaurant_edit_forecast': 'تحديث التوقعات',
            'restaurant_view_forecast_reports': 'عرض تقارير التوقعات',
            # دعم ووجبات الموظفين
            'restaurant_view_subsidy': 'عرض الدعم والخصومات',
            'restaurant_add_subsidy': 'إضافة دعم جديد',
            'restaurant_edit_subsidy': 'تعديل الدعم',
            'restaurant_view_payroll': 'عرض ملخص الأجور والوجبات',
            # وجبات الموظفين (Employee Meals)
            'restaurant_view_employee_meals': 'عرض وجبات الموظفين',
            'restaurant_add_employee_meal': 'تسجيل وجبة موظف جديدة',
            'restaurant_edit_employee_meal': 'تعديل وجبات الموظفين',
            'restaurant_view_employee_alerts': 'عرض تنبيهات الوجبات',
            'restaurant_view_employee_receipt': 'عرض إيصالات الموظفين',
            'restaurant_view_employee_payments': 'عرض إدارة دفعات حقوق الوجبات',
            'restaurant_process_employee_payment': 'معالجة دفعات حقوق الوجبات',
            'restaurant_view_payment_history': 'عرض سجل الدفعات',
        }
    },
    
    # === التقارير (Reports) ===
    'reports': {
        'name': 'التقارير',
        'permissions': {
            'reports_inventory_movement': 'تقرير حركة المخزون',
            'reports_low_stock': 'تقرير الأصناف منخفضة المخزون',
            'reports_asset_inventory': 'تقرير جرد الأصول',
            'reports_meal_consumption': 'تقرير استهلاك الوجبات',
            'reports_print': 'طباعة التقارير',
            'reports_export': 'تصدير التقارير',
        }
    },
    
    # === إدارة النظام (Admin) ===
    'admin': {
        'name': 'إدارة النظام',
        'permissions': {
            'admin_view_users': 'عرض قائمة المستخدمين',
            'admin_add_user': 'إضافة مستخدم جديد',
            'admin_edit_user': 'تعديل بيانات المستخدمين',
            'admin_delete_user': 'حذف المستخدمين',
            'admin_manage_permissions': 'إدارة صلاحيات المستخدمين',
            'admin_view_activity_logs': 'عرض سجل النشاطات',
            'admin_manage_organization_settings': 'إعدادات المؤسسة والتنظيم',
        }
    },
    
    # === طلبات الموظفين (Employee Requests) ===
    'employee_requests': {
        'name': 'طلبات الموظفين',
        'permissions': {
            'requests_create': 'إنشاء طلب منتجات جديد',
            'requests_view_own': 'عرض طلباتي الشخصية',
            'requests_view_all': 'عرض جميع الطلبات',
            'requests_approve': 'الموافقة على الطلبات',
            'requests_reject': 'رفض الطلبات',
            'requests_manage': 'إدارة كاملة للطلبات',
        }
    },

    # === الميزات المتقدمة (Advanced Features) ===
    'advanced_features': {
        'name': 'الميزات المتقدمة',
        'permissions': {
            'advanced_notifications_view': 'عرض الإشعارات',
            'advanced_alerts_view': 'عرض التنبيهات',
            'advanced_api_keys_view': 'إدارة مفاتيح API',
            'advanced_approvals_view': 'عرض الموافقات',
            'advanced_budgets_view': 'عرض الميزانيات',
            'advanced_audit_logs_view': 'عرض سجلات التدقيق',
            'advanced_backups_view': 'إدارة النسخ الاحتياطية',
            'advanced_documents_view': 'عرض الوثائق',
            'advanced_kpi_view': 'إدارة مؤشرات الأداء',
        }
    },

    # === التنبيهات الذكية (Smart Alerts) ===
    'smart_alerts': {
        'name': 'التنبيهات الذكية',
        'permissions': {
            'alerts_view': 'عرض قائمة التنبيهات',
            'alerts_create': 'إنشاء تنبيه جديد',
            'alerts_edit': 'تعديل التنبيهات',
            'alerts_delete': 'حذف التنبيهات',
            'alerts_history': 'عرض سجل التنبيهات',
            'alerts_setup': 'إعدادات التنبيهات',
        }
    },

    # === التحليلات (Analytics) ===
    'analytics': {
        'name': 'التحليلات والتقارير المتقدمة',
        'permissions': {
            'analytics_view_dashboard': 'عرض لوحة تحكم التحليلات',
            'analytics_view_inventory': 'تحليلات المخزون',
            'analytics_view_suppliers': 'تحليلات الموردين',
            'analytics_view_trends': 'تحليل الاتجاهات والأنماط',
            'analytics_view_predictions': 'التنبؤات والتوقعات',
            'analytics_view_reports': 'التقارير التحليلية المخصصة',
            'analytics_export': 'تصدير بيانات التحليلات',
        }
    },

    # === مؤشرات الأداء (KPI) ===
    'kpi': {
        'name': 'مؤشرات الأداء الرئيسية',
        'permissions': {
            'kpi_view': 'عرض مؤشرات الأداء',
            'kpi_create': 'إنشاء مؤشر أداء جديد',
            'kpi_edit': 'تعديل مؤشرات الأداء',
            'kpi_delete': 'حذف مؤشرات الأداء',
            'kpi_track': 'تتبع مؤشرات الأداء',
        }
    },

    # === الأمان والحماية (Security) ===
    'security': {
        'name': 'الأمان والحماية',
        'permissions': {
            'mfa_setup': 'إعداد المصادقة متعددة العوامل',
            'login_attempts_view': 'عرض محاولات تسجيل الدخول',
            'api_keys_manage': 'إدارة مفاتيح API',
            'security_logs': 'عرض سجلات الأمان',
            'backup_manage': 'إدارة النسخ الاحتياطية',
            'backup_schedule': 'جدولة النسخ الاحتياطية',
        }
    },

    # === سير العمل والموافقات (Workflows) ===
    'workflows': {
        'name': 'سير العمل والموافقات',
        'permissions': {
            'workflows_view': 'عرض سير العمل',
            'workflows_create': 'إنشاء سير عمل جديد',
            'workflows_approve': 'الموافقة على الطلبات',
            'workflows_reject': 'رفض الطلبات',
            'workflows_manage': 'إدارة سير العمل',
        }
    },

    # === إدارة الميزانيات (Budgets) ===
    'budgets': {
        'name': 'إدارة الميزانيات',
        'permissions': {
            'budgets_view': 'عرض الميزانيات',
            'budgets_create': 'إنشاء ميزانية جديدة',
            'budgets_edit': 'تعديل الميزانيات',
            'budgets_delete': 'حذف الميزانيات',
            'budgets_track': 'تتبع الميزانيات',
        }
    },

    # === إدارة الفروع والأقسام (Branches & Departments) ===
    'organizational': {
        'name': 'إدارة الفروع والأقسام',
        'permissions': {
            'branches_view': 'عرض الفروع',
            'branches_create': 'إنشاء فرع جديد',
            'branches_edit': 'تعديل الفروع',
            'branches_delete': 'حذف الفروع',
            'departments_view': 'عرض الأقسام',
            'departments_create': 'إنشاء قسم جديد',
            'departments_edit': 'تعديل الأقسام',
            'departments_delete': 'حذف الأقسام',
        }
    },

    # === إدارة الوثائق (Document Management) ===
    'documents': {
        'name': 'إدارة الوثائق',
        'permissions': {
            'documents_view': 'عرض الوثائق',
            'documents_upload': 'رفع وثائق جديدة',
            'documents_edit': 'تعديل الوثائق',
            'documents_delete': 'حذف الوثائق',
            'documents_share': 'مشاركة الوثائق',
            'documents_approve': 'الموافقة على الوثائق',
        }
    },

    # === الإشعارات والتنبيهات (Notifications) ===
    'notifications': {
        'name': 'الإشعارات والتنبيهات',
        'permissions': {
            'notifications_view': 'عرض الإشعارات',
            'notifications_manage': 'إدارة الإشعارات',
            'notifications_config': 'تكوين قنوات الإشعارات',
        }
    },

    # === البريد الإلكتروني (Email Notifications) ===
    'email_notifications': {
        'name': 'البريد الإلكتروني والإشعارات',
        'permissions': {
            'email_notifications_view': 'عرض الإشعارات البريدية',
            'email_notifications_send': 'إرسال بريد إلكتروني',
            'email_notifications_manage': 'إدارة الإشعارات البريدية',
            'email_templates_manage': 'إدارة قوالب البريد',
            'email_logs_view': 'عرض سجلات البريد',
        }
    },

    # === أكواد QR والباركود (QR & Barcode) ===
    'qr_barcode': {
        'name': 'أكواد QR والباركود',
        'permissions': {
            'qr_barcode_generate': 'إنشاء أكواد QR والباركود',
            'qr_barcode_view': 'عرض الأكواد',
            'qr_barcode_scan': 'مسح الأكواد',
            'qr_barcode_manage': 'إدارة الأكواد',
            'qr_barcode_logs': 'عرض سجلات المسح',
        }
    },

    # === تصدير PDF (PDF Export) ===
    'pdf_export': {
        'name': 'تصدير PDF',
        'permissions': {
            'pdf_export_create': 'إنشاء تصديرات PDF',
            'pdf_export_view': 'عرض مهام التصدير',
            'pdf_export_download': 'تحميل ملفات PDF',
            'pdf_export_manage': 'إدارة مهام التصدير',
            'pdf_export_schedule': 'جدولة التصديرات',
        }
    },

    # === التحديثات الفورية (Real-time Updates) ===
    'realtime_updates': {
        'name': 'التحديثات الفورية',
        'permissions': {
            'realtime_view': 'عرض التحديثات الفورية',
            'realtime_manage': 'إدارة التحديثات',
            'realtime_dashboard': 'لوحة تحكم الوقت الفعلي',
        }
    },

    # === التكاملات الخارجية (External Integrations) ===
    'integrations': {
        'name': 'التكاملات الخارجية',
        'permissions': {
            'integrations_view': 'عرض التكاملات',
            'integrations_create': 'إنشاء تكامل جديد',
            'integrations_edit': 'تعديل التكاملات',
            'integrations_delete': 'حذف التكاملات',
            'integrations_test': 'اختبار التكاملات',
            'integrations_sync': 'مزامنة البيانات',
            'integrations_logs': 'عرض سجلات التكاملات',
        }
    },

    # === سجلات التدقيق المتقدمة (Advanced Audit Logs) ===
    'advanced_audit': {
        'name': 'سجلات التدقيق المتقدمة',
        'permissions': {
            'audit_logs_view': 'عرض سجلات التدقيق',
            'audit_logs_export': 'تصدير سجلات التدقيق',
            'audit_logs_config': 'تكوين سجلات التدقيق',
            'audit_logs_delete': 'حذف سجلات التدقيق',
        }
    },

    # === التطبيقات المحمولة (Mobile App) ===
    'mobile_app': {
        'name': 'التطبيقات المحمولة',
        'permissions': {
            'mobile_devices_view': 'عرض الأجهزة المحمولة',
            'mobile_devices_manage': 'إدارة الأجهزة',
            'mobile_api_keys_create': 'إنشاء مفاتيح API',
            'mobile_api_keys_manage': 'إدارة مفاتيح API',
            'mobile_push_notifications': 'إرسال إشعارات فورية',
        }
    },

    # === علامات الميزات (Feature Flags) ===
    'feature_management': {
        'name': 'إدارة الميزات',
        'permissions': {
            'feature_flags_view': 'عرض علامات الميزات',
            'feature_flags_create': 'إنشاء ميزة جديدة',
            'feature_flags_edit': 'تعديل الميزات',
            'feature_flags_delete': 'حذف الميزات',
            'feature_flags_enable': 'تفعيل/تعطيل الميزات',
        }
    },

    # === الميزات العشر الإضافية (New Advanced Inventory Features) ===
    
    # 1. تحليل ABC للمخزون (ABC Analysis)
    'inventory_abc_analysis': {
        'name': 'تحليل ABC للمخزون',
        'permissions': {
            'inventory_view_abc_analysis': 'عرض تحليل ABC',
            'inventory_edit_abc_analysis': 'تحديث تحليل ABC',
            'inventory_export_abc_analysis': 'تصدير تحليل ABC',
        }
    },

    # 2. عمليات الجرد (Inventory Counts)
    'inventory_counts': {
        'name': 'عمليات الجرد الدورية',
        'permissions': {
            'inventory_view_counts': 'عرض عمليات الجرد',
            'inventory_add_count': 'إنشاء عملية جرد جديدة',
            'inventory_edit_count': 'تحرير عمليات الجرد',
            'inventory_complete_count': 'إغلاق عملية جرد',
            'inventory_view_variance': 'عرض فروقات المخزون',
        }
    },

    # 3. إدارة المستودعات (Warehouse Management)
    'inventory_warehouses': {
        'name': 'إدارة المستودعات',
        'permissions': {
            'inventory_view_warehouses': 'عرض قائمة المستودعات',
            'inventory_add_warehouse': 'إضافة مستودع جديد',
            'inventory_edit_warehouse': 'تعديل بيانات المستودعات',
            'inventory_delete_warehouse': 'حذف المستودعات',
            'inventory_view_warehouse_items': 'عرض مخزون المستودع',
            'inventory_transfer_between_warehouses': 'تحويل المخزون بين المستودعات',
        }
    },

    # 4. تحليل تكاليف المخزون (Cost Analysis)
    'inventory_cost_analysis': {
        'name': 'تحليل تكاليف المخزون',
        'permissions': {
            'inventory_view_cost_analysis': 'عرض تحليل التكاليف',
            'inventory_edit_cost_analysis': 'تحديث تحليل التكاليف',
            'inventory_export_cost_analysis': 'تصدير تحليل التكاليف',
            'inventory_view_holding_costs': 'عرض تكاليف الاحتفاظ',
            'inventory_view_profitability': 'عرض الربحية',
        }
    },

    # 5. التوصيات والطلبات الموصى بها (Recommendations)
    'inventory_recommendations': {
        'name': 'توصيات الطلب والتنبيهات',
        'permissions': {
            'inventory_view_recommendations': 'عرض التوصيات',
            'inventory_approve_recommendation': 'الموافقة على التوصيات',
            'inventory_reject_recommendation': 'رفض التوصيات',
            'inventory_convert_to_order': 'تحويل التوصية لأمر شراء',
        }
    },

    # 6. التنبؤات (Forecasting)
    'inventory_forecasting': {
        'name': 'التنبؤات بالمخزون',
        'permissions': {
            'inventory_view_forecasts': 'عرض التنبؤات',
            'inventory_generate_forecasts': 'توليد التنبؤات',
            'inventory_view_stockout_predictions': 'عرض توقعات نفاد المخزون',
            'inventory_export_forecasts': 'تصدير التنبؤات',
        }
    },

    # 7. سجل الأسعار (Price History)
    'inventory_price_history': {
        'name': 'سجل الأسعار والتتبع',
        'permissions': {
            'inventory_view_price_history': 'عرض سجل الأسعار',
            'inventory_track_price_changes': 'تتبع تغييرات الأسعار',
            'inventory_analyze_price_trends': 'تحليل اتجاهات الأسعار',
            'inventory_export_price_history': 'تصدير سجل الأسعار',
        }
    },

    # 8. أداء الموردين (Supplier Performance)
    'inventory_supplier_performance': {
        'name': 'تقييم أداء الموردين',
        'permissions': {
            'inventory_view_supplier_performance': 'عرض تقييمات الموردين',
            'inventory_evaluate_supplier': 'تقييم الموردين',
            'inventory_view_supplier_metrics': 'عرض مؤشرات أداء الموردين',
            'inventory_compare_suppliers': 'مقارنة الموردين',
            'inventory_export_supplier_performance': 'تصدير تقييمات الموردين',
        }
    },

    # 9. QR/Barcode والمسح السريع (QR/Barcode Scanning)
    'inventory_qrbarcode': {
        'name': 'مسح QR/Barcode والحصر السريع',
        'permissions': {
            'inventory_view_qrbarcode': 'عرض إعدادات QR/Barcode',
            'inventory_scan_qrbarcode': 'مسح QR/Barcode',
            'inventory_generate_qr_codes': 'توليد رموز QR',
            'inventory_generate_barcodes': 'توليد Barcode',
            'inventory_view_scan_history': 'عرض سجل المسح',
        }
    },

    # 10. الإنذارات الذكية للمخزون (Smart Inventory Alerts)
    'inventory_smart_alerts': {
        'name': 'الإنذارات الذكية للمخزون',
        'permissions': {
            'inventory_view_smart_alerts': 'عرض الإنذارات الذكية',
            'inventory_configure_alerts': 'تكوين الإنذارات',
            'inventory_resolve_alert': 'حل الإنذارات',
            'inventory_view_alert_history': 'عرض سجل الإنذارات',
            'inventory_alert_notifications': 'إدارة قنوات الإشعارات',
        }
    },

    # === التقارير (Reports) ===
    'reports': {
        'name': 'التقارير والتحليلات',
        'permissions': {
            'reports_view': 'عرض صفحة التقارير',
            'reports_inventory_movement': 'عرض تقرير حركة المخزون',
            'reports_low_stock': 'عرض تقرير المخزون المنخفض',
            'reports_asset_inventory': 'عرض تقرير جرد الأصول',
            'reports_meal_consumption': 'عرض تقرير استهلاك الوجبات',
            'reports_generate': 'إنشاء تقارير جديدة',
            'reports_export_pdf': 'تصدير التقارير PDF',
            'reports_export_excel': 'تصدير التقارير Excel',
        }
    },
}


def get_all_permissions_flat():
    """الحصول على جميع الصلاحيات بصيغة مسطحة (قاموس)"""
    result = {}
    for category, data in PERMISSIONS.items():
        for perm_key, perm_name in data['permissions'].items():
            result[perm_key] = {
                'name': perm_name,
                'category': category,
                'category_name': data['name']
            }
    return result


def get_permissions_by_category():
    """الحصول على الصلاحيات مجمعة حسب الفئة"""
    return PERMISSIONS


def get_category_permissions(category):
    """الحصول على صلاحيات فئة معينة"""
    return PERMISSIONS.get(category, {}).get('permissions', {})