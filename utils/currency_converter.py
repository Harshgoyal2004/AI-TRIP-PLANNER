import requests
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class CurrencyConverter:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CurrencyConverter with an API key.
        
        Args:
            api_key: Optional API key. If not provided, will try to load from environment.
        """
        self.api_key = api_key or os.getenv("EXCHANGE_RATE_API_KEY")
        if not self.api_key:
            raise ValueError("EXCHANGE_RATE_API_KEY not found in environment variables")
        self.base_url = "https://v6.exchangerate-api.com/v6"
    
    def get_exchange_rates(self, base_currency: str = "USD") -> Dict[str, float]:
        """
        Get all exchange rates for a base currency.
        
        Args:
            base_currency: 3-letter currency code (default: 'USD')
            
        Returns:
            Dictionary of currency codes to exchange rates
        """
        try:
            url = f"{self.base_url}/{self.api_key}/latest/{base_currency.upper()}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get('result') != 'success':
                raise ValueError(f"API Error: {data.get('error-type', 'Unknown error')}")
            
            # Ensure all rates are floats
            rates = data.get('conversion_rates', {})
            return {k: float(v) for k, v in rates.items()}
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch exchange rates: {str(e)}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid API response: {str(e)}")
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount
        """
        try:
            # Ensure amount is a float
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0")
            
            # Get exchange rates
            rates = self.get_exchange_rates(from_currency.upper())
            
            # Ensure target currency exists in rates
            target_currency = to_currency.upper()
            if target_currency not in rates:
                raise ValueError(f"Currency {to_currency} not found in exchange rates")
            
            # Calculate and return the converted amount
            return amount * rates[target_currency]
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid input: {str(e)}")
        except Exception as e:
            raise Exception(f"Conversion failed: {str(e)}")

# Example usage
if __name__ == "__main__":
    try:
        # Initialize the converter
        converter = CurrencyConverter()
        
        # Test conversion
        amount = 100
        from_curr = "USD"
        to_curr = "INR"
        
        # Get exchange rates
        print(f"Getting exchange rates for {from_curr}...")
        rates = converter.get_exchange_rates(from_curr)
        print(f"1 {from_curr} = {rates.get(to_curr, 'N/A')} {to_curr}")
        
        # Test conversion
        print(f"\nConverting {amount} {from_curr} to {to_curr}...")
        result = converter.convert(amount, from_curr, to_curr)
        print(f"{amount} {from_curr} = {result:.2f} {to_curr}")
        
        # Test error handling
        print("\nTesting error handling...")
        try:
            print(converter.convert(-100, "USD", "INR"))
        except ValueError as e:
            print(f"Expected error: {e}")
            
        try:
            print(converter.convert(100, "USD", "XYZ"))
        except ValueError as e:
            print(f"Expected error: {e}")
            
    except Exception as e:
        print(f"Error: {str(e)}")