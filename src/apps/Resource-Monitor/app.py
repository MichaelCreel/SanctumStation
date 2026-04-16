################################################################################
# Resource Monitor Backend for Sanctum Station
################################################################################

from backend import UsageMonitorAPI

usage_monitor = UsageMonitorAPI()

processor_usage = 0.0
processor_core_usage = []
processor_cores = 0
memory_usage = 0.0
memory_used = 0.0
memory_total = 0.0
swap_memory_usage = 0.0
swap_memory_used = 0.0
swap_memory_total = 0.0
storage_usage = 0.0
storage_used = 0.0
storage_total = 0.0

def update_processor_info():
    global processor_usage, processor_core_usage, processor_cores
    processor_usage = usage_monitor.get_processor_usage()
    processor_core_usage = usage_monitor.get_processor_cores_usage()
    processor_cores = usage_monitor.get_processor_cores()

def update_memory_info():
    global memory_usage, memory_used, memory_total, swap_memory_usage, swap_memory_used, swap_memory_total
    mem = usage_monitor.get_memory_usage()
    memory_used = mem["used"] / (1024 ** 3)
    memory_total = mem["total"] / (1024 ** 3)
    memory_usage = mem["percent"]
    swap = usage_monitor.get_swap_memory_usage()
    swap_memory_used = swap["used"] / (1024 ** 3)
    swap_memory_total = swap["total"] / (1024 ** 3)
    swap_memory_usage = swap["percent"]

def update_storage_info():
    global storage_usage, storage_used, storage_total
    storage = usage_monitor.get_storage_info()
    storage_used = storage["used"] / (1024 ** 3)
    storage_total = storage["total"] / (1024 ** 3)
    storage_usage = storage["percent"]


def get_usage_snapshot():
    update_processor_info()
    update_memory_info()
    update_storage_info()

    return {
        "cpu": {
            "overall": float(processor_usage),
            "cores": [float(value) for value in processor_core_usage],
            "count": int(processor_cores),
        },
        "memory": {
            "percent": float(memory_usage),
            "used": float(memory_used),
            "total": float(memory_total),
        },
        "storage": {
            "percent": float(storage_usage),
            "used": float(storage_used),
            "total": float(storage_total),
        },
    }
