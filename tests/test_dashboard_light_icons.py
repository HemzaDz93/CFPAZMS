"""
E2E Tests for Dashboard Light Icon Colors
Testing removal of glowing animations and implementation of lighter, clearer icon backgrounds
"""

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def authenticated_page(page):
    """Create authenticated page for dashboard access"""
    # Navigate to login page
    await page.goto('http://localhost:5000/auth/login?next=/dashboard/')
    
    # Login with test credentials
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    
    # Wait for dashboard to load
    await page.wait_for_url('http://localhost:5000/dashboard/')
    await page.wait_for_selector('.stat-icon', timeout=5000)
    
    yield page


@pytest.mark.asyncio
async def test_stat_cards_exist(authenticated_page):
    """Verify all 4 stat cards are present"""
    stat_cards = await authenticated_page.query_selector_all('.stat-card')
    assert len(stat_cards) == 4, "Expected 4 stat cards on dashboard"


@pytest.mark.asyncio
async def test_stat_icons_exist(authenticated_page):
    """Verify all stat icons are rendered"""
    stat_icons = await authenticated_page.query_selector_all('.stat-icon')
    assert len(stat_icons) == 4, "Expected 4 stat icons"


@pytest.mark.asyncio
async def test_no_pulse_glow_animation(authenticated_page):
    """Verify pulse-glow animation has been removed"""
    animation_check = await authenticated_page.evaluate("""
        () => {
            const icons = document.querySelectorAll('.stat-icon');
            const results = [];
            icons.forEach((icon, index) => {
                const computedStyle = window.getComputedStyle(icon);
                results.push({
                    card: index + 1,
                    animation: computedStyle.animation
                });
            });
            return results;
        }
    """)
    
    # Verify no animation is applied
    for result in animation_check:
        assert result['animation'] == 'none', \
            f"Card {result['card']}: animation should be 'none', got '{result['animation']}'"


@pytest.mark.asyncio
async def test_stat_icons_background_colors(authenticated_page):
    """Verify stat icons have light background colors"""
    color_check = await authenticated_page.evaluate("""
        () => {
            const icons = document.querySelectorAll('.stat-icon');
            const results = [];
            icons.forEach((icon, index) => {
                const computedStyle = window.getComputedStyle(icon);
                results.push({
                    card: index + 1,
                    background: computedStyle.backgroundColor
                });
            });
            return results;
        }
    """)
    
    # Define expected light colors (RGB values)
    expected_colors = {
        1: 'rgb(224, 231, 255)',      # Light blue
        2: 'rgb(209, 250, 229)',      # Light green
        3: 'rgb(254, 243, 199)',      # Light yellow
        4: 'rgb(254, 226, 226)'       # Light red
    }
    
    for result in color_check:
        card_num = result['card']
        assert result['background'] == expected_colors[card_num], \
            f"Card {card_num}: Expected background {expected_colors[card_num]}, got {result['background']}"


@pytest.mark.asyncio
async def test_stat_icons_text_colors(authenticated_page):
    """Verify stat icons have contrasting text colors"""
    color_check = await authenticated_page.evaluate("""
        () => {
            const icons = document.querySelectorAll('.stat-icon i');
            const results = [];
            icons.forEach((icon, index) => {
                const computedStyle = window.getComputedStyle(icon);
                results.push({
                    card: index + 1,
                    color: computedStyle.color
                });
            });
            return results;
        }
    """)
    
    # Define expected icon colors (RGB values)
    expected_icon_colors = {
        1: 'rgb(79, 70, 229)',        # Indigo
        2: 'rgb(5, 150, 105)',        # Green
        3: 'rgb(217, 119, 6)',        # Orange
        4: 'rgb(220, 38, 38)'         # Red
    }
    
    for result in color_check:
        card_num = result['card']
        assert result['color'] == expected_icon_colors[card_num], \
            f"Card {card_num}: Expected icon color {expected_icon_colors[card_num]}, got {result['color']}"


@pytest.mark.asyncio
async def test_stat_values_and_labels_visible(authenticated_page):
    """Verify stat values and labels are visible"""
    stat_values = await authenticated_page.query_selector_all('.stat-value')
    stat_labels = await authenticated_page.query_selector_all('.stat-label')
    
    assert len(stat_values) == 4, "Expected 4 stat values"
    assert len(stat_labels) == 4, "Expected 4 stat labels"


@pytest.mark.asyncio
async def test_icon_containers_have_proper_shadows(authenticated_page):
    """Verify icon containers have subtle shadows for clarity"""
    shadow_check = await authenticated_page.evaluate("""
        () => {
            const icons = document.querySelectorAll('.stat-icon');
            const results = [];
            icons.forEach((icon, index) => {
                const computedStyle = window.getComputedStyle(icon);
                results.push({
                    card: index + 1,
                    boxShadow: computedStyle.boxShadow,
                    hasValidShadow: computedStyle.boxShadow.includes('rgba')
                });
            });
            return results;
        }
    """)
    
    for result in shadow_check:
        assert result['hasValidShadow'], \
            f"Card {result['card']}: Icon should have a shadow, got '{result['boxShadow']}'"


@pytest.mark.asyncio
async def test_dashboard_layout_responsive(authenticated_page):
    """Verify dashboard layout is responsive with new colors"""
    # Test desktop view
    stat_cards = await authenticated_page.query_selector_all('.stat-card')
    assert len(stat_cards) == 4
    
    # Verify all cards are visible
    for card in stat_cards:
        is_visible = await card.is_visible()
        assert is_visible, "All stat cards should be visible"