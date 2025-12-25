################################################################################
# Data Formatter Backend for Sanctum Station
################################################################################

import json
import yaml
import base64

class DataFormatterBackend:
    def __init__(self):
        pass
    
    def format_json(self, data, indent=2):
        """Format JSON data"""
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data
            
            formatted = json.dumps(parsed, indent=indent, sort_keys=False)
            return {'success': True, 'data': formatted}
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'JSON parse error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def minify_json(self, data):
        """Minify JSON data"""
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data
            
            minified = json.dumps(parsed, separators=(',', ':'))
            return {'success': True, 'data': minified}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def json_to_yaml(self, data):
        """Convert JSON to YAML"""
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data
            
            yaml_str = yaml.dump(parsed, default_flow_style=False, sort_keys=False)
            return {'success': True, 'data': yaml_str}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def yaml_to_json(self, data):
        """Convert YAML to JSON"""
        try:
            parsed = yaml.safe_load(data)
            json_str = json.dumps(parsed, indent=2, sort_keys=False)
            return {'success': True, 'data': json_str}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_json(self, data):
        """Validate JSON data"""
        try:
            json.loads(data)
            return {'success': True, 'valid': True, 'message': 'Valid JSON'}
        except json.JSONDecodeError as e:
            return {'success': True, 'valid': False, 'message': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_yaml(self, data):
        """Validate YAML data"""
        try:
            yaml.safe_load(data)
            return {'success': True, 'valid': True, 'message': 'Valid YAML'}
        except yaml.YAMLError as e:
            return {'success': True, 'valid': False, 'message': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def encode_base64(self, data):
        """Encode data to base64"""
        try:
            encoded = base64.b64encode(data.encode()).decode()
            return {'success': True, 'data': encoded}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def decode_base64(self, data):
        """Decode base64 data"""
        try:
            decoded = base64.b64decode(data).decode()
            return {'success': True, 'data': decoded}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global formatter instance
formatter = DataFormatterBackend()

def format_json(data, indent=2):
    return formatter.format_json(data, indent)

def minify_json(data):
    return formatter.minify_json(data)

def json_to_yaml(data):
    return formatter.json_to_yaml(data)

def yaml_to_json(data):
    return formatter.yaml_to_json(data)

def validate_json(data):
    return formatter.validate_json(data)

def validate_yaml(data):
    return formatter.validate_yaml(data)

def encode_base64(data):
    return formatter.encode_base64(data)

def decode_base64(data):
    return formatter.decode_base64(data)

def main(stop_event=None):
    """Keep the formatter backend running"""
    import time
    print("Data Formatter backend started")
    while True:
        if stop_event and stop_event.is_set():
            print("Data Formatter backend stopping...")
            break
        time.sleep(0.5)
