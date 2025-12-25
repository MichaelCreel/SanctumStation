################################################################################
# API Tester Backend for Sanctum Station
################################################################################

import requests
import json
import time

class APITesterBackend:
    def __init__(self):
        self.history = []
    
    def make_request(self, method, url, headers=None, body=None, timeout=30):
        """Make an HTTP request"""
        try:
            start_time = time.time()
            
            # Parse headers
            header_dict = {}
            if headers:
                try:
                    if isinstance(headers, str):
                        header_dict = json.loads(headers)
                    else:
                        header_dict = headers
                except:
                    # Try to parse as key:value lines
                    for line in headers.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            header_dict[key.strip()] = value.strip()
            
            # Parse body
            data = None
            if body:
                try:
                    if isinstance(body, str):
                        data = json.loads(body)
                    else:
                        data = body
                except:
                    data = body
            
            # Make request
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=header_dict,
                json=data if isinstance(data, dict) else None,
                data=data if not isinstance(data, dict) else None,
                timeout=timeout
            )
            
            elapsed = time.time() - start_time
            
            # Try to parse response as JSON
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            result = {
                'success': True,
                'status_code': response.status_code,
                'status_text': response.reason,
                'headers': dict(response.headers),
                'body': response_data,
                'elapsed': round(elapsed * 1000, 2)  # ms
            }
            
            # Add to history
            self.history.append({
                'method': method,
                'url': url,
                'timestamp': time.time(),
                'status_code': response.status_code,
                'elapsed': result['elapsed']
            })
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timed out'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_history(self):
        """Get request history"""
        return self.history
    
    def clear_history(self):
        """Clear request history"""
        self.history = []
        return True

# Global API tester instance
api_tester = APITesterBackend()

def make_request(method, url, headers=None, body=None, timeout=30):
    return api_tester.make_request(method, url, headers, body, timeout)

def get_history():
    return api_tester.get_history()

def clear_history():
    return api_tester.clear_history()

def main(stop_event=None):
    """Keep the API tester backend running"""
    import time
    print("API Tester backend started")
    while True:
        if stop_event and stop_event.is_set():
            print("API Tester backend stopping...")
            break
        time.sleep(0.5)
