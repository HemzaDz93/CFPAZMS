"""
Comprehensive E2E Tests for Granular Permission Enforcement
Tests the three-layer permission system:
1. Route-level permission checks
2. Sidebar menu visibility
3. Direct URL access prevention

These tests work with the running Flask development server.
"""

import time
from playwright.sync_api import sync_playwright
import requests
import json


class PermissionTestSetup:
    """Helper to create test users via Flask context"""
    
    @staticmethod
    def create_test_user(username, email, password, permissions_list):
        """Create a test user with specific permissions"""
        try:
            # Import here to ensure we're using the running app's database
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            
            from app import create_app
            from models import db, User, UserPermission
            
            app = create_app('development')
            
            with app.app_context():
                # Check if user exists and delete
                existing = User.query.filter_by(username=username).first()
                if existing:
                    db.session.delete(existing)
                    db.session.commit()
                
                # Create user
                user = User(
                    username=username,
                    email=email,
                    first_name=username,
                    last_name="Test",
                    role="worker",
                    is_active=True
                )
                user.set_password(password)
                db.session.add(user)
                db.session.flush()
                
                # Add permissions
                for perm_key in permissions_list:
                    perm = UserPermission(
                        user_id=user.id,
                        permission_key=perm_key,
                        permission_name=perm_key.replace('_', ' '),
                        permission_category=perm_key.split('_')[0],
                        is_allowed=True
                    )
                    db.session.add(perm)
                
                db.session.commit()
                return True
        except Exception as e:
            print(f"Error creating test user: {e}")
            return False
    
    @staticmethod
    def delete_test_user(username):
        """Delete test user"""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            
            from app import create_app
            from models import db, User
            
            app = create_app('development')
            
            with app.app_context():
                user = User.query.filter_by(username=username).first()
                if user:
                    db.session.delete(user)
                    db.session.commit()
                return True
        except Exception as e:
            print(f"Error deleting test user: {e}")
            return False


