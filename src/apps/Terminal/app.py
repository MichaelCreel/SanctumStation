################################################################################
# Terminal Backend for Sanctum Station
################################################################################

import subprocess
import os
import threading
import queue

class TerminalBackend:
    def __init__(self):
        self.history = []
        self.current_dir = os.path.expanduser('~')
    
    def execute_command(self, command):
        """Execute a shell command and return the output
        
        WARNING: Uses shell=True for full shell feature support (pipes, redirects, etc).
        This is a local developer tool - do not expose to untrusted users or networks.
        """
        try:
            # Handle cd command specially to maintain state
            if command.strip().startswith('cd '):
                path = command.strip()[3:].strip()
                if not path:
                    path = os.path.expanduser('~')
                elif path.startswith('~'):
                    path = os.path.expanduser(path)
                elif not os.path.isabs(path):
                    path = os.path.join(self.current_dir, path)
                
                if os.path.isdir(path):
                    self.current_dir = os.path.abspath(path)
                    return {
                        'success': True,
                        'output': '',
                        'cwd': self.current_dir
                    }
                else:
                    return {
                        'success': False,
                        'output': f'cd: {path}: No such file or directory',
                        'cwd': self.current_dir
                    }
            
            # Execute other commands
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            self.history.append({
                'command': command,
                'output': output,
                'cwd': self.current_dir
            })
            
            return {
                'success': result.returncode == 0,
                'output': output,
                'cwd': self.current_dir
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': 'Command timed out after 30 seconds',
                'cwd': self.current_dir
            }
        except Exception as e:
            return {
                'success': False,
                'output': f'Error: {str(e)}',
                'cwd': self.current_dir
            }
    
    def get_current_dir(self):
        """Get the current working directory"""
        return self.current_dir
    
    def get_history(self):
        """Get command history"""
        return self.history
    
    def clear_history(self):
        """Clear command history"""
        self.history = []
        return True

# Global terminal instance
terminal = TerminalBackend()

def execute_command(command):
    """Wrapper function for API access"""
    return terminal.execute_command(command)

def get_current_dir():
    """Wrapper function for API access"""
    return terminal.get_current_dir()

def get_history():
    """Wrapper function for API access"""
    return terminal.get_history()

def clear_history():
    """Wrapper function for API access"""
    return terminal.clear_history()

def main(stop_event=None):
    """Keep the terminal backend running"""
    import time
    print("Terminal backend started")
    while True:
        if stop_event and stop_event.is_set():
            print("Terminal backend stopping...")
            break
        time.sleep(0.5)
