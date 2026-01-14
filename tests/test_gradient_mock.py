import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from implementation_folder.core.gradient_client import GradientLLMClient

class TestGradientClient(unittest.TestCase):

    def setUp(self):
        # Mock environment variable
        self.env_patcher = patch.dict(os.environ, {"GRADIENT_MODEL_ACCESS_KEY": "fake-key"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("implementation_folder.core.gradient_client.Gradient")
    def test_sync_chat_completion(self, MockGradient):
        # Setup Mock
        mock_instance = MockGradient.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello World"))]
        mock_instance.chat.completions.create.return_value = mock_response

        # Init Client
        client = GradientLLMClient()

        # Act
        response = client.chat_completion(messages=[{"role": "user", "content": "test"}])

        # Assert
        self.assertEqual(response, "Hello World")
        mock_instance.chat.completions.create.assert_called_once()

    @patch("implementation_folder.core.gradient_client.Gradient")
    def test_missing_api_key(self, MockGradient):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                GradientLLMClient()

if __name__ == '__main__':
    unittest.main()
