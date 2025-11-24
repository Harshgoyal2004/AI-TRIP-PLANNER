from typing import List, Dict, Any
from langchain.tools import tool
from dotenv import load_dotenv
import os
import requests
from utils.currency_converter import CurrencyConverter

class CurrencyConverterTool:
    def __init__(self):
        """Initialize the CurrencyConverterTool with API key from environment variables."""
        load_dotenv()
        self.api_key = os.getenv("EXCHANGE_RATE_API_KEY")
        if not self.api_key:
            raise ValueError("EXCHANGE_RATE_API_KEY not found in environment variables")
        self.currency_service = CurrencyConverter(self.api_key)
        self.currency_converter_tool_list = self._setup_tools()

    def _setup_tools(self) -> List[Dict[str, Any]]:
        """Setup the currency conversion tools.
        
        Returns:
            List of tool configurations
        """
        @tool
        def get_exchange_rates(base_currency: str = "USD") -> str:
            """
            Get exchange rates for a base currency compared to common currencies.
            
            Args:
                base_currency: Base currency code (default: 'USD')
                
            Returns:
                Formatted string with exchange rates
            """
            try:
                common_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"]
                if base_currency not in common_currencies:
                    common_currencies.append(base_currency)
                
                # Get rates for the base currency
                url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/{base_currency}"
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get('result') != 'success':
                    return f"Error: {data.get('error-type', 'Failed to fetch exchange rates')}"
                
                rates = data.get('conversion_rates', {})
                if not rates:
                    return "No exchange rates available"
                
                # Format the output
                result = [f"💱 Exchange Rates (1 {base_currency} = ?):", "="*40]
                for currency in sorted(common_currencies):
                    if currency != base_currency and currency in rates:
                        result.append(f"• {currency}: {rates[currency]:.4f}")
                
                return "\n".join(result)
                
            except Exception as e:
                return f"Error getting exchange rates: {str(e)}"

        @tool
        def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
            """
            Convert an amount from one currency to another.
            
            Args:
                amount: The amount to convert (must be greater than 0)
                from_currency: Source currency code (e.g., 'USD', 'EUR')
                to_currency: Target currency code (e.g., 'INR', 'GBP')
                
            Returns:
                Formatted string with the conversion result
            """
            try:
                converted_amount = self.currency_service.convert(amount, from_currency, to_currency)
                return (
                    f"💱 Currency Conversion:\n"
                    f"• {amount} {from_currency.upper()} = {converted_amount:.2f} {to_currency.upper()}\n"
                    f"• Exchange Rate: 1 {from_currency.upper()} = {converted_amount/amount:.4f} {to_currency.upper()}"
                )
            except ValueError as e:
                return f"Error: {str(e)}"
            except Exception as e:
                return f"Failed to convert currency: {str(e)}"
        
        return [get_exchange_rates, convert_currency]