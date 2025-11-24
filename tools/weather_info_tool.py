from typing import List, Dict, Any
from logger.logger import logger
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.tools import tool, StructuredTool
from dotenv import load_dotenv
import os
import requests

from utils.weather_info import WeatherForecastTool

class WeatherInfoTool:
    def __init__(self):
        """Initialize the WeatherInfoTool with API key from environment variables."""
        load_dotenv()
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not self.api_key:
            raise ValueError("OPENWEATHERMAP_API_KEY not found in environment variables")
        self.weather_service = WeatherForecastTool(self.api_key)
        self.weather_tool_list = self._setup_tools()
    
    def _setup_tools(self) -> List[Dict[str, Any]]:
        """Setup the weather information tools."""
        def get_current_weather(place: str) -> str:
            """
            Get detailed current weather for a specific location.
            
            Args:
                place: City name and optional country code (e.g., 'London' or 'London,uk')
                
            Returns:
                Formatted string with current weather information
            """
            try:
                logger.info(f"🔥 TOOL TRIGGERED: get_current_weather({place})")
                weather_data = self.weather_service.get_current_weather(place)
                if not weather_data:
                    return f"Could not fetch weather for {place}"
                
                # Extract weather information
                main_data = weather_data.get('main', {})
                weather_desc = weather_data.get('weather', [{}])[0]
                wind_data = weather_data.get('wind', {})
                sys_data = weather_data.get('sys', {})
                
                return (
                    "🌤️ Current Weather Report\n"
                    "=" * 40 + "\n"
                    f"📍 Location: {weather_data.get('name', 'N/A')}, {sys_data.get('country', 'N/A')}\n"
                    f"🌡️ Temperature: {main_data.get('temp', 'N/A')}K (Feels like: {main_data.get('feels_like', 'N/A')}K)\n"
                    f"📊 Conditions: {weather_desc.get('description', 'N/A').title()}\n"
                    f"💧 Humidity: {main_data.get('humidity', 'N/A')}%\n"
                    f"🌬️ Wind: {wind_data.get('speed', 'N/A')} m/s\n"
                    f"☁️  Cloudiness: {weather_data.get('clouds', {}).get('all', 'N/A')}%\n"
                    f"🌅 Sunrise: {datetime.fromtimestamp(sys_data.get('sunrise', 0)).strftime('%H:%M')} "
                    f"🌇 Sunset: {datetime.fromtimestamp(sys_data.get('sunset', 0)).strftime('%H:%M')}"
                )
            except Exception as e:
                return f"Error getting weather for {place}: {str(e)}"

        def get_weather_forecast(city: str, days: int = 3) -> str:
            """
            Get detailed weather forecast for a city.
            
            Args:
                city: City name and optional country code
                days: Number of days to forecast (1-5, default: 3)
                
            Returns:
                Formatted string with weather forecast
            """
            try:
                logger.info(f"🔥 TOOL TRIGGERED: get_weather_forecast({city}, {days})")
                days = max(1, min(5, int(days)))
                forecast_data = self.weather_service.get_forecast_weather(city, days=days)
                
                if not forecast_data or 'list' not in forecast_data:
                    return f"Could not fetch forecast for {city}"
                
                # Group by day
                daily_forecast = {}
                for item in forecast_data['list']:
                    date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                    if date not in daily_forecast:
                        daily_forecast[date] = []
                    daily_forecast[date].append(item)
                
                # Format the forecast
                result = [
                    f"📅 {days}-Day Weather Forecast for {forecast_data['city']['name']}, {forecast_data['city']['country']}",
                    "=" * 60
                ]
                
                for date, forecasts in list(daily_forecast.items())[:days]:
                    day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
                    daily_high = max(f['main']['temp'] for f in forecasts)
                    daily_low = min(f['main']['temp'] for f in forecasts)
                    conditions = [f['weather'][0]['description'] for f in forecasts]
                    most_common_condition = max(set(conditions), key=conditions.count)
                    
                    result.extend([
                        f"\n📌 {day_name} ({date})",
                        f"   🌡️ {daily_low:.1f}K - {daily_high:.1f}K",
                        f"   📊 {most_common_condition.title()}",
                        "   └── Hourly:"
                    ])
                    
                    for f in forecasts[:4]:  # Show 4 time points per day
                        time = datetime.fromtimestamp(f['dt']).strftime('%H:%M')
                        temp = f['main']['temp']
                        desc = f['weather'][0]['description']
                        result.append(f"      {time}: {temp:.1f}K, {desc}")
                
                return "\n".join(result)
                
            except Exception as e:
                return f"Error getting forecast for {city}: {str(e)}"
        

        
        return [
            StructuredTool.from_function(
                func=get_current_weather,
                name="get_current_weather",
                description="Get detailed current weather for a specific location"
            ),
            StructuredTool.from_function(
                func=get_weather_forecast,
                name="get_weather_forecast",
                description="Get detailed weather forecast for a city"
            )
        ]