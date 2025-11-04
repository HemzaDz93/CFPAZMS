"""
Simple E2E Tests for Dashboard Cards Enhancement
Using playwright without complex async fixtures
"""

import subprocess
import time
from playwright.sync_api import sync_playwright


def test_dashboard_loads():
    """Test that dashboard page loads successfully"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # Wait for page title
            assert "لوحة التحكم" in page.title()
            
            # Wait for main content to be visible
            main_content = page.locator(".main-content")
            assert main_content.is_visible()
            
            print("✓ Dashboard loads successfully")
        finally:
            browser.close()


def test_stat_cards_exist():
    """Test that all 4 stat cards are present"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            # Wait for stat cards to load
            stat_cards = page.locator(".stat-card")
            count = stat_cards.count()
            assert count >= 4, f"Should have at least 4 stat cards, got {count}"
            
            # Verify each card is visible
            for i in range(min(4, count)):
                card = stat_cards.nth(i)
                assert card.is_visible(), f"Stat card {i+1} should be visible"
            
            print(f"✓ Found {count} stat cards")
        finally:
            browser.close()


def test_stat_card_structure():
    """Test the structure of stat cards"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            # Get first stat card
            first_card = page.locator(".stat-card").first
            
            # Check for stat-card-content
            content = first_card.locator(".stat-card-content")
            assert content.is_visible()
            
            # Check for stat-icon
            icon = first_card.locator(".stat-icon")
            assert icon.is_visible()
            
            # Check for stat-value
            value = first_card.locator(".stat-value")
            assert value.is_visible()
            
            # Check for stat-label
            label = first_card.locator(".stat-label")
            assert label.is_visible()
            text = label.text_content()
            assert len(text.strip()) > 0
            
            print("✓ Stat card structure is correct")
        finally:
            browser.close()


def test_stat_icons_display():
    """Test that stat card icons are displayed correctly"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            # Get all stat icons
            icons = page.locator(".stat-icon i")
            icon_count = icons.count()
            
            assert icon_count >= 4, f"Should have at least 4 icons, got {icon_count}"
            
            # Verify icons are visible and have correct class
            for i in range(min(4, icon_count)):
                icon = icons.nth(i)
                assert icon.is_visible()
                class_attr = icon.get_attribute("class")
                assert "fas" in class_attr, f"Icon {i+1} should have 'fas' class"
            
            print(f"✓ Found {icon_count} icon elements with correct classes")
        finally:
            browser.close()


def test_stat_values_are_numeric():
    """Test that stat values are displayed and numeric"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            # Get all stat values
            values = page.locator(".stat-value")
            value_count = values.count()
            
            assert value_count >= 4, f"Should have at least 4 stat values, got {value_count}"
            
            # Verify each value is numeric
            for i in range(min(4, value_count)):
                value_text = values.nth(i).text_content()
                assert value_text.strip().isdigit(), \
                    f"Stat value {i+1} should be numeric, got '{value_text}'"
            
            print("✓ All stat values are numeric")
        finally:
            browser.close()


def test_stat_labels_arabic_text():
    """Test that stat labels display correct Arabic text"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            # Get all stat labels
            labels = page.locator(".stat-label")
            label_count = labels.count()
            
            assert label_count >= 4, f"Should have at least 4 stat labels, got {label_count}"
            
            # Expected labels
            expected_labels = ["إجمالي الأصناف", "عدد المستخدمين", "عدد الموردين", "أصناف منخفضة"]
            
            # Verify labels contain expected text
            for i, expected_label in enumerate(expected_labels):
                if i < label_count:
                    label_text = labels.nth(i).text_content()
                    assert expected_label in label_text, \
                        f"Label {i+1} should contain '{expected_label}', got '{label_text}'"
            
            print("✓ Stat labels contain correct Arabic text")
        finally:
            browser.close()


def test_stat_card_has_box_shadow():
    """Test that stat cards have box shadow styling"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            first_card = page.locator(".stat-card").first
            
            # Get computed box shadow
            box_shadow = first_card.evaluate(
                "el => window.getComputedStyle(el).boxShadow"
            )
            
            # Should have some shadow (not 'none')
            assert box_shadow and "none" not in box_shadow.lower(), \
                "Stat card should have box shadow"
            
            print(f"✓ Stat card has box shadow: {box_shadow}")
        finally:
            browser.close()


def test_meal_cards_structure():
    """Test meal cards structure when present"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            meal_cards = page.locator(".meal-card")
            meal_count = meal_cards.count()
            
            if meal_count > 0:
                # Verify meal cards are visible
                for i in range(min(2, meal_count)):
                    card = meal_cards.nth(i)
                    assert card.is_visible()
                    
                    # Check for meal-card-image
                    image_div = card.locator(".meal-card-image")
                    assert image_div.is_visible()
                    
                    # Check for meal-card-content
                    content_div = card.locator(".meal-card-content")
                    assert content_div.is_visible()
                
                print(f"✓ Found {meal_count} meal cards with correct structure")
            else:
                print("ℹ No meals available today")
        finally:
            browser.close()


def test_stat_card_icon_size():
    """Test that stat card icons have proper dimensions"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            stat_icons = page.locator(".stat-icon")
            
            if stat_icons.count() > 0:
                first_icon = stat_icons.first
                
                # Get dimensions
                bounding_box = first_icon.bounding_box()
                
                # Icon should be at least 70 pixels
                assert bounding_box["width"] >= 70, \
                    f"Icon width should be at least 70px, got {bounding_box['width']}"
                assert bounding_box["height"] >= 70, \
                    f"Icon height should be at least 70px, got {bounding_box['height']}"
                
                print(f"✓ Stat icon size is correct: {bounding_box['width']}x{bounding_box['height']}px")
        finally:
            browser.close()


def test_dashboard_page_layout():
    """Test overall dashboard page layout"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:5000/dashboard/", timeout=30000)
            
            # Check for welcome section
            welcome = page.locator(".welcome-section")
            assert welcome.is_visible()
            
            # Check for stat cards section
            stat_cards = page.locator(".stat-card")
            assert stat_cards.count() >= 4
            
            # Check for container fluid
            container = page.locator(".container-fluid")
            assert container.is_visible()
            
            print("✓ Dashboard page layout is correct")
        finally:
            browser.close()


if __name__ == "__main__":
    # Run tests manually
    print("\n=== Dashboard Cards Tests ===\n")
    
    tests = [
        test_dashboard_loads,
        test_stat_cards_exist,
        test_stat_card_structure,
        test_stat_icons_display,
        test_stat_values_are_numeric,
        test_stat_labels_arabic_text,
        test_stat_card_has_box_shadow,
        test_meal_cards_structure,
        test_stat_card_icon_size,
        test_dashboard_page_layout,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\nRunning: {test.__name__}")
            test()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            failed += 1
    
    print(f"\n\n=== Results ===")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()