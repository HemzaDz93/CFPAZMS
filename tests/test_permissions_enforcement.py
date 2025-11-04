"""
Comprehensive E2E Tests for Granular Permission Enforcement - Pytest Compatible
Uses pytest framework with sync Playwright
"""

import pytest
import time
from playwright.sync_api import sync_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from models import db, User, UserPermission


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    """Setup test environment and cleanup"""
    app = create_app('development')
    
    # Create test users
    with app.app_context():
        # User with only requests permissions
        existing = User.query.filter_by(username="test_requests").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        user1 = User(
            username="test_requests",
            email="test_requests@test.local",
            first_name="Test",
            last_name="Requests",
            role="worker",
            is_active=True
        )
        user1.set_password("testpass123")
        db.session.add(user1)
        db.session.flush()
        
        perm1 = UserPermission(
            user_id=user1.id,
            permission_key="requests_view_own",
            permission_name="View own requests",
            permission_category="employee_requests",
            is_allowed=True
        )
        db.session.add(perm1)
        db.session.commit()
        
        # User with only inventory permissions
        existing = User.query.filter_by(username="test_inventory").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        user2 = User(
            username="test_inventory",
            email="test_inventory@test.local",
            first_name="Test",
            last_name="Inventory",
            role="worker",
            is_active=True
        )
        user2.set_password("testpass123")
        db.session.add(user2)
        db.session.flush()
        
        perm2 = UserPermission(
            user_id=user2.id,
            permission_key="inventory_view_items",
            permission_name="View inventory items",
            permission_category="inventory",
            is_allowed=True
        )
        db.session.add(perm2)
        db.session.commit()
    
    yield  # Run tests
    
    # Cleanup
    with app.app_context():
        user = User.query.filter_by(username="test_requests").first()
        if user:
            db.session.delete(user)
        user = User.query.filter_by(username="test_inventory").first()
        if user:
            db.session.delete(user)
        db.session.commit()


@pytest.mark.test_permissions
class TestPermissionEnforcement:
    """Test suite for permission enforcement"""
    
    BASE_URL = "http://localhost:5000"
    
    def test_user_login_success(self):
        """Test successful login with minimal permissions"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "test_requests")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                assert "لوحة التحكم" in page.title() or "Dashboard" in page.title()
            finally:
                browser.close()
    
    def test_inventory_access_denied_without_permission(self):
        """Test that users without inventory permission cannot access inventory"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Login with requests-only user
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "test_requests")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access inventory
                page.goto(f"{self.BASE_URL}/inventory/items", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Verify not on inventory page
                url = page.url.lower()
                assert "inventory" not in url or "items" not in url
            finally:
                browser.close()
    
    def test_suppliers_access_denied_without_permission(self):
        """Test suppliers access denied"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "test_requests")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                page.goto(f"{self.BASE_URL}/suppliers/", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                url = page.url.lower()
                assert "suppliers" not in url
            finally:
                browser.close()
    
    def test_admin_access_denied_without_permission(self):
        """Test admin access denied"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "test_requests")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                page.goto(f"{self.BASE_URL}/admin/users", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                url = page.url.lower()
                assert "admin" not in url or "users" not in url
            finally:
                browser.close()
    
    def test_inventory_user_can_access_inventory(self):
        """Test that user WITH inventory permission CAN access inventory"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
                page.fill("input[name='username']", "test_inventory")
                page.fill("input[name='password']", "testpass123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
                
                # Try to access inventory (should succeed)
                page.goto(f"{self.BASE_URL}/inventory/items", timeout=30000)
                page.wait_for_load_state("networkidle")
                
                url = page.url.lower()
                # Should be on inventory page or at least not denied
                assert ("inventory" in url or "items" in url) or "dashboard" not in url
            finally:
                browser.close()
    
    def test_permission_isolation(self):
        """Test that permissions are properly isolated between users"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Test requests user cannot access inventory
            page1 = browser.new_page()
            page1.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
            page1.fill("input[name='username']", "test_requests")
            page1.fill("input[name='password']", "testpass123")
            page1.click("button[type='submit']")
            page1.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
            
            page1.goto(f"{self.BASE_URL}/inventory/items", timeout=30000)
            page1.wait_for_load_state("networkidle")
            url1 = page1.url.lower()
            page1.close()
            
            # Test inventory user cannot access admin
            page2 = browser.new_page()
            page2.goto(f"{self.BASE_URL}/auth/login", timeout=30000)
            page2.fill("input[name='username']", "test_inventory")
            page2.fill("input[name='password']", "testpass123")
            page2.click("button[type='submit']")
            page2.wait_for_url(f"{self.BASE_URL}/dashboard/**", timeout=30000)
            
            page2.goto(f"{self.BASE_URL}/admin/users", timeout=30000)
            page2.wait_for_load_state("networkidle")
            url2 = page2.url.lower()
            page2.close()
            
            browser.close()
            
            # Verify isolation
            assert "inventory" not in url1 or "items" not in url1
            assert "admin" not in url2 or "users" not in url2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])