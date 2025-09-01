#!/usr/bin/env python3
"""
Memory monitoring script for Celery workers
Helps identify memory leaks and optimize worker configuration
"""
import os
import sys
import psutil
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f}{unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f}TB"

def get_celery_workers():
    """Find all Celery worker processes"""
    workers = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('celery' in cmd and 'worker' in cmd for cmd in cmdline):
                workers.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return workers

def monitor_memory_usage(duration_minutes=30, check_interval=10):
    """Monitor Celery worker memory usage"""
    logger.info(f"Starting memory monitoring for {duration_minutes} minutes")
    logger.info(f"Check interval: {check_interval} seconds")
    logger.info("=" * 80)
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    max_memory_seen = {}
    memory_warnings = 0
    
    while time.time() < end_time:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        workers = get_celery_workers()
        
        if not workers:
            logger.warning(f"[{timestamp}] No Celery workers found")
        else:
            logger.info(f"[{timestamp}] Found {len(workers)} Celery worker(s):")
            
            for i, worker in enumerate(workers, 1):
                try:
                    memory_info = worker.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    cpu_percent = worker.cpu_percent()
                    
                    # Track maximum memory usage
                    pid = worker.pid
                    if pid not in max_memory_seen or memory_mb > max_memory_seen[pid]:
                        max_memory_seen[pid] = memory_mb
                    
                    # Warning thresholds
                    status = "OK"
                    if memory_mb > 2000:  # 2GB
                        status = "CRITICAL"
                        memory_warnings += 1
                    elif memory_mb > 1000:  # 1GB  
                        status = "WARNING"
                    elif memory_mb > 500:  # 500MB
                        status = "WATCH"
                    
                    logger.info(f"  Worker {i} (PID {pid}): "
                              f"Memory: {format_bytes(memory_info.rss)} "
                              f"({memory_mb:.1f}MB) "
                              f"CPU: {cpu_percent:.1f}% "
                              f"Status: {status}")
                    
                    # Show memory breakdown
                    if hasattr(memory_info, 'vms'):
                        logger.info(f"    Virtual: {format_bytes(memory_info.vms)} "
                                  f"Shared: {format_bytes(getattr(memory_info, 'shared', 0))}")
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.warning(f"  Worker {i}: Process no longer accessible")
        
        logger.info("-" * 40)
        time.sleep(check_interval)
    
    # Summary
    logger.info("=" * 80)
    logger.info("MONITORING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Duration: {duration_minutes} minutes")
    logger.info(f"Memory warnings: {memory_warnings}")
    
    if max_memory_seen:
        logger.info("Maximum memory usage per worker:")
        for pid, max_mb in max_memory_seen.items():
            status = "CRITICAL" if max_mb > 2000 else "WARNING" if max_mb > 1000 else "OK"
            logger.info(f"  PID {pid}: {max_mb:.1f}MB ({status})")
        
        avg_max = sum(max_memory_seen.values()) / len(max_memory_seen)
        logger.info(f"Average maximum memory: {avg_max:.1f}MB")
        
        # Recommendations
        logger.info("\nRECOMMENDATIONS:")
        if avg_max > 1500:
            logger.info("- URGENT: Workers using >1.5GB, consider disabling CrewAI tasks")
            logger.info("- Reduce worker_max_tasks_per_child to 5-10")
            logger.info("- Set worker_max_memory_per_child to 300MB")
        elif avg_max > 800:
            logger.info("- Workers using >800MB, monitor closely")  
            logger.info("- Consider reducing task complexity")
        else:
            logger.info("- Memory usage within acceptable limits")

def check_current_status():
    """Quick status check of current workers"""
    workers = get_celery_workers()
    
    if not workers:
        print("No Celery workers currently running")
        return
    
    print(f"Found {len(workers)} active Celery worker(s):")
    print("=" * 60)
    
    total_memory = 0
    for i, worker in enumerate(workers, 1):
        try:
            memory_info = worker.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            total_memory += memory_mb
            
            print(f"Worker {i} (PID {worker.pid}):")
            print(f"  Memory: {format_bytes(memory_info.rss)} ({memory_mb:.1f}MB)")
            print(f"  CPU: {worker.cpu_percent():.1f}%")
            print(f"  Status: {'OK' if memory_mb < 500 else 'HIGH' if memory_mb < 1000 else 'CRITICAL'}")
            print()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"Worker {i}: No longer accessible")
    
    print(f"Total memory usage: {total_memory:.1f}MB")
    print(f"Average per worker: {total_memory/len(workers):.1f}MB")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        check_current_status()
    else:
        duration = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        monitor_memory_usage(duration, interval)