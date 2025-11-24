import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from logger.logger import logger

class WeatherForecastTool:
    def __init__(self, api_key: str):
        """
        Initialize the WeatherForecastTool with OpenWeatherMap API key.
        
        Args:
            api_key: OpenWeatherMap API key
        """
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(self, place: str) -> Dict[str, Any]:
        """
        Get current weather for a specific location.
        
        Args:
            place: City name and country code (e.g., 'London,uk')
            
        Returns:
            Dictionary containing weather data
            
        Raises:
            Exception: If API request fails or returns an error
        """
        logger.info(f"🔥 TOOL TRIGGERED: get_current_weather({place})")
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": place,
                "appid": self.api_key,
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise Exception("Empty response from weather API")
                
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Weather API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get weather data: {str(e)}")
    
    def get_forecast_weather(self, place: str, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for a specific location.
        
        Args:
            place: City name and country code (e.g., 'London,uk')
            days: Number of days to forecast (1-5)
            
        Returns:
            Dictionary containing forecast data
            
        Raises:
            Exception: If API request fails or returns an error
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": place,
                "appid": self.api_key,
                "cnt": days * 8  # 8 readings per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise Exception("Empty response from forecast API")
                
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Forecast API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get forecast data: {str(e)}")

# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    
    if not api_key:
        print("Error: OPENWEATHERMAP_API_KEY not found in environment variables")
    else:
        try:
            weather_tool = WeatherForecastTool(api_key)
            
            # Test current weather
            print("Testing current weather for New York,US:")
            current = weather_tool.get_current_weather("New York,US")
            temp_k = current['main']['temp']
            desc = current['weather'][0]['description']
            print(f"Current weather: {temp_k}K, {desc}")
            
            # Test forecast
            print("\nTesting 3-day forecast for New York,US:")
            forecast = weather_tool.get_forecast_weather("New York,US", days=3)
            for item in forecast['list']:
                dt = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d %H:%M')
                temp = item['main']['temp']
                weather = item['weather'][0]['description']
                print(f"{dt}: {temp}K, {weather}")
                
        except Exception as e:
            print(f"Error: {str(e)}")