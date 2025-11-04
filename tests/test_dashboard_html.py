"""
Simple HTML-based tests for Dashboard Cards Enhancement
"""

import requests
from bs4 import BeautifulSoup


def test_dashboard_html():
    """Test dashboard HTML contains all stat cards"""
    response = requests.get("http://localhost:5000/dashboard/")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all stat cards
    stat_cards = soup.find_all('div', class_='stat-card')
    assert len(stat_cards) >= 4, f"Expected at least 4 stat cards, found {len(stat_cards)}"
    
    print(f"✓ Found {len(stat_cards)} stat cards")


def test_stat_card_structure():
    """Test stat card contains required elements"""
    response = requests.get("http://localhost:5000/dashboard/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    stat_cards = soup.find_all('div', class_='stat-card')
    
    for i, card in enumerate(stat_cards[:4]):
        # Check for stat-card-content
        content = card.find('div', class_='stat-card-content')
        assert content is not None, f"Card {i+1} missing stat-card-content"
        
        # Check for stat-icon
        icon = content.find('div', class_='stat-icon')
        assert icon is not None, f"Card {i+1} missing stat-icon"
        
        # Check for stat-value
        value = content.find('div', class_='stat-value')
        assert value is not None, f"Card {i+1} missing stat-value"
        
        # Check for stat-label
        label = content.find('div', class_='stat-label')
        assert label is not None, f"Card {i+1} missing stat-label"
        assert len(label.get_text().strip()) > 0, f"Card {i+1} label is empty"
    
    print("✓ All stat cards have correct structure")


def test_stat_card_labels_arabic():
    """Test stat card labels contain Arabic text"""
    response = requests.get("http://localhost:5000/dashboard/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    stat_cards = soup.find_all('div', class_='stat-card')
    expected_labels = ["إجمالي الأصناف", "عدد المستخدمين", "عدد الموردين", "أصناف منخفضة"]
    
    for i, card in enumerate(stat_cards[:4]):
        label = card.find('div', class_='stat-label')
        label_text = label.get_text().strip()
        assert expected_labels[i] in label_text, \
            f"Card {i+1}: Expected '{expected_labels[i]}' in '{label_text}'"
    
    print("✓ All stat card labels contain correct Arabic text")


def test_stat_icons_present():
    """Test stat icons are present"""
    response = requests.get("http://localhost:5000/dashboard/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    stat_icons = soup.find_all('div', class_='stat-icon')
    assert len(stat_icons) >= 4, f"Expected at least 4 icons, found {len(stat_icons)}"
    
    # Check that each icon has an i element with fas class
    for i, icon in enumerate(stat_icons[:4]):
        i_elem = icon.find('i', class_='fas')
        assert i_elem is not None, f"Icon {i+1} missing 'i' element with 'fas' class"
    
    print(f"✓ All {len(stat_icons)} icons have correct structure")


def test_stat_values_present():
    """Test stat values are present and numeric"""
    response = requests.get("http://localhost:5000/dashboard/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    stat_values = soup.find_all('div', class_='stat-value')
    assert len(stat_values) >= 4, f"Expected at least 4 values, found {len(stat_values)}"
    
    # Check that values are numeric
    for i, value in enumerate(stat_values[:4]):
        text = value.get_text().strip()
        assert text.isdigit(), f"Value {i+1} is not numeric: '{text}'"
    
    print(f"✓ All {len(stat_values)} stat values are numeric")


def test_meal_cards():
    """Test meal cards structure if present"""
    response = requests.get("http://localhost:5000/dashboard/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    meal_cards = soup.find_all('div', class_='meal-card')
    
    if len(meal_cards) > 0:
        for i, card in enumerate(meal_cards[:2]):
            # Check for meal-card-image
            image = card.find('div', class_='meal-card-image')
            assert image is not None, f"Meal card {i+1} missing image section"
            
            # Check for meal-card-content
            content = card.find('div', class_='meal-card-content')
            assert content is not None, f"Meal card {i+1} missing content section"
            
            # Check for meal-badge
            badge = content.find('div', class_='meal-badge')
            assert badge is not None, f"Meal card {i+1} missing badge"
            
            # Check for meal-title
            title = content.find('h5', class_='meal-title')
            assert title is not None, f"Meal card {i+1} missing title"
        
        print(f"✓ All {len(meal_cards)} meal cards have correct structure")
    else:
        print("ℹ No meals available today")


def test_dashboard_css_classes():
    """Test that dashboard has correct CSS classes"""
    response = requests.get("http://localhost:5000/dashboard/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Check for welcome section
    welcome = soup.find('div', class_='welcome-section')
    assert welcome is not None, "Missing welcome-section"
    
    # Check for main content
    main_content = soup.find('div', class_='main-content')
    assert main_content is not None, "Missing main-content"
    
    # Check for stat card wrapper
    stat_wrappers = soup.find_all('div', class_='stat-card-wrapper')
    assert len(stat_wrappers) >= 4, "Missing stat-card-wrapper elements"
    
    print("✓ Dashboard has correct CSS classes")


def test_stat_card_css_gradient():
    """Test that stat cards have gradient styling in HTML"""
    response = requests.get("http://localhost:5000/dashboard/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Check if CSS is present in style tags
    styles = soup.find_all('style')
    css_content = ''.join([style.string for style in styles if style.string])
    
    # Check for gradient definitions
    assert 'linear-gradient' in css_content, "Missing linear-gradient in CSS"
    assert 'stat-card' in css_content, "Missing stat-card styling in CSS"
    assert 'stat-icon' in css_content, "Missing stat-icon styling in CSS"
    
    print("✓ Dashboard CSS contains required gradient and styling")


if __name__ == "__main__":
    print("\n=== Dashboard HTML Tests ===\n")
    
    tests = [
        test_dashboard_html,
        test_stat_card_structure,
        test_stat_card_labels_arabic,
        test_stat_icons_present,
        test_stat_values_present,
        test_meal_cards,
        test_dashboard_css_classes,
        test_stat_card_css_gradient,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"Running: {test.__name__}")
            test()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            failed += 1
    
    print(f"\n\n=== Results ===")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()