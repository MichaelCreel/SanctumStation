################################################################################
# Git Manager Backend for Sanctum Station
################################################################################

import subprocess
import os
import json

class GitManagerBackend:
    def __init__(self):
        self.repo_path = os.path.expanduser('~')
    
    def set_repo_path(self, path):
        """Set the current repository path"""
        if os.path.isdir(path):
            self.repo_path = os.path.abspath(path)
            return {'success': True, 'path': self.repo_path}
        return {'success': False, 'error': 'Invalid path'}
    
    def get_repo_path(self):
        """Get the current repository path"""
        return self.repo_path
    
    def execute_git_command(self, command):
        """Execute a git command"""
        try:
            result = subprocess.run(
                f'git {command}',
                shell=True,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self):
        """Get git status"""
        result = self.execute_git_command('status --porcelain')
        if result['success']:
            files = []
            for line in result['output'].split('\n'):
                if line.strip():
                    status = line[:2]
                    filepath = line[3:]
                    files.append({
                        'status': status.strip(),
                        'path': filepath
                    })
            return {'success': True, 'files': files}
        return result
    
    def get_branches(self):
        """Get all branches"""
        result = self.execute_git_command('branch -a')
        if result['success']:
            branches = []
            current = None
            for line in result['output'].split('\n'):
                if line.strip():
                    is_current = line.startswith('*')
                    branch = line.replace('*', '').strip()
                    if is_current:
                        current = branch
                    branches.append({
                        'name': branch,
                        'current': is_current
                    })
            return {'success': True, 'branches': branches, 'current': current}
        return result
    
    def get_log(self, count=10):
        """Get recent commits"""
        result = self.execute_git_command(f'log -n {count} --pretty=format:"%H|%an|%ae|%ad|%s"')
        if result['success']:
            commits = []
            for line in result['output'].split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) == 5:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'email': parts[2],
                            'date': parts[3],
                            'message': parts[4]
                        })
            return {'success': True, 'commits': commits}
        return result
    
    def commit(self, message):
        """Create a commit"""
        # First add all changes
        add_result = self.execute_git_command('add -A')
        if not add_result['success']:
            return add_result
        
        # Then commit
        result = self.execute_git_command(f'commit -m "{message}"')
        return result
    
    def checkout(self, branch):
        """Checkout a branch"""
        result = self.execute_git_command(f'checkout {branch}')
        return result
    
    def pull(self):
        """Pull from remote"""
        result = self.execute_git_command('pull')
        return result
    
    def push(self):
        """Push to remote"""
        result = self.execute_git_command('push')
        return result
    
    def create_branch(self, branch_name):
        """Create a new branch"""
        result = self.execute_git_command(f'checkout -b {branch_name}')
        return result

# Global git manager instance
git_manager = GitManagerBackend()

def set_repo_path(path):
    return git_manager.set_repo_path(path)

def get_repo_path():
    return git_manager.get_repo_path()

def execute_git_command(command):
    return git_manager.execute_git_command(command)

def get_status():
    return git_manager.get_status()

def get_branches():
    return git_manager.get_branches()

def get_log(count=10):
    return git_manager.get_log(count)

def commit(message):
    return git_manager.commit(message)

def checkout(branch):
    return git_manager.checkout(branch)

def pull():
    return git_manager.pull()

def push():
    return git_manager.push()

def create_branch(branch_name):
    return git_manager.create_branch(branch_name)

def main(stop_event=None):
    """Keep the git manager backend running"""
    import time
    print("Git Manager backend started")
    while True:
        if stop_event and stop_event.is_set():
            print("Git Manager backend stopping...")
            break
        time.sleep(0.5)
