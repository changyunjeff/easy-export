import os

def worker_count() -> int:
    """
    根据系统的CPU核心数返回workers数量
    """
    return os.cpu_count() or 1
