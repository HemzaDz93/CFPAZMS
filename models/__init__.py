"""
نماذج قاعدة البيانات
Database Models

هذا الملف يوفر نقطة وصول موحدة لجميع نماذج قاعدة البيانات
"""

import sys
import os
import importlib.util

# Import db and core models from parent models.py
spec = importlib.util.spec_from_file_location("models_core", 
        os.path.join(os.path.dirname(__file__), '..', 'models.py'))
models_core = importlib.util.module_from_spec(spec)
sys.modules['models_core'] = models_core
spec.loader.exec_module(models_core)

# Re-export everything from models.py
db = models_core.db

# Enums
UserRole = models_core.UserRole
ItemCategory = models_core.ItemCategory
ItemStatus = models_core.ItemStatus
TransactionType = models_core.TransactionType
VocationalCenterStatus = models_core.VocationalCenterStatus
TrainingLevel = models_core.TrainingLevel
TraineeStatus = models_core.TraineeStatus
EquipmentCondition = models_core.EquipmentCondition
ResourceType = models_core.ResourceType
TransferRequestStatus = models_core.TransferRequestStatus
MaintenanceType = models_core.MaintenanceType
MaintenanceStatus = models_core.MaintenanceStatus

# Models - Core
OrganizationSettings = models_core.OrganizationSettings
User = models_core.User
UserPermission = models_core.UserPermission
ItemCategory_Model = models_core.ItemCategory_Model
Item = models_core.Item
Supplier = models_core.Supplier
PurchaseOrder = models_core.PurchaseOrder
PurchaseOrderItem = models_core.PurchaseOrderItem
Transaction = models_core.Transaction
AssetRegistration = models_core.AssetRegistration
AssetScanLog = models_core.AssetScanLog
ItemIssue = models_core.ItemIssue
Recipe = models_core.Recipe
RecipeIngredient = models_core.RecipeIngredient
MealRecord = models_core.MealRecord
ActivityLog = models_core.ActivityLog
Notification = models_core.Notification
Alert = models_core.Alert

# Models - Workflow & API
WorkflowApproval = models_core.WorkflowApproval
WorkflowStep = models_core.WorkflowStep
APIKey = models_core.APIKey
UserMFASettings = models_core.UserMFASettings
LoginAttempt = models_core.LoginAttempt

# Models - Reports & Budgeting
Report = models_core.Report
ReportSchedule = models_core.ReportSchedule
Budget = models_core.Budget
BudgetTransaction = models_core.BudgetTransaction

# Models - Backup & Analytics
Backup = models_core.Backup
BackupSchedule = models_core.BackupSchedule
Analytics = models_core.Analytics
Forecast = models_core.Forecast

# Models - Organization Structure
Branch = models_core.Branch
Department = models_core.Department

# Models - Units & Conversion
UnitOfMeasure = models_core.UnitOfMeasure
UnitConversion = models_core.UnitConversion

# Models - Audit & Filters
DetailedAuditLog = models_core.DetailedAuditLog
SavedFilter = models_core.SavedFilter
FullTextIndex = models_core.FullTextIndex

# Models - Mobile & Push
MobileDevice = models_core.MobileDevice
MobileNotification = models_core.MobileNotification
PushSubscription = models_core.PushSubscription
OfflineData = models_core.OfflineData

# Models - QR & Scanning
QRCodeMapping = models_core.QRCodeMapping

# Models - Dashboard & KPI
DashboardMetric = models_core.DashboardMetric
AnalyticsReport = models_core.AnalyticsReport
KPITracker = models_core.KPITracker
SmartAlert = models_core.SmartAlert
AlertHistory = models_core.AlertHistory

# Models - Documents
Document = models_core.Document
DocumentVersion = models_core.DocumentVersion
DocumentComment = models_core.DocumentComment

# Models - Email
EmailNotification = models_core.EmailNotification
EmailTemplate = models_core.EmailTemplate

# Models - QR/Barcode & Export
QRBarcode = models_core.QRBarcode
QRBarcodeLog = models_core.QRBarcodeLog
PDFExportJob = models_core.PDFExportJob

# Models - Real-time & Integration
RealTimeEvent = models_core.RealTimeEvent
ExternalIntegration = models_core.ExternalIntegration
IntegrationLog = models_core.IntegrationLog

# Models - Advanced Audit & Features
AdvancedAuditLog = models_core.AdvancedAuditLog
MobileAPIKey = models_core.MobileAPIKey
FeatureFlag = models_core.FeatureFlag

# Models - Stock & Inventory Analysis
StockRequest = models_core.StockRequest
StockRequestItem = models_core.StockRequestItem
InventoryABCAnalysis = models_core.InventoryABCAnalysis
InventoryCount = models_core.InventoryCount
InventoryCountItem = models_core.InventoryCountItem
Warehouse = models_core.Warehouse
WarehouseInventory = models_core.WarehouseInventory
InventoryCostAnalysis = models_core.InventoryCostAnalysis
RecommendedOrder = models_core.RecommendedOrder
InventoryForecast = models_core.InventoryForecast
PriceHistory = models_core.PriceHistory
SupplierPerformance = models_core.SupplierPerformance

