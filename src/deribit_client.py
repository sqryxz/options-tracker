import os
import json
import time
import requests
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DeribitClient:
    """
    Client for interacting with the Deribit API to fetch options data.
    """
    
    BASE_URL = "https://www.deribit.com/api/v2"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the Deribit API client.
        
        Args:
            api_key: Deribit API key (optional, will use env var if not provided)
            api_secret: Deribit API secret (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.getenv("DERIBIT_API_KEY")
        self.api_secret = api_secret or os.getenv("DERIBIT_API_SECRET")
        self.session = requests.Session()
    
    def _make_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to the Deribit API.
        
        Args:
            method: API method to call
            params: Parameters for the API call
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.BASE_URL}/public/{method}"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Add authentication if API key is available
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        response = self.session.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
        
        result = response.json()
        
        if "error" in result and result["error"]:
            raise Exception(f"API error: {result['error']}")
        
        return result["result"] if "result" in result else result
    
    def get_instruments(self, currency: str, kind: str = "option", expired: bool = False) -> List[Dict[str, Any]]:
        """
        Get available instruments for a specific currency.
        
        Args:
            currency: Currency code (BTC or ETH)
            kind: Instrument kind (option, future, etc.)
            expired: Whether to include expired instruments
            
        Returns:
            List of available instruments
        """
        params = {
            "currency": currency.upper(),
            "kind": kind,
            "expired": "true" if expired else "false"
        }
        
        return self._make_request("get_instruments", params)
    
    def get_order_book(self, instrument_name: str) -> Dict[str, Any]:
        """
        Get order book for a specific instrument.
        
        Args:
            instrument_name: Name of the instrument
            
        Returns:
            Order book data
        """
        params = {
            "instrument_name": instrument_name
        }
        
        return self._make_request("get_order_book", params)
    
    def get_instrument_summary(self, instrument_name: str) -> Dict[str, Any]:
        """
        Get summary for a specific instrument.
        
        Args:
            instrument_name: Name of the instrument
            
        Returns:
            Instrument summary data
        """
        params = {
            "instrument_name": instrument_name
        }
        
        return self._make_request("get_book_summary_by_instrument", params)
    
    def get_index_price(self, currency: str) -> Dict[str, Any]:
        """
        Get current index price for a currency.
        
        Args:
            currency: Currency code (BTC or ETH)
            
        Returns:
            Index price data
        """
        params = {
            "index_name": f"{currency.lower()}_usd"
        }
        
        return self._make_request("get_index_price", params)
    
    def get_option_instruments_by_currency(self, currency: str) -> List[Dict[str, Any]]:
        """
        Get all option instruments for a specific currency.
        
        Args:
            currency: Currency code (BTC or ETH)
            
        Returns:
            List of option instruments
        """
        return self.get_instruments(currency, kind="option")
    
    def get_option_chain(self, currency: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the full options chain for a currency, organized by expiration date.
        
        Args:
            currency: Currency code (BTC or ETH)
            
        Returns:
            Dictionary with expiration dates as keys and lists of options as values
        """
        instruments = self.get_option_instruments_by_currency(currency)
        
        # Group instruments by expiration date
        options_chain = {}
        for instrument in instruments:
            expiration = instrument["expiration_timestamp"]
            if expiration not in options_chain:
                options_chain[expiration] = []
            options_chain[expiration].append(instrument)
        
        return options_chain
    
    def get_option_summary_by_currency(self, currency: str) -> List[Dict[str, Any]]:
        """
        Get summary for all options of a specific currency.
        
        Args:
            currency: Currency code (BTC or ETH)
            
        Returns:
            List of option summaries
        """
        params = {
            "currency": currency.upper(),
            "kind": "option"
        }
        
        return self._make_request("get_book_summary_by_currency", params) 