"""
Unit & Edge-Case Test Suite for Tokenly Core Utilities and Input Validation
"""

import unittest
from app import app
from models import db, Business, DailyTokenSequence
from utils import calculate_item_price, allowed_file, generate_daily_token, get_today_date_key

class TestTokenlyUtilities(unittest.TestCase):

    def test_calculate_item_price_decimal_precision(self):
        """Test strict financial price quantization to 2 decimal places"""
        self.assertEqual(calculate_item_price(70.0), 70.0)
        self.assertEqual(calculate_item_price("129.99"), 129.99)
        self.assertEqual(calculate_item_price("110.1234"), 110.12)
        self.assertEqual(calculate_item_price(None), 0.0)
        self.assertEqual(calculate_item_price(-50.0), 0.0)
        self.assertEqual(calculate_item_price("invalid_string"), 0.0)

    def test_allowed_file_security_check(self):
        """Test image extension whitelist filtering"""
        self.assertTrue(allowed_file("dish_photo.png"))
        self.assertTrue(allowed_file("food.jpg"))
        self.assertTrue(allowed_file("burger.webp"))
        self.assertFalse(allowed_file("malicious_script.exe"))
        self.assertFalse(allowed_file("payload.php"))
        self.assertFalse(allowed_file("no_extension"))
        self.assertFalse(allowed_file(""))

    def test_daily_token_sequence_increment(self):
        """Test daily token increment logic (#001 -> #002)"""
        with app.app_context():
            # Query or create demo business
            business = Business.query.filter_by(username='sharmafastfood').first()
            if business:
                raw_1, token_1 = generate_daily_token(business.id)
                raw_2, token_2 = generate_daily_token(business.id)
                
                self.assertGreater(raw_2, raw_1)
                self.assertEqual(raw_2 - raw_1, 1)
                self.assertTrue(token_1.startswith("#"))
                self.assertTrue(token_2.startswith("#"))

if __name__ == '__main__':
    unittest.main()