# Models - QR Barcode Config
QRBarcodeConfig = models_core.QRBarcodeConfig
QRBarcodeScan = models_core.QRBarcodeScan

# Models - Inventory Alerts & Waste
SmartInventoryAlert = models_core.SmartInventoryAlert
FoodWaste = models_core.FoodWaste
WasteAnalysis = models_core.WasteAnalysis

# Models - Demand & Employee Meals
DemandForecast = models_core.DemandForecast
DemandAnalysis = models_core.DemandAnalysis
EmployeeMealSubsidy = models_core.EmployeeMealSubsidy
EmployeeMealTransaction = models_core.EmployeeMealTransaction
MealPayrollIntegration = models_core.MealPayrollIntegration
EmployeeMealAlert = models_core.EmployeeMealAlert

# Models - Vocational Centers & Training
VocationalCenter = models_core.VocationalCenter
TrainingProgram = models_core.TrainingProgram
Trainee = models_core.Trainee

# Models - Equipment Transfer & Maintenance
EquipmentTransferRequest = models_core.EquipmentTransferRequest
MaintenanceLog = models_core.MaintenanceLog

__all__ = [
    'db',
    # Enums
    'UserRole',
    'ItemCategory',
    'ItemStatus',
    'TransactionType',
    'VocationalCenterStatus',
    'TrainingLevel',
    'TraineeStatus',
    'EquipmentCondition',
    'ResourceType',
    'TransferRequestStatus',
    'MaintenanceType',
    'MaintenanceStatus',
    # Core Models
    'OrganizationSettings',
    'User',
    'UserPermission',
    'ItemCategory_Model',
    'Item',
    'Supplier',
    'PurchaseOrder',
    'PurchaseOrderItem',
    'Transaction',
    'AssetRegistration',
    'AssetScanLog',
    'ItemIssue',
    'Recipe',
    'RecipeIngredient',
    'MealRecord',
    'ActivityLog',
    'Notification',
    'Alert',
    # Workflow & API
    'WorkflowApproval',
    'WorkflowStep',
    'APIKey',
    'UserMFASettings',
    'LoginAttempt',
    # Reports & Budgeting
    'Report',
    'ReportSchedule',
    'Budget',
    'BudgetTransaction',
    # Backup & Analytics
    'Backup',
    'BackupSchedule',
    'Analytics',
    'Forecast',
    # Organization Structure
    'Branch',
    'Department',
    # Units & Conversion
    'UnitOfMeasure',
    'UnitConversion',
    # Audit & Filters
    'DetailedAuditLog',
    'SavedFilter',
    'FullTextIndex',
    # Mobile & Push
    'MobileDevice',
    'MobileNotification',
    'PushSubscription',
    'OfflineData',
    # QR & Scanning
    'QRCodeMapping',
    # Dashboard & KPI
    'DashboardMetric',
    'AnalyticsReport',
    'KPITracker',
    'SmartAlert',
    'AlertHistory',
    # Documents
    'Document',
    'DocumentVersion',
    'DocumentComment',
    # Email
    'EmailNotification',
    'EmailTemplate',
    # QR/Barcode & Export
    'QRBarcode',
    'QRBarcodeLog',
    'PDFExportJob',
    # Real-time & Integration
    'RealTimeEvent',
    'ExternalIntegration',
    'IntegrationLog',
    # Advanced Audit & Features
    'AdvancedAuditLog',
    'MobileAPIKey',
    'FeatureFlag',
    # Stock & Inventory Analysis
    'StockRequest',
    'StockRequestItem',
    'InventoryABCAnalysis',
    'InventoryCount',
    'InventoryCountItem',
    'Warehouse',
    'WarehouseInventory',
    'InventoryCostAnalysis',
    'RecommendedOrder',
    'InventoryForecast',
    'PriceHistory',
    'SupplierPerformance',
    # QR Barcode Config
    'QRBarcodeConfig',
    'QRBarcodeScan',
    # Inventory Alerts & Waste
    'SmartInventoryAlert',
    'FoodWaste',
    'WasteAnalysis',
    # Demand & Employee Meals
    'DemandForecast',
    'DemandAnalysis',
    'EmployeeMealSubsidy',
    'EmployeeMealTransaction',
    'MealPayrollIntegration',
    'EmployeeMealAlert',
    # Vocational Centers & Training
    'VocationalCenter',
    'TrainingProgram',
    'Trainee',
    # Equipment Transfer & Maintenance
    'EquipmentTransferRequest',
    'MaintenanceLog',
]