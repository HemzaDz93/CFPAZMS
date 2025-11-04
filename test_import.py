#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify imports"""

try:
    from app import create_app
    print("✓ Successfully imported create_app")
    
    app = create_app()
    print("✓ Successfully created app instance")
    
    from routes.advanced_features_v2 import advanced_v2_bp
    print("✓ Successfully imported advanced_v2_bp")
    
    from models import (
        EmailNotification, EmailTemplate, QRBarcode, QRBarcodeLog,
        PDFExportJob, RealTimeEvent, ExternalIntegration, IntegrationLog,
        AdvancedAuditLog, MobileDevice, MobileAPIKey, FeatureFlag
    )
    print("✓ Successfully imported all new models")
    
    print("\n✓✓✓ All imports successful! ✓✓✓")
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()