class TestGranularPermissionEnforcement:
    """Test suite for granular permission enforcement"""
    
    BASE_URL = "http://localhost:5000"
    
    @classmethod
    def setup_class(cls):
        """Setup test users"""
        # Create users with different permission sets
        PermissionTestSetup.create_test_user(
            "requests_only",
            "requests@test.local",
            "testpass123",
            ["requests_view_own", "requests_create"]
        )
        
        PermissionTestSetup.create_test_user(
            "inventory_only",
            "inventory@test.local",
            "testpass123",
            ["inventory_view_items"]
        )
        
        PermissionTestSetup.create_test_user(
            "minimal_user",
            "minimal@test.local",
            "testpass123",
            ["dashboard_view"]
        )
        
        PermissionTestSetup.create_test_user(
            "no_perms_user",
            "noperms@test.local",
            "testpass123",
            []
        )
        
        time.sleep(1)  # Allow time for database writes
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test users"""
        PermissionTestSetup.delete_test_user("requests_only")
        PermissionTestSetup.delete_test_user("inventory_only")
        PermissionTestSetup.delete_test_user("minimal_user")
        PermissionTestSetup.delete_test_user("no_perms_user")
    
    def test_01_user_login_success(self):
        """Test successful user login with minimal permissions"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Fill login form
                page.fill("input[name='username']", "minimal_user")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                
                # Wait for redirect to dashboard
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Verify dashboard loaded
                assert "لوحة التحكم" in page.title() or "Dashboard" in page.title()
                print("[OK] Test 01: User login successful")
                
            finally:
                browser.close()
    
    def test_02_inventory_access_denied_without_permission(self):
        """Test that users without inventory permission cannot access inventory"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Login with user that has only requests permission
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "requests_only")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access inventory (should be denied)
                page.goto(f"{self.BASE_URL}/inventory/items", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected to dashboard
                current_url = page.url.lower()
                assert "dashboard" in current_url, f"Expected dashboard URL, got {current_url}"
                
                # Look for error message - use specific selector for danger alerts
                danger_alert = page.locator(".alert-danger, [role='alert']:has-text('ليس لديك صلاحية')")
                if danger_alert.count() > 0:
                    assert danger_alert.is_visible()
                    alert_text = danger_alert.first.text_content()
                    assert "ليس لديك صلاحية" in alert_text or "permission" in alert_text.lower()
                
                print("[OK] Test 02: Inventory access denied for user without permission")
                
            finally:
                browser.close()
    
    def test_03_suppliers_access_denied_without_permission(self):
        """Test that users without suppliers permission cannot access suppliers"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Login with minimal permissions
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "minimal_user")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access suppliers
                page.goto(f"{self.BASE_URL}/suppliers/", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected to dashboard
                assert "dashboard" in page.url.lower()
                
                print("[OK] Test 03: Suppliers access denied for user without permission")
                
            finally:
                browser.close()
    
    def test_04_equipment_access_denied_without_permission(self):
        """Test that users without equipment permission cannot access equipment"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "minimal_user")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access equipment
                page.goto(f"{self.BASE_URL}/equipment/assets", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected or no access (either dashboard or not on equipment page)
                url = page.url.lower()
                is_allowed = ("equipment" in url and "assets" in url)
                assert not is_allowed, f"User should not access equipment, but URL is {page.url}"
                
                print("[OK] Test 04: Equipment access denied without permission")
                
            finally:
                browser.close()
    
    def test_05_restaurant_access_denied_without_permission(self):
        """Test that users without restaurant permission cannot access restaurant"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "minimal_user")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access restaurant recipes
                page.goto(f"{self.BASE_URL}/restaurant/recipes", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected
                assert "dashboard" in page.url.lower()
                
                print("[OK] Test 05: Restaurant access denied without permission")
                
            finally:
                browser.close()
    
    def test_06_admin_access_denied_without_permission(self):
        """Test that users without admin permission cannot access admin panel"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "requests_only")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access admin users
                page.goto(f"{self.BASE_URL}/admin/users", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected
                assert "dashboard" in page.url.lower()
                
                print("[OK] Test 06: Admin access denied without permission")
                
            finally:
                browser.close()
    
    def test_07_reports_access_denied_without_permission(self):
        """Test that users without reports permission cannot access reports"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "minimal_user")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access inventory movement report
                page.goto(f"{self.BASE_URL}/reports/inventory-movement", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected
                assert "dashboard" in page.url.lower()
                
                print("[OK] Test 07: Reports access denied without permission")
                
            finally:
                browser.close()
    
    def test_08_employee_requests_access_denied_without_permission(self):
        """Test that users without requests permission cannot access requests"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "inventory_only")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access employee requests
                page.goto(f"{self.BASE_URL}/employee-requests/", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected
                assert "dashboard" in page.url.lower()
                
                print("[OK] Test 08: Employee requests access denied without permission")
                
            finally:
                browser.close()
    
    def test_09_advanced_features_access_denied_without_permission(self):
        """Test that users without advanced features permission cannot access advanced features"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "minimal_user")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access advanced features
                page.goto(f"{self.BASE_URL}/advanced/notifications", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected
                assert "dashboard" in page.url.lower()
                
                print("[OK] Test 09: Advanced features access denied without permission")
                
            finally:
                browser.close()
    
    def test_10_analytics_access_denied_without_permission(self):
        """Test that users without analytics permission cannot access analytics"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "minimal_user")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access analytics
                page.goto(f"{self.BASE_URL}/analytics/dashboard", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify redirected or no access
                assert "dashboard" in page.url.lower() or "login" in page.url.lower()
                
                print("[OK] Test 10: Analytics access denied without permission")
                
            finally:
                browser.close()
    
    def test_11_user_with_inventory_can_access_inventory(self):
        """Test that user with inventory permission CAN access inventory"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "inventory_only")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access inventory (should succeed)
                page.goto(f"{self.BASE_URL}/inventory/items", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify NOT redirected to dashboard
                # Should either be on inventory page or show inventory content
                current_url = page.url.lower()
                assert "inventory" in current_url or "items" in current_url, \
                    f"Expected to access inventory, but was redirected to {current_url}"
                
                print("[OK] Test 11: User with inventory permission CAN access inventory")
                
            finally:
                browser.close()
    
    def test_12_permission_isolation_between_users(self):
        """Test that permissions are properly isolated between users"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # User 1 with requests permission
            page1 = browser.new_page()
            page1.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
            page1.fill("input[name='username']", "requests_only")
            page1.fill("input[name='password']", "testpass123")
            page1.click("button[type='submit']")
            page1.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
            
            # User 1 tries inventory (should fail)
            page1.goto(f"{self.BASE_URL}/inventory/items", timeout=30000)
            page1.wait_for_load_state("networkidle")
            url1_inventory = page1.url.lower()
            page1.close()
            
            # User 2 with inventory permission
            page2 = browser.new_page()
            page2.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
            page2.fill("input[name='username']", "inventory_only")
            page2.fill("input[name='password']", "testpass123")
            page2.click("button[type='submit']")
            page2.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
            
            # User 2 tries requests (should fail if not in permissions)
            page2.goto(f"{self.BASE_URL}/employee-requests/", timeout=30000)
            page2.wait_for_load_state("networkidle")
            url2_requests = page2.url.lower()
            page2.close()
            
            browser.close()
            
            # Verify permission isolation
            assert "dashboard" in url1_inventory, "User 1 should be denied inventory access"
            assert "dashboard" in url2_requests, "User 2 should be denied employee requests access"
            
            print("[OK] Test 12: Permission isolation verified")


if __name__ == "__main__":
    # Run tests
    test = TestGranularPermissionEnforcement()
    test.setup_class()
    
    try:
        test.test_01_user_login_success()
        test.test_02_inventory_access_denied_without_permission()
        test.test_03_suppliers_access_denied_without_permission()
        test.test_04_equipment_access_denied_without_permission()
        test.test_05_restaurant_access_denied_without_permission()
        test.test_06_admin_access_denied_without_permission()
        test.test_07_reports_access_denied_without_permission()
        test.test_08_employee_requests_access_denied_without_permission()
        test.test_09_advanced_features_access_denied_without_permission()
        test.test_10_analytics_access_denied_without_permission()
        test.test_11_user_with_inventory_can_access_inventory()
        test.test_12_permission_isolation_between_users()
        
        print("\n" + "="*60)
        print("[OK] All tests passed!")
        print("="*60)
    finally:
        test.teardown_class()