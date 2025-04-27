import re
from typing import Any, Dict, List, Union

class FinancialCalculator:
    def __init__(self, data_context: Dict[str, Any] = None):
        """
        Initialize the calculator with an optional data context.
        
        :param data_context: A dictionary containing metric values
        """
        self.data_context = data_context or {}
        
        # Define supported mathematical functions
        self.functions = {
            'avg': self._avg,
            'sum': self._sum,
            'max': self._max,
            'min': self._min
        }
    
    def _resolve_metric(self, metric: str) -> Union[int, float]:
        """
        Resolve a metric from the data context.
        
        :param metric: Metric identifier
        :return: Metric value
        """
        if metric in self.data_context:
            return self.data_context[metric]
        raise ValueError(f"Metric '{metric}' not found in data context")
    
    def evaluate_expression(self, expression: str) -> Union[int, float]:
        """
        Evaluate a mathematical expression with support for metrics and functions.
        
        :param expression: Mathematical expression to evaluate
        :return: Calculated result
        """
        # First, try to parse as a direct metric
        if re.match(r'^[A-Za-z:_]+$', expression):
            return self._resolve_metric(expression)
        
        # Try to parse as a function call
        func_match = re.match(r'^(\w+)\((.*)\)$', expression)
        if func_match:
            function = func_match.group(1)
            args_str = func_match.group(2)
            
            # Split arguments, handling potential nested structures
            args = [arg.strip() for arg in args_str.split(',')]
            
            # Resolve each argument (either a metric or a constant)
            resolved_args = []
            for arg in args:
                if re.match(r'^[A-Za-z:_]+$', arg):
                    resolved_args.append(self._resolve_metric(arg))
                else:
                    try:
                        resolved_args.append(float(arg))
                    except ValueError:
                        raise ValueError(f"Cannot resolve argument: {arg}")
            
            # Call the function
            if function not in self.functions:
                raise ValueError(f"Unsupported function: {function}")
            
            return self.functions[function](*resolved_args)
        
        # Try to parse as a numeric constant
        try:
            return float(expression)
        except ValueError:
            raise ValueError(f"Unable to parse expression: {expression}")
    
    def decompose_calculation_query(self, query: str) -> Dict[str, Any]:
        """
        Decompose a calculation query into components.
        
        :param query: Calculation query string
        :return: Decomposed query components
        """
        # Example query format: "avg(GA:sessions:current, 90000)"
        match = re.match(r'(\w+)\((.*)\)', query)
        if not match:
            raise ValueError(f"Invalid query format: {query}")
        
        function = match.group(1)
        args_str = match.group(2)
        
        # Split arguments, handling potential nested structures
        args = [arg.strip() for arg in args_str.split(',')]
        
        return {
            'function': function,
            'arguments': args
        }
    
    # Helper functions for mathematical operations
    def _avg(self, *args):
        """Calculate average of given arguments"""
        if not args:
            raise ValueError("No arguments provided")
        return sum(args) / len(args)
    
    def _sum(self, *args):
        """Calculate sum of given arguments"""
        return sum(args)
    
    def _max(self, *args):
        """Find maximum of given arguments"""
        return max(args)
    
    def _min(self, *args):
        """Find minimum of given arguments"""
        return min(args)