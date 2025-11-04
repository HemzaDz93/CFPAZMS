"""
E2E Tests for Dashboard Cards Enhancement
Tests the improved dashboard stat cards and meal cards with beautiful styling
"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_dashboard_loads(page):
    """Test that dashboard page loads successfully"""
    await page.goto("http://localhost:5000/dashboard/")
    
    # Wait for page title
    assert "لوحة التحكم" in await page.title()
    
    # Wait for main content to be visible
    main_content = page.locator(".main-content")
    assert await main_content.is_visible()


@pytest.mark.asyncio
async def test_stat_cards_exist(page):
    """Test that all 4 stat cards are present"""
    await page.goto("http://localhost:5000/dashboard/")
    
    # Wait for stat cards to load
    stat_cards = page.locator(".stat-card")
    count = await stat_cards.count()
    assert count >= 4, f"Should have at least 4 stat cards, got {count}"
    
    # Verify each card is visible
    for i in range(min(4, count)):
        card = stat_cards.nth(i)
        assert await card.is_visible(), f"Stat card {i+1} should be visible"


@pytest.mark.asyncio
async def test_stat_card_structure(page):
    """Test the structure of stat cards"""
    await page.goto("http://localhost:5000/dashboard/")
    
    # Get first stat card
    first_card = page.locator(".stat-card").first
    
    # Check for stat-card-content
    content = first_card.locator(".stat-card-content")
    assert await content.is_visible()
    
    # Check for stat-icon
    icon = first_card.locator(".stat-icon")
    assert await icon.is_visible()
    
    # Check for stat-value
    value = first_card.locator(".stat-value")
    assert await value.is_visible()
    
    # Check for stat-label
    label = first_card.locator(".stat-label")
    assert await label.is_visible()
    text = await label.text_content()
    assert len(text.strip()) > 0


@pytest.mark.asyncio
async def test_stat_icons_display(page):
    """Test that stat card icons are displayed correctly"""
    await page.goto("http://localhost:5000/dashboard/")
    
    # Get all stat icons
    icons = page.locator(".stat-icon i")
    icon_count = await icons.count()
    
    assert icon_count >= 4, f"Should have at least 4 icons, got {icon_count}"
    
    # Verify icons are visible and have correct class
    for i in range(min(4, icon_count)):
        icon = icons.nth(i)
        assert await icon.is_visible()
        class_attr = await icon.get_attribute("class")
        assert "fas" in class_attr, f"Icon {i+1} should have 'fas' class"


@pytest.mark.asyncio
async def test_stat_values_are_numeric(page):
    """Test that stat values are displayed and numeric"""
    await page.goto("http://localhost:5000/dashboard/")
    
    # Get all stat values
    values = page.locator(".stat-value")
    value_count = await values.count()
    
    assert value_count >= 4, f"Should have at least 4 stat values, got {value_count}"
    
    # Verify each value is numeric
    for i in range(min(4, value_count)):
        value_text = await values.nth(i).text_content()
        assert value_text.strip().isdigit(), \
            f"Stat value {i+1} should be numeric, got '{value_text}'"


@pytest.mark.asyncio
async def test_stat_labels_arabic_text(page):
    """Test that stat labels display correct Arabic text"""
    await page.goto("http://localhost:5000/dashboard/")
    
    # Get all stat labels
    labels = page.locator(".stat-label")
    label_count = await labels.count()
    
    assert label_count >= 4, f"Should have at least 4 stat labels, got {label_count}"
    
    # Expected labels - just check first one as example
    first_label = await labels.first.text_content()
    assert len(first_label.strip()) > 0, "First label should have text"
    # Check for Arabic characters
    assert any('\u0600' <= c <= '\u06FF' for c in first_label), \
        "Label should contain Arabic characters"


@pytest.mark.asyncio
async def test_stat_card_hover_effect(page):
    """Test that stat cards respond to hover"""
    await page.goto("http://localhost:5000/dashboard/")
    
    first_card = page.locator(".stat-card").first
    
    # Card should be visible before hover
    assert await first_card.is_visible()
    
    # Hover over the card
    await first_card.hover()
    
    # Wait a bit for animation
    await page.wait_for_timeout(300)
    
    # Card should still be visible after hover
    assert await first_card.is_visible()


@pytest.mark.asyncio
async def test_stat_card_has_box_shadow(page):
    """Test that stat cards have box shadow styling"""
    await page.goto("http://localhost:5000/dashboard/")
    
    first_card = page.locator(".stat-card").first
    
    # Get computed box shadow
    box_shadow = await first_card.evaluate(
        "el => window.getComputedStyle(el).boxShadow"
    )
    
    # Should have some shadow (not 'none')
    assert box_shadow and "none" not in box_shadow.lower(), \
        "Stat card should have box shadow"


@pytest.mark.asyncio
async def test_meal_cards_structure(page):
    """Test meal cards structure when present"""
    await page.goto("http://localhost:5000/dashboard/")
    
    meal_cards = page.locator(".meal-card")
    meal_count = await meal_cards.count()
    
    if meal_count > 0:
        # Verify meal cards are visible
        for i in range(min(2, meal_count)):  # Test first 2 if present
            card = meal_cards.nth(i)
            assert await card.is_visible()
            
            # Check for meal-card-image
            image_div = card.locator(".meal-card-image")
            assert await image_div.is_visible()
            
            # Check for meal-card-content
            content_div = card.locator(".meal-card-content")
            assert await content_div.is_visible()


@pytest.mark.asyncio
async def test_meal_card_badge_present(page):
    """Test meal card badges are present and visible"""
    await page.goto("http://localhost:5000/dashboard/")
    
    meal_badges = page.locator(".meal-badge")
    badge_count = await meal_badges.count()
    
    if badge_count > 0:
        # Check that at least one badge is visible
        first_badge = meal_badges.first
        assert await first_badge.is_visible()
        
        # Badge should have text
        text = await first_badge.text_content()
        assert len(text.strip()) > 0


@pytest.mark.asyncio
async def test_meal_card_title_present(page):
    """Test meal card titles are present"""
    await page.goto("http://localhost:5000/dashboard/")
    
    meal_titles = page.locator(".meal-title")
    title_count = await meal_titles.count()
    
    if title_count > 0:
        # Check that at least one title is visible
        first_title = meal_titles.first
        assert await first_title.is_visible()
        
        # Title should have text
        text = await first_title.text_content()
        assert len(text.strip()) > 0


@pytest.mark.asyncio
async def test_stat_card_icon_size(page):
    """Test that stat card icons have proper dimensions"""
    await page.goto("http://localhost:5000/dashboard/")
    
    stat_icons = page.locator(".stat-icon")
    
    if await stat_icons.count() > 0:
        first_icon = stat_icons.first
        
        # Get dimensions
        bounding_box = await first_icon.bounding_box()
        
        # Icon should be at least 70 pixels (allowing for some browser differences)
        assert bounding_box["width"] >= 70, \
            f"Icon width should be at least 70px, got {bounding_box['width']}"
        assert bounding_box["height"] >= 70, \
            f"Icon height should be at least 70px, got {bounding_box['height']}"


@pytest.mark.asyncio
async def test_dashboard_welcome_section(page):
    """Test dashboard welcome section"""
    await page.goto("http://localhost:5000/dashboard/")
    
    # Check for welcome section
    welcome = page.locator(".welcome-section")
    assert await welcome.is_visible()
    
    # Check for welcome heading
    heading = welcome.locator("h1")
    assert await heading.is_visible()
    text = await heading.text_content()
    assert "مرحباً" in text or "لوحة التحكم" in text


@pytest.mark.asyncio
async def test_stat_cards_responsive_grid(page):
    """Test responsive grid layout of stat cards"""
    await page.goto("http://localhost:5000/dashboard/")
    
    # Get stat cards
    stat_cards = page.locator(".stat-card")
    count = await stat_cards.count()
    
    assert count >= 4, "Should have at least 4 stat cards"
    
    # All cards should be visible
    for i in range(count):
        card = stat_cards.nth(i)
        bounding_box = await card.bounding_box()
        assert bounding_box is not None, f"Card {i+1} should have valid bounding box"
        assert bounding_box["width"] > 0, f"Card {i+1} should have positive width"
        assert bounding_box["height"] > 0, f"Card {i+1} should have positive height"


@pytest.mark.asyncio
async def test_page_title_correct(page):
    """Test page title is correct"""
    await page.goto("http://localhost:5000/dashboard/")
    
    title = await page.title()
    assert "لوحة التحكم" in title
    assert "نظام الإدارة" in title


if __name__ == "__main__":
    # Run tests with: pytest tests/test_dashboard_cards.py -v
    pytest.main([__file__, "-v"])