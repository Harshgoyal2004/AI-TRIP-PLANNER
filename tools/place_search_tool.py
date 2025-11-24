import os
from logger.logger import logger
from utils.place_info_search import GooglePlaceSearchTool, TavilyPlaceSearchTool
from typing import List
from langchain_core.tools import tool
from langchain_core.tools import tool, StructuredTool
from dotenv import load_dotenv

class PlaceSearchTool:
    def __init__(self):
        load_dotenv()
        self.google_api_key = os.environ.get("GPLACES_API_KEY")
        self.google_places_search = GooglePlaceSearchTool(self.google_api_key)
        self.tavily_search = TavilyPlaceSearchTool()
        self.place_search_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for the place search tool"""
        def search_attractions(place:str) -> str:
            """Search attractions of a place
            
            Args:
                place: Name of the place to search attractions for
                
            Returns:
                String containing information about attractions in the specified place
            """
            try:
                logger.info(f"🔥 TOOL TRIGGERED: search_attractions({place})")
                attraction_result = self.google_places_search.google_search_attractions(place)
                if attraction_result:
                    return f"Following are the attractions of {place} as suggested by google: {attraction_result}"
            except Exception as e:
                tavily_result = self.tavily_search.tavily_search_attractions(place)
                return f"Google cannot find the details due to {e}. \nFollowing are the attractions of {place}: {tavily_result}"  ## Fallback search using tavily in case google places fail
        
        def search_restaurants(place:str) -> str:
            """Search restaurants of a place
            
            Args:
                place: Name of the place to search restaurants for
                
            Returns:
                String containing information about restaurants in the specified place
            """
            try:
                logger.info(f"🔥 TOOL TRIGGERED: search_restaurants({place})")
                restaurants_result = self.google_places_search.google_search_restaurants(place)
                if restaurants_result:
                    return f"Following are the restaurants of {place} as suggested by google: {restaurants_result}"
            except Exception as e:
                tavily_result = self.tavily_search.tavily_search_restaurants(place)
                return f"Google cannot find the details due to {e}. \nFollowing are the restaurants of {place}: {tavily_result}"  ## Fallback search using tavily in case google places fail
        
        def search_activities(place:str) -> str:
            """Search activities of a place
            
            Args:
                place: Name of the place to search activities for
                
            Returns:
                String containing information about activities in the specified place
            """
            try:
                logger.info(f"🔥 TOOL TRIGGERED: search_activities({place})")
                restaurants_result = self.google_places_search.google_search_activity(place)
                if restaurants_result:
                    return f"Following are the activities in and around {place} as suggested by google: {restaurants_result}"
            except Exception as e:
                tavily_result = self.tavily_search.tavily_search_activity(place)
                return f"Google cannot find the details due to {e}. \nFollowing are the activities of {place}: {tavily_result}"  ## Fallback search using tavily in case google places fail
        
        def search_transportation(place:str) -> str:
            """Search transportation of a place
            
            Args:
                place: Name of the place to search transportation options for
                
            Returns:
                String containing information about transportation options in the specified place
            """
            try:
                logger.info(f"🔥 TOOL TRIGGERED: search_transportation({place})")
                restaurants_result = self.google_places_search.google_search_transportation(place)
                if restaurants_result:
                    return f"Following are the modes of transportation available in {place} as suggested by google: {restaurants_result}"
            except Exception as e:
                tavily_result = self.tavily_search.tavily_search_transportation(place)
                return f"Google cannot find the details due to {e}. \nFollowing are the modes of transportation available in {place}: {tavily_result}"  ## Fallback search using tavily in case google places fail
        

        
        return [
            StructuredTool.from_function(
                func=search_attractions,
                name="search_attractions",
                description="Search for tourist attractions in a specific location"
            ),
            StructuredTool.from_function(
                func=search_restaurants,
                name="search_restaurants",
                description="Search for restaurants in a specific location"
            ),
            StructuredTool.from_function(
                func=search_activities,
                name="search_activities",
                description="Search for activities to do in a specific location"
            ),
            StructuredTool.from_function(
                func=search_transportation,
                name="search_transportation",
                description="Search for available transportation options in a specific location"
            )
        ]