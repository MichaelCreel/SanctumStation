################################################################################
# Calculator Backend for Sanctum Station
################################################################################

import math
import re

class CalculatorBackend:
    def __init__(self):
        self.memory = 0
        self.angle_mode = 'deg'  # 'deg' or 'rad'
    
    def save_memory(self, value):
        """Save a value to memory"""
        try:
            self.memory = float(value)
            return {'success': True, 'memory': self.memory}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def recall_memory(self):
        """Recall value from memory"""
        return self.memory
    
    def clear_memory(self):
        """Clear memory"""
        self.memory = 0
        return True
    
    def set_angle_mode(self, mode):
        """Set angle mode to 'deg' or 'rad'"""
        if mode in ['deg', 'rad']:
            self.angle_mode = mode
            return True
        return False
    
    def evaluate(self, expression):
        """Safely evaluate a mathematical expression"""
        try:
            # Replace common symbols
            expr = expression.replace('×', '*').replace('÷', '/').replace('−', '-').replace('^', '**')
            
            # Replace constants
            expr = expr.replace('π', str(math.pi)).replace('e', str(math.e))
            
            # Safe namespace with math functions
            safe_dict = {
                '__builtins__': None,
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
                'pow': pow,
                # Math module functions
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'asin': math.asin,
                'acos': math.acos,
                'atan': math.atan,
                'sinh': math.sinh,
                'cosh': math.cosh,
                'tanh': math.tanh,
                'log': math.log,
                'log10': math.log10,
                'exp': math.exp,
                'pi': math.pi,
                'e': math.e,
                'ceil': math.ceil,
                'floor': math.floor,
                'factorial': math.factorial,
                'degrees': math.degrees,
                'radians': math.radians,
            }
            
            result = eval(expr, safe_dict)
            
            # Check for invalid results
            if math.isnan(result) or math.isinf(result):
                return {'success': False, 'error': 'Invalid result'}
            
            return {'success': True, 'result': result}
            
        except ZeroDivisionError:
            return {'success': False, 'error': 'Division by zero'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global calculator instance
calculator = CalculatorBackend()

def main(stop_event=None):
    """Keep the calculator backend running"""
    import time
    print("Calculator backend started")
    while True:
        if stop_event and stop_event.is_set():
            print("Calculator backend stopping...")
            break
        time.sleep(0.5)
