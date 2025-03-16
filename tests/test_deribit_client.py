#!/usr/bin/env python3

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from deribit_client import DeribitClient


class TestDeribitClient(unittest.TestCase):
    """Test cases for the DeribitClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = DeribitClient()
    
    def test_make_request_mocked(self):
        """Test the _make_request method with a mocked session."""
        # Create a mock for the session
        mock_session = MagicMock()
        self.client.session = mock_session
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"test": "data"}}
        mock_session.get.return_value = mock_response
        
        # Call the method
        result = self.client._make_request("test_method", {"param": "value"})
        
        # Check the result
        self.assertEqual(result, {"test": "data"})
        
        # Check that the session was called correctly
        mock_session.get.assert_called_once()
        args, kwargs = mock_session.get.call_args
        self.assertEqual(kwargs["params"], {"param": "value"})
    
    @patch("deribit_client.DeribitClient._make_request")
    def test_get_instruments(self, mock_make_request):
        """Test the get_instruments method."""
        # Mock the response
        mock_make_request.return_value = [{"instrument_name": "BTC-PERPETUAL"}]
        
        # Call the method
        result = self.client.get_instruments("BTC")
        
        # Check the result
        self.assertEqual(result, [{"instrument_name": "BTC-PERPETUAL"}])
        
        # Check that _make_request was called correctly
        mock_make_request.assert_called_once_with("get_instruments", {
            "currency": "BTC",
            "kind": "option",
            "expired": "false"
        })
    
    @patch("deribit_client.DeribitClient._make_request")
    def test_get_index_price(self, mock_make_request):
        """Test the get_index_price method."""
        # Mock the response
        mock_make_request.return_value = {"index_price": 50000.0}
        
        # Call the method
        result = self.client.get_index_price("BTC")
        
        # Check the result
        self.assertEqual(result, {"index_price": 50000.0})
        
        # Check that _make_request was called correctly
        mock_make_request.assert_called_once_with("get_index_price", {
            "index_name": "btc_usd"
        })


if __name__ == "__main__":
    unittest.main() 