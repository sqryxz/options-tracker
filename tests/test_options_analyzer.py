#!/usr/bin/env python3

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from options_analyzer import OptionsAnalyzer
from deribit_client import DeribitClient


class TestOptionsAnalyzer(unittest.TestCase):
    """Test cases for the OptionsAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = MagicMock(spec=DeribitClient)
        self.analyzer = OptionsAnalyzer(self.client)
    
    def test_timestamp_to_date(self):
        """Test the _timestamp_to_date method."""
        # Test with a known timestamp
        timestamp = 1609459200000  # 2021-01-01 00:00:00 UTC
        expected_date = "2021-01-01"
        
        result = self.analyzer._timestamp_to_date(timestamp)
        
        self.assertEqual(result, expected_date)
    
    def test_fetch_options_data(self):
        """Test the fetch_options_data method."""
        # Mock the client methods
        self.client.get_index_price.return_value = {"index_price": 50000.0}
        self.client.get_option_instruments_by_currency.return_value = [
            {
                "instrument_name": "BTC-31DEC21-60000-C",
                "expiration_timestamp": 1640908800000,
                "creation_timestamp": 1609459200000,
                "strike": 60000.0
            },
            {
                "instrument_name": "BTC-31DEC21-40000-P",
                "expiration_timestamp": 1640908800000,
                "creation_timestamp": 1609459200000,
                "strike": 40000.0
            }
        ]
        self.client.get_option_summary_by_currency.return_value = [
            {
                "instrument_name": "BTC-31DEC21-60000-C",
                "open_interest": 100.0,
                "volume": 50.0,
                "mark_iv": 0.8
            },
            {
                "instrument_name": "BTC-31DEC21-40000-P",
                "open_interest": 200.0,
                "volume": 75.0,
                "mark_iv": 0.7
            }
        ]
        
        # Call the method
        result = self.analyzer.fetch_options_data("BTC")
        
        # Check that the client methods were called correctly
        self.client.get_index_price.assert_called_once_with("BTC")
        self.client.get_option_instruments_by_currency.assert_called_once_with("BTC")
        self.client.get_option_summary_by_currency.assert_called_once_with("BTC")
        
        # Check the result
        self.assertEqual(result["currency"], "BTC")
        self.assertEqual(result["index_price"], 50000.0)
        self.assertEqual(len(result["options"]), 2)
        
        # Check that the options data was combined correctly
        option1 = result["options"][0]
        self.assertEqual(option1["instrument_name"], "BTC-31DEC21-60000-C")
        self.assertEqual(option1["strike"], 60000.0)
        self.assertEqual(option1["open_interest"], 100.0)
        self.assertEqual(option1["mark_iv"], 0.8)
        
        option2 = result["options"][1]
        self.assertEqual(option2["instrument_name"], "BTC-31DEC21-40000-P")
        self.assertEqual(option2["strike"], 40000.0)
        self.assertEqual(option2["open_interest"], 200.0)
        self.assertEqual(option2["mark_iv"], 0.7)
    
    def test_create_options_dataframe(self):
        """Test the create_options_dataframe method."""
        # Set up test data
        self.analyzer.data = {
            "currency": "BTC",
            "index_price": 50000.0,
            "timestamp": datetime.now().isoformat(),
            "options": [
                {
                    "instrument_name": "BTC-31DEC21-60000-C",
                    "expiration_timestamp": 1640908800000,
                    "creation_timestamp": 1609459200000,
                    "strike": 60000.0,
                    "open_interest": 100.0,
                    "volume": 50.0,
                    "mark_iv": 0.8
                },
                {
                    "instrument_name": "BTC-31DEC21-40000-P",
                    "expiration_timestamp": 1640908800000,
                    "creation_timestamp": 1609459200000,
                    "strike": 40000.0,
                    "open_interest": 200.0,
                    "volume": 75.0,
                    "mark_iv": 0.7
                }
            ]
        }
        
        # Call the method
        df = self.analyzer.create_options_dataframe()
        
        # Check the result
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["instrument_name"], "BTC-31DEC21-60000-C")
        self.assertEqual(df.iloc[0]["option_type"], "call")
        self.assertEqual(df.iloc[0]["strike"], 60000.0)
        self.assertEqual(df.iloc[0]["expiration_date"], "2021-12-31")
        
        self.assertEqual(df.iloc[1]["instrument_name"], "BTC-31DEC21-40000-P")
        self.assertEqual(df.iloc[1]["option_type"], "put")
        self.assertEqual(df.iloc[1]["strike"], 40000.0)
        self.assertEqual(df.iloc[1]["expiration_date"], "2021-12-31")
    
    def test_get_calls_and_puts(self):
        """Test the get_calls_and_puts method."""
        # Mock the create_options_dataframe method
        with patch.object(self.analyzer, 'create_options_dataframe') as mock_create_df:
            # Create a mock DataFrame
            import pandas as pd
            mock_df = pd.DataFrame([
                {
                    "instrument_name": "BTC-31DEC21-60000-C",
                    "option_type": "call",
                    "strike": 60000.0
                },
                {
                    "instrument_name": "BTC-31DEC21-40000-P",
                    "option_type": "put",
                    "strike": 40000.0
                }
            ])
            mock_create_df.return_value = mock_df
            
            # Call the method
            calls, puts = self.analyzer.get_calls_and_puts()
            
            # Check the result
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls.iloc[0]["instrument_name"], "BTC-31DEC21-60000-C")
            
            self.assertEqual(len(puts), 1)
            self.assertEqual(puts.iloc[0]["instrument_name"], "BTC-31DEC21-40000-P")


if __name__ == "__main__":
    unittest.main() 