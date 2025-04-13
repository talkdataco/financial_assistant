# financial_assistant/connectors/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class DataConnector(ABC):
    """Abstract base class for all data source connectors."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize the connector with credentials.
        
        Args:
            credentials: Dictionary containing authentication credentials
        """
        self.credentials = credentials
        self._client = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the data source.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def fetch_data(self, metrics: List[str], 
                  dimensions: Optional[List[str]] = None,
                  start_date: Optional[str] = None, 
                  end_date: Optional[str] = None,
                  filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch data from the source based on specified parameters.
        
        Args:
            metrics: List of metrics to fetch
            dimensions: Optional dimensions to segment data by
            start_date: Start date for the data range
            end_date: End date for the data range
            filters: Optional filters to apply
            
        Returns:
            Dictionary containing the fetched data
        """
        pass
    
    def parse_time_period(self, time_period: str) -> tuple:
        """
        Convert a time period string to actual start and end dates.
        
        Args:
            time_period: String indicating time period (e.g., 'last_month')
            
        Returns:
            Tuple of (start_date, end_date) as strings in YYYY-MM-DD format
        """
        today = datetime.now()
        
        if time_period == "last_month":
            # First day of previous month
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            # Last day of previous month
            end_date = today.replace(day=1) - timedelta(days=1)
        elif time_period == "last_week":
            # 7 days ago
            start_date = today - timedelta(days=7)
            end_date = today
        elif time_period == "last_30_days":
            start_date = today - timedelta(days=30)
            end_date = today
        elif time_period == "year_to_date":
            start_date = today.replace(month=1, day=1)
            end_date = today
        elif time_period == "q1":
            year = today.year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 3, 31)
        # Add more time period parsing as needed
        else:
            # Default to last 30 days
            start_date = today - timedelta(days=30)
            end_date = today
            
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')