################################################################################
# System Monitor Backend for Sanctum Station
################################################################################

import psutil
import platform
import time

class SystemMonitorBackend:
    def __init__(self):
        pass
    
    def get_cpu_info(self):
        """Get CPU information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            
            return {
                'success': True,
                'percent': psutil.cpu_percent(interval=0.1),
                'per_cpu': cpu_percent,
                'count': psutil.cpu_count(),
                'frequency': {
                    'current': cpu_freq.current if cpu_freq else 0,
                    'min': cpu_freq.min if cpu_freq else 0,
                    'max': cpu_freq.max if cpu_freq else 0
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_memory_info(self):
        """Get memory information"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'success': True,
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_disk_info(self):
        """Get disk information"""
        try:
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except:
                    continue
            
            return {
                'success': True,
                'partitions': partitions
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_network_info(self):
        """Get network information"""
        try:
            net_io = psutil.net_io_counters()
            
            return {
                'success': True,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_process_list(self, limit=10):
        """Get list of top processes by CPU usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'cpu_percent': info['cpu_percent'] or 0,
                        'memory_percent': info['memory_percent'] or 0
                    })
                except:
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return {
                'success': True,
                'processes': processes[:limit]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_system_info(self):
        """Get general system information"""
        try:
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            return {
                'success': True,
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'uptime': uptime
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global system monitor instance
system_monitor = SystemMonitorBackend()

def get_cpu_info():
    return system_monitor.get_cpu_info()

def get_memory_info():
    return system_monitor.get_memory_info()

def get_disk_info():
    return system_monitor.get_disk_info()

def get_network_info():
    return system_monitor.get_network_info()

def get_process_list(limit=10):
    return system_monitor.get_process_list(limit)

def get_system_info():
    return system_monitor.get_system_info()

def main(stop_event=None):
    """Keep the system monitor backend running"""
    import time
    print("System Monitor backend started")
    while True:
        if stop_event and stop_event.is_set():
            print("System Monitor backend stopping...")
            break
        time.sleep(0.5)
