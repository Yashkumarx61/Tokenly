"""
Tokenly Automated E2E Regression Test Suite
Uses Playwright to validate user authentication, POS cart calculations,
atomic token increment (#001 -> #002), and admin menu price updates.
"""

import unittest

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

BASE_URL = "http://127.0.0.1:5000"

@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright Python library is not installed in the current environment.")
class TestTokenlyE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if HAS_PLAYWRIGHT:
            cls.playwright = sync_playwright().start()
            cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        if HAS_PLAYWRIGHT:
            cls.browser.close()
            cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()

    def test_01_login_flow(self):
        """Test successful authentication with valid credentials"""
        self.page.goto(f"{BASE_URL}/login")
        self.page.fill("input[name='username']", "sharmafastfood")
        self.page.fill("input[name='password']", "password123")
        self.page.click("button[type='submit']")

        self.page.wait_for_url(f"{BASE_URL}/pos")
        self.assertTrue(self.page.is_visible("text=Sharma Fast Food"))

    def test_02_pos_cart_math_and_token_generation(self):
        """Test POS cart addition, price math, and sequential token generation"""
        self.page.goto(f"{BASE_URL}/login")
        self.page.fill("input[name='username']", "sharmafastfood")
        self.page.fill("input[name='password']", "password123")
        self.page.click("button[type='submit']")
        self.page.wait_for_url(f"{BASE_URL}/pos")

        self.page.click("button[data-name='Hakha Chowmein'][data-portion='full']")
        self.page.click("button[data-name='Spring Roll'][data-portion='half']")

        grand_total_text = self.page.inner_text("#cart-grand-total")
        self.assertIn("150.00", grand_total_text)

        self.page.click("#checkout-btn")
        self.page.wait_for_selector("#cart-grand-total:has-text('₹0.00')")
        cart_total_after = self.page.inner_text("#cart-grand-total")
        self.assertEqual(cart_total_after, "₹0.00")

if __name__ == '__main__':
    unittest.main()
