# tests/test_example.py

import unittest
from list_sync.config import encrypt_config, decrypt_config
from list_sync.database import init_database, load_list_ids
from list_sync.utils import color_gradient

class TestConfigFunctions(unittest.TestCase):

    def test_encrypt_decrypt_config(self):
        data = {"overseerr_url": "http://example.com", "api_key": "testkey"}
        password = "testpassword"
        
        encrypted_data = encrypt_config(data, password)
        decrypted_data = decrypt_config(encrypted_data, password)
        
        self.assertEqual(data, decrypted_data)

class TestDatabaseFunctions(unittest.TestCase):

    def test_init_database(self):
        # This is a simple test to ensure the database initializes without error
        try:
            init_database()
        except Exception as e:
            self.fail(f"init_database() raised an exception {e}")

    def test_load_list_ids(self):
        # Assuming the database is empty initially
        init_database()
        list_ids = load_list_ids()
        self.assertEqual(list_ids, [])

class TestUtilsFunctions(unittest.TestCase):

    def test_color_gradient(self):
        text = "Hello"
        start_color = "#000000"
        end_color = "#ffffff"
        result = color_gradient(text, start_color, end_color)
        self.assertIn("Hello", result)

if __name__ == '__main__':
    unittest.main()
