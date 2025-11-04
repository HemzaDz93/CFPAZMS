"""
E2E Tests para o sistema de wajbat de Employés
Testa o registro diário de wajbat, cálculo dinâmico de preços, e tratamento de alertas
"""

import pytest
from playwright.sync_api import sync_playwright, expect
from datetime import datetime, timedelta
import time


@pytest.fixture
def browser_context():
    """Cria um contexto do Playwright para os testes"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        yield page
        
        page.close()
        context.close()
        browser.close()


class TestEmployeeMealsDailyRegistration:
    """Testa a página de registro diário de wajbat"""
    
    BASE_URL = "http://127.0.0.1:5000"
    TEST_USERNAME = "admin"
    TEST_PASSWORD = "admin123"
    
    def login(self, page):
        """Autentica o usuário"""
        page.goto(f"{self.BASE_URL}/auth/login")
        
        # Preencher credenciais
        page.fill('input[name="username"]', self.TEST_USERNAME)
        page.fill('input[name="password"]', self.TEST_PASSWORD)
        
        # Clique no botão de login
        page.click('button[type="submit"]')
        
        # Aguardar redirecionamento
        page.wait_for_url("**/dashboard/**")
    
    def test_meal_registration_page_loads(self, browser_context):
        """Testa se a página de registro diário carrega corretamente"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para a página de registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Verificar que a página carregou
        expect(page).to_have_url(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Verificar elementos principais
        page.wait_for_selector("h2:has-text('تسجيل وجبات الموظفين')")
        assert page.is_visible("button:has-text('تسجيل الوجبات')")
    
    def test_meal_cost_displays_from_settings(self, browser_context):
        """Testa se o preço da wajbat é exibido dinamicamente das configurações"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para o registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Verificar que o preço está presente (deve ser 2.5 ou configurado)
        price_text = page.text_content("p:has-text('السعر الموحد')")
        assert "دج" in price_text
        assert any(char.isdigit() for char in price_text), "Preço não encontrado no texto"
    
    def test_price_calculation_updates_dynamically(self, browser_context):
        """Testa se o cálculo de preço atualiza quando muda a quantidade"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para o registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Obter o preço inicial
        initial_price_text = page.text_content("#meal_price")
        initial_price = float(initial_price_text.strip())
        
        # Mudar a quantidade de wajbat
        meal_count_input = page.locator("input#meal_count")
        meal_count_input.fill("3")
        
        # Aguardar atualização
        page.wait_for_timeout(100)
        
        # Verificar que o total foi calculado corretamente
        total_text = page.text_content("#total_price")
        total_price = float(total_text.strip())
        
        expected_total = initial_price * 3
        assert abs(total_price - expected_total) < 0.01, \
            f"Cálculo incorreto: esperado {expected_total}, obtido {total_price}"
    
    def test_meal_registration_success(self, browser_context):
        """Testa o registro bem-sucedido de uma wajbat"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para o registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Selecionar um empregado (primeira opção)
        page.select_option("select#user_id", "المدير العام (admin)")
        
        # Verificar que a opção foi selecionada
        selected_value = page.input_value("select#user_id")
        assert selected_value != "", "Nenhum empregado selecionado"
        
        # Definir quantidade
        page.fill("input#meal_count", "2")
        
        # Clique no botão de registro
        page.click("button:has-text('تسجيل الوجبات')")
        
        # Aguardar a mensagem de sucesso
        page.wait_for_selector(".alert-success", timeout=5000)
        
        # Verificar mensagem de sucesso
        success_message = page.text_content(".alert-success")
        assert "بنجاح" in success_message, f"Mensagem de sucesso não encontrada: {success_message}"
        assert "وجبة" in success_message
    
    def test_meal_registration_no_error(self, browser_context):
        """Testa que não há erro 'DEFAULT_ALERT_THRESHOLD' ao registar"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para o registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Selecionar empregado e registar
        page.select_option("select#user_id", "المدير العام (admin)")
        page.click("button:has-text('تسجيل الوجبات')")
        
        # Aguardar resposta
        page.wait_for_timeout(2000)
        
        # Verificar que não há erro sobre DEFAULT_ALERT_THRESHOLD
        page_content = page.content()
        assert "DEFAULT_ALERT_THRESHOLD" not in page_content
        assert "is not defined" not in page_content
    
    def test_meal_information_section_displays_correctly(self, browser_context):
        """Testa se a seção de informações exibe o preço e limite corretos"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para o registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Verificar seção de informações
        assert page.is_visible("h6:has-text('💡 معلومات')")
        
        # Verificar que os valores estão presentes
        info_text = page.text_content("li:has-text('سعر الوجبة')")
        assert "دج" in info_text
        
        threshold_text = page.text_content("li:has-text('الحد الأقصى')")
        assert "دج" in threshold_text


class TestEmployeeMealsDynamicPricing:
    """Testa a atualização dinâmica de preços em diferentes páginas"""
    
    BASE_URL = "http://127.0.0.1:5000"
    TEST_USERNAME = "admin"
    TEST_PASSWORD = "admin123"
    
    def login(self, page):
        """Autentica o usuário"""
        page.goto(f"{self.BASE_URL}/auth/login")
        page.fill('input[name="username"]', self.TEST_USERNAME)
        page.fill('input[name="password"]', self.TEST_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/**")
    
    def test_price_reads_from_organization_settings(self, browser_context):
        """Testa que o preço é lido das org_settings (context processor)"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para o registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Obter o preço exibido
        displayed_price_text = page.text_content("#meal_price")
        displayed_price = float(displayed_price_text.strip())
        
        # Verificar que o preço está sendo exibido (não é zero ou inválido)
        assert displayed_price > 0, f"Preço inválido: {displayed_price}"
        assert displayed_price < 1000, f"Preço parece incorreto: {displayed_price}"
        
        # Preço deve ser exibido em múltiplos lugares
        price_in_header = page.text_content("p:has-text('السعر الموحد')")
        assert str(displayed_price) in price_in_header or str(int(displayed_price)) in price_in_header
    
    def test_get_meal_cost_per_unit_function_works(self, browser_context):
        """Testa que a função get_meal_cost_per_unit() funciona corretamente"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para a página de registro
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Fazer uma submissão de formulário para ativar a função
        page.select_option("select#user_id", "المدير العام (admin)")
        page.click("button:has-text('تسجيل الوجبات')")
        
        # Verificar que não há erro
        page.wait_for_timeout(1000)
        
        # Não deve haver erro de "MEAL_COST_PER_UNIT is not defined"
        page_content = page.content()
        assert "MEAL_COST_PER_UNIT" not in page_content or "is not defined" not in page_content


class TestEmployeeMealsAlertThreshold:
    """Testa o sistema de alertas com threshold dinâmico"""
    
    BASE_URL = "http://127.0.0.1:5000"
    TEST_USERNAME = "admin"
    TEST_PASSWORD = "admin123"
    
    def login(self, page):
        """Autentica o usuário"""
        page.goto(f"{self.BASE_URL}/auth/login")
        page.fill('input[name="username"]', self.TEST_USERNAME)
        page.fill('input[name="password"]', self.TEST_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/**")
    
    def test_no_alert_threshold_error(self, browser_context):
        """Testa que não há erro sobre threshold não definido"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para o registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Fazer o registro
        page.select_option("select#user_id", "المدير العام (admin)")
        page.click("button:has-text('تسجيل الوجبات')")
        
        # Aguardar resposta
        page.wait_for_timeout(2000)
        
        # Verificar que não há erro
        alerts = page.query_selector_all(".alert-danger")
        for alert in alerts:
            text = alert.text_content()
            assert "DEFAULT_ALERT_THRESHOLD" not in text
            assert "not defined" not in text
    
    def test_alert_threshold_displays_in_info_section(self, browser_context):
        """Testa que o threshold de alerta é exibido na seção de informações"""
        page = browser_context
        
        # Login
        self.login(page)
        
        # Navegar para o registro diário
        page.goto(f"{self.BASE_URL}/employee-meals/daily-registration")
        
        # Verificar que o threshold está presente
        threshold_element = page.locator("#info_alert_threshold")
        assert threshold_element.is_visible()
        
        threshold_value = threshold_element.text_content()
        threshold_num = float(threshold_value.strip())
        assert threshold_num > 0, f"Threshold inválido: {threshold_num}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])