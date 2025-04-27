# financial_assistant/utils/calculator.py

import re
import ast
import operator
from typing import Dict, Any, Union, List, Tuple
import math
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialCalculator:
    """
    Calculator utility for performing financial calculations on metrics.
    Supports referencing values from fetched data and evaluating expressions.
    """
    
    # Define operators
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,  # Unary subtraction
    }
    
    # Built-in functions
    _functions = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'avg': lambda values: sum(values) / len(values) if values else 0,
        'growth_rate': lambda current, previous: (current - previous) / previous if previous != 0 else 0,
        'percent': lambda value: value * 100,
        'percentage_change': lambda current, previous: ((current - previous) / previous) * 100 if previous != 0 else 0,
    }
    
    def __init__(self, data_context: Dict[str, Any] = None):
        """
        Initialize the calculator with an optional data context.
        
        Args:
            data_context: Dictionary containing metric data from various sources
        """
        self.data_context = data_context or {}
        
    def update_context(self, data_context: Dict[str, Any]) -> None:
        """
        Update the data context.
        
        Args:
            data_context: Dictionary containing metric data from various sources
        """
        self.data_context = data_context
        
    def extract_value(self, source: str, metric: str, field: str = "current") -> float:
        """
        Extract a specific value from the data context.
        
        Args:
            source: Source name (e.g., 'google_analytics', 'stripe')
            metric: Metric name (e.g., 'conversion_rate', 'revenue')
            field: Field to extract (e.g., 'current', 'previous', 'change')
            
        Returns:
            The extracted value as a float
        """
        try:
            # Navigate through nested data structure
            if source in self.data_context.get("data", {}):
                source_data = self.data_context["data"][source]
                if "data" in source_data and metric in source_data["data"]:
                    metric_data = source_data["data"][metric]
                    if field in metric_data:
                        return float(metric_data[field])
            
            # If we get here, the path wasn't found
            logger.warning(f"Could not find {source}.{metric}.{field} in data context")
            return 0.0
        except Exception as e:
            logger.error(f"Error extracting value for {source}.{metric}.{field}: {e}")
            return 0.0
            
    def evaluate(self, expression: str) -> Union[float, str]:
        """
        Evaluate a mathematical expression, which can include references to metrics.
        
        Args:
            expression: Expression to evaluate, can include metric references like 
                        'GA:conversion_rate:current * 100' or financial functions
        
        Returns:
            The calculated result or an error message
        """
        try:
            # Replace metric references with their values
            processed_expr = self._process_metric_references(expression)
            
            # Parse and evaluate the expression
            return self._evaluate_ast(ast.parse(processed_expr, mode='eval').body)
            
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return f"Error: {str(e)}"
    
    def _process_metric_references(self, expression: str) -> str:
        """
        Process metric references in the expression and replace them with actual values.
        
        Args:
            expression: Expression containing metric references
            
        Returns:
            Expression with metric references replaced by their values
        """
        # Define a pattern for metric references: SOURCE:METRIC:FIELD
        pattern = r'([A-Za-z_]+):([A-Za-z_]+):([A-Za-z_]+)'
        
        def replace_match(match):
            source, metric, field = match.groups()
            
            # Map source shortcuts to full names
            source_mapping = {
                'GA': 'google_analytics',
                'S': 'stripe',
                'SF': 'shopify',
                # Add more mappings as needed
            }
            
            # Get the full source name if a shortcut was used
            full_source = source_mapping.get(source, source)
            
            # Extract the value
            value = self.extract_value(full_source, metric, field)
            
            # Return the string representation of the value
            return str(value)
        
        # Replace all metric references
        return re.sub(pattern, replace_match, expression)
    
    def _evaluate_ast(self, node):
        """
        Recursively evaluate an AST node.
        
        Args:
            node: AST node to evaluate
            
        Returns:
            Evaluated result
        """
        # Handle numbers
        if isinstance(node, ast.Num):
            return node.n
            
        # Handle names (variables)
        elif isinstance(node, ast.Name):
            if node.id in self._functions:
                return self._functions[node.id]
            else:
                raise NameError(f"Name '{node.id}' is not defined")
                
        # Handle binary operations
        elif isinstance(node, ast.BinOp):
            left = self._evaluate_ast(node.left)
            right = self._evaluate_ast(node.right)
            op = type(node.op)
            if op in self._operators:
                return self._operators[op](left, right)
            else:
                raise TypeError(f"Unsupported operator: {op}")
                
        # Handle unary operations (like -x)
        elif isinstance(node, ast.UnaryOp):
            operand = self._evaluate_ast(node.operand)
            op = type(node.op)
            if op in self._operators:
                return self._operators[op](operand)
            else:
                raise TypeError(f"Unsupported unary operator: {op}")
                
        # Handle function calls
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name in self._functions:
                args = [self._evaluate_ast(arg) for arg in node.args]
                return self._functions[func_name](*args)
            else:
                raise NameError(f"Function '{func_name}' is not defined")
                
        # Handle other AST nodes
        else:
            raise TypeError(f"Unsupported AST node type: {type(node)}")
    
    def decompose_calculation_query(self, query: str) -> List[Tuple[str, str]]:
        """
        Analyze a complex query and break it down into sub-queries and calculations.
        
        Args:
            query: The complex query to decompose
            
        Returns:
            List of (sub_query, calculation) tuples
        """
        # This is a placeholder for more sophisticated decomposition logic
        # In a real implementation, you'd use NLP to break down the query
        
        # Example patterns for metric-related calculations
        calculation_patterns = [
            # Pattern: METRIC from SOURCE compared to PREVIOUS PERIOD
            (r'([\w\s]+) from ([\w\s]+) compared to', 
             "{0}:{1}:percentage_change"),
             
            # Pattern: average/mean of X and Y
            (r'(average|mean) of ([\w\s]+) and ([\w\s]+)',
             "avg([{0}:{1}:current, {0}:{2}:current])"),
             
            # Pattern: total/sum of X and Y
            (r'(total|sum) of ([\w\s]+) and ([\w\s]+)',
             "sum([{0}:{1}:current, {0}:{2}:current])"),
             
            # Pattern: ratio of X to Y
            (r'ratio of ([\w\s]+) to ([\w\s]+)',
             "{0}:{1}:current / {0}:{2}:current"),
        ]
        
        # This is simplified logic - a real implementation would be more robust
        results = []
        for pattern, calc_template in calculation_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Extract components and create a calculation
                # This is very simplified - real implementation would be more robust
                components = match.groups()
                sub_query = f"Get {components[0]} from {components[1]}"
                calculation = calc_template.format(*components)
                results.append((sub_query, calculation))
                
        return results or [(query, None)]  # Return original query if no decomposition
    
    def explain_calculation(self, expression: str, result: float) -> str:
        """
        Generate an explanation of how a calculation was performed.
        
        Args:
            expression: The expression that was evaluated
            result: The result of the calculation
            
        Returns:
            Human-readable explanation
        """
        # This is a simplified implementation
        # A more sophisticated version would parse the expression and explain each step
        
        return (
            f"I calculated this by evaluating the expression: {expression}\n"
            f"This gave us the result: {result:.2f}"
        )