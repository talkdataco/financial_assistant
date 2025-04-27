# financial_assistant/connectors/google_analytics.py

from typing import Dict, List, Any, Optional
from financial_assistant.connectors.base import DataConnector
import os
import json
from datetime import datetime, timedelta


# Google Analytics API libraries
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    MetricType
)
from google.oauth2.service_account import Credentials

class GoogleAnalyticsConnector(DataConnector):
    """Connector for Google Analytics data."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize with GA credentials.
        
        Args:
            credentials: Dictionary containing authentication credentials
                - key_file: Path to service account JSON file
                - property_id: GA4 property ID (format: "properties/123456789")
        """
        super().__init__(credentials)
        self.property_id = credentials.get('property_id')
        self.client = None
        
        # Metric type mapping for proper formatting
        self.metric_types = {
            "conversions": MetricType.TYPE_INTEGER,
            "sessions": MetricType.TYPE_INTEGER,
            "pageviews": MetricType.TYPE_INTEGER,
            "activeUsers": MetricType.TYPE_INTEGER,
            "screenPageViews": MetricType.TYPE_INTEGER,
            "conversions": MetricType.TYPE_INTEGER,
            "transactions": MetricType.TYPE_INTEGER,
            "totalUsers": MetricType.TYPE_INTEGER,
            "newUsers": MetricType.TYPE_INTEGER,
            "eventCount": MetricType.TYPE_INTEGER,
            "eventValue": MetricType.TYPE_INTEGER,
            "purchaseRevenue": MetricType.TYPE_CURRENCY,
            "averagePurchaseRevenue": MetricType.TYPE_CURRENCY,
            "conversionRate": MetricType.TYPE_FLOAT,
            "bounceRate": MetricType.TYPE_FLOAT,
            "engagementRate": MetricType.TYPE_FLOAT,
            "sessionsPerUser": MetricType.TYPE_FLOAT,
            "averageSessionDuration": MetricType.TYPE_SECONDS
        }
    
    def connect(self) -> bool:
        """
        Establish connection to Google Analytics.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            # Check if key file exists
            key_file = self.credentials.get('key_file')
            if not key_file or not os.path.exists(key_file):
                print(f"❌ Google Analytics key file not found: {key_file}")
                return False
                
            # Initialize the client
            credentials = Credentials.from_service_account_file(
                key_file, 
                scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            
            self.client = BetaAnalyticsDataClient(credentials=credentials)
            print(f"✅ Successfully connected to Google Analytics")
            return True
                
        except Exception as e:
            print(f"❌ Failed to connect to Google Analytics: {e}")
            return False
    
    def fetch_data(self, metrics: List[str], 
                  dimensions: Optional[List[str]] = None,
                  start_date: Optional[str] = None, 
                  end_date: Optional[str] = None,
                  filters: Optional[Dict[str, Any]] = None,
                  save_directory: str = None) -> Dict[str, Any]:
        """
        Fetch data from Google Analytics.
        
        Args:
            metrics: List of metrics to fetch (e.g., "conversions", "sessions")
            dimensions: Optional list of dimensions (e.g., "country", "device")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            filters: Optional filters to apply
            
        Returns:
            Dictionary containing the fetched data
        """
        if not self.client:
            success = self.connect()
            if not success:
                return {"error": "Failed to connect to Google Analytics"}
        
        # If dates weren't provided, use last 30 days
        if not start_date or not end_date:
            start_date, end_date = self.parse_time_period("last_30_days")
            
        try:
            # Prepare dimensions
            dimension_list = []
            if dimensions:
                for dim in dimensions:
                    dimension_list.append(Dimension(name=dim))
            
            # Prepare metrics
            metric_list = []
            for metric in metrics:
                # Convert common alternative names to GA4 metric names
                ga_metric = self._convert_metric_name(metric)
                metric_list.append(Metric(name=ga_metric))
            
            # Create the request
            request = RunReportRequest(
                property=self.property_id,
                dimensions=dimension_list,
                metrics=metric_list,
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
            )
            
            # Add dimension filter if provided
            if filters:
                # Implementation of filters would go here
                # This is more complex and would require building filter expressions
                pass
            
            # Execute the report request
            response = self.client.run_report(request)
            
            # Process the response
            result = {
                "source": "google_analytics",
                "start_date": start_date,
                "end_date": end_date,
                "data": {}
            }
            
            # Get comparison data if requested
            comparison_data = None
            if filters and 'comparison_period' in filters and filters['comparison_period']:
                comparison_start, comparison_end = self.parse_time_period(filters['comparison_period'])
                comparison_request = RunReportRequest(
                    property=self.property_id,
                    dimensions=dimension_list,
                    metrics=metric_list,
                    date_ranges=[DateRange(start_date=comparison_start, end_date=comparison_end)]
                )
                comparison_response = self.client.run_report(comparison_request)
                comparison_data = self._process_response(comparison_response, metrics)
            
            # Process current period data
            current_data = self._process_response(response, metrics)
            
            # Combine current and comparison data
            for metric in metrics:
                ga_metric = self._convert_metric_name(metric)
                result["data"][metric] = {
                    "current": current_data.get(ga_metric, 0)
                }
                
                if comparison_data:
                    previous = comparison_data.get(ga_metric, 0)
                    result["data"][metric]["previous"] = previous
                    
                    # Calculate change
                    if previous != 0:
                        change = (current_data.get(ga_metric, 0) - previous) / previous
                        result["data"][metric]["change"] = change
                    else:
                        result["data"][metric]["change"] = 0
                
                # Add dimension data if available
                if dimensions and len(response.rows) > 0:
                    dimension_data = self._process_dimensions(response, dimensions, metrics)
                    if dimension_data:
                        result["data"][metric]["dimensions"] = dimension_data
            
            # Save the data to a file
            filepath = self.save_ga_data_to_json(result, directory=save_directory)
            
            # Add the filepath to the result
            result["_saved_filepath"] = filepath
            return result
            
        except Exception as e:
            print(f"❌ Error fetching data from Google Analytics: {e}")
            return {"error": f"Error fetching data: {str(e)}"}
    
    def _process_response(self, response, metrics: List[str]) -> Dict[str, Any]:
        """Process the GA API response into a usable format."""
        data = {}
        
        if not response.rows:
            return data
            
        # For simple metric totals (no dimensions)
        for i, metric in enumerate(response.metric_headers):
            metric_name = metric.name
            # Sum up values across all rows
            total = sum(float(row.metric_values[i].value) for row in response.rows)
            
            # Convert to appropriate type
            metric_type = self.metric_types.get(metric_name, MetricType.TYPE_FLOAT)
            if metric_type == MetricType.TYPE_INTEGER:
                data[metric_name] = int(total)
            elif metric_type == MetricType.TYPE_CURRENCY or metric_type == MetricType.TYPE_FLOAT:
                data[metric_name] = float(total)
            else:
                data[metric_name] = total
                
        return data
    
    def _process_dimensions(self, response, dimensions: List[str], metrics: List[str]) -> Dict[str, Dict[str, Any]]:
        """Process dimension data from the response."""
        result = {}
        
        for dim in dimensions:
            dim_index = next((i for i, header in enumerate(response.dimension_headers) 
                              if header.name == dim), None)
            if dim_index is None:
                continue
                
            dim_values = {}
            for row in response.rows:
                dim_value = row.dimension_values[dim_index].value
                
                # Get the first metric value for this dimension
                if len(row.metric_values) > 0:
                    metric_index = 0  # Default to first metric
                    metric_value = row.metric_values[metric_index].value
                    
                    # Convert to appropriate type
                    metric_name = self._convert_metric_name(metrics[0])
                    metric_type = self.metric_types.get(metric_name, MetricType.TYPE_FLOAT)
                    
                    if metric_type == MetricType.TYPE_INTEGER:
                        dim_values[dim_value] = int(float(metric_value))
                    elif metric_type == MetricType.TYPE_CURRENCY or metric_type == MetricType.TYPE_FLOAT:
                        dim_values[dim_value] = float(metric_value)
                    else:
                        dim_values[dim_value] = metric_value
            
            result[dim] = dim_values
            
        return result
    
    def _convert_metric_name(self, metric: str) -> str:
        """Convert common metric names to GA4 equivalent."""
        # Mapping of common names to GA4 metric names
        metric_mapping = {
            "conversion_rate": "conversionsRate",
            "conversions": "conversions",
            "page_views": "screenPageViews",
            "pageviews": "screenPageViews", 
            "total_visits": "sessions",
            "visits": "sessions",
            "sessions": "sessions",
            "users": "totalUsers",
            "new_users": "newUsers",
            "bounce_rate": "bounceRate",
            "revenue": "totalRevenue",
            "purchase_revenue": "purchaseRevenue",
            "average_order_value": "averagePurchaseRevenue",
            "session_duration": "averageSessionDuration",
            "engagement_rate": "engagementRate",
            "active_users": "activeUsers",
            "event_count": "eventCount"
        }
        
        # Look up the metric name, or use the original if not found
        return metric_mapping.get(metric.lower(), metric)
    

    def save_ga_data_to_json(data, filename=None, directory="ga_data"):
        """
        Save Google Analytics data to a JSON file.
        
        Args:
            data: The data dictionary returned from Google Analytics
            filename: Optional filename (if None, a timestamp-based name is used)
            directory: Directory to save the file in (will be created if it doesn't exist)
            
        Returns:
            The path to the saved file
        """
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Create a filename with timestamp if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics_str = "_".join(list(data.get("data", {}).keys())[:3])  # Include first 3 metrics in filename
            filename = f"ga_data_{metrics_str}_{timestamp}.json"
        
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Full path to save the file
        filepath = os.path.join(directory, filename)
        
        # Write the data to a file with nice formatting
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Data saved to {filepath}")
        return filepath