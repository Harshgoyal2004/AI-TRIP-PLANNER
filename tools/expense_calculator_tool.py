from utils.expense_calculator import Calculator
from logger.logger import logger
from typing import List
from langchain_core.tools import tool
from langchain_core.tools import tool, StructuredTool

class CalculatorTool:
    def __init__(self):
        self.calculator = Calculator()
        self.calculator_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for the calculator tool"""
        def estimate_total_hotel_cost(price_per_night: str, total_days: str) -> float:
            """Calculate total hotel cost
            
            Args:
                price_per_night: Price per night for the hotel
                total_days: Total number of days for the stay
                
            Returns:
                Total cost of the hotel stay
            """
            logger.info(f"🔥 TOOL TRIGGERED: estimate_total_hotel_cost({price_per_night}, {total_days})")
            try:
                price = float(price_per_night)
                days = float(total_days)
                return self.calculator.multiply(price, days)
            except ValueError:
                return 0.0
        
        def calculate_total_expense(costs: List[float]) -> float:
            """Calculate total expense of the trip
            
            Args:
                costs: List of cost items to sum up
                
            Returns:
                Sum of all provided costs
            """
            logger.info(f"🔥 TOOL TRIGGERED: calculate_total_expense({costs})")
            return self.calculator.calculate_total(*costs)
        
        def calculate_daily_expense_budget(total_cost: str, days: str) -> float:
            """Calculate daily expense budget
            
            Args:
                total_cost: Total budget for the trip
                days: Number of days for the trip
                
            Returns:
                Daily budget amount
            """
            logger.info(f"🔥 TOOL TRIGGERED: calculate_daily_expense_budget({total_cost}, {days})")
            try:
                total = float(total_cost)
                d = int(float(days)) # handle "5.0" or "5"
                return self.calculator.calculate_daily_budget(total, d)
            except ValueError:
                return 0.0
        
        return [
            StructuredTool.from_function(
                func=estimate_total_hotel_cost,
                name="estimate_total_hotel_cost",
                description="Calculate total hotel cost based on price per night and total days"
            ),
            StructuredTool.from_function(
                func=calculate_total_expense,
                name="calculate_total_expense",
                description="Calculate total expense by summing up all individual costs"
            ),
            StructuredTool.from_function(
                func=calculate_daily_expense_budget,
                name="calculate_daily_expense_budget",
                description="Calculate daily expense budget by dividing total cost by number of days"
            )
        ]