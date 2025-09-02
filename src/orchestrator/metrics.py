"""
Performance metrics collection system.
Monitors system resources and execution metrics during benchmark tests.
"""

import os
import sys
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.config import SystemConfig


@dataclass
class SystemMetrics:
    """System-level metrics at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available: int
    memory_used: int
    disk_io_read: int
    disk_io_write: int
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0


@dataclass
class ProcessMetrics:
    """Process-specific metrics."""
    pid: int
    cpu_percent: float
    memory_rss: int
    memory_vms: int
    memory_percent: float
    num_threads: int
    io_read_bytes: int = 0
    io_write_bytes: int = 0


@dataclass
class ExecutionMetrics:
    """Complete metrics for a test execution."""
    execution_time: float
    start_timestamp: datetime
    end_timestamp: datetime
    peak_memory_usage: int
    avg_cpu_usage: float
    max_cpu_usage: float
    system_metrics: List[SystemMetrics] = field(default_factory=list)
    process_metrics: List[ProcessMetrics] = field(default_factory=list)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates performance metrics during test execution."""
    
    def __init__(self, system_config: SystemConfig):
        self.config = system_config
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.current_metrics: Optional[ExecutionMetrics] = None
        
        # Monitoring state
        self.target_process: Optional[psutil.Process] = None
        self.system_metrics_history: List[SystemMetrics] = []
        self.process_metrics_history: List[ProcessMetrics] = []
        
        # Sampling configuration
        self.sampling_interval = 0.1  # 100ms
        self.max_samples = 1000  # Limit memory usage
        
        print(" Metrics collector initialized")
    
    def start_monitoring(self, process_id: Optional[int] = None) -> None:
        """Start monitoring system and process metrics."""
        if self.monitoring_active:
            self.stop_monitoring()
        
        self.monitoring_active = True
        self.system_metrics_history.clear()
        self.process_metrics_history.clear()
        
        # Set target process if provided
        if process_id:
            try:
                self.target_process = psutil.Process(process_id)
            except psutil.NoSuchProcess:
                self.target_process = None
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
    
    def stop_monitoring(self) -> ExecutionMetrics:
        """Stop monitoring and return collected metrics."""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
        
        # Compile metrics
        metrics = self._compile_execution_metrics()
        self.current_metrics = metrics
        
        return metrics
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in separate thread."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                if self.config.monitor_resources:
                    system_metrics = self._collect_system_metrics()
                    if system_metrics:
                        self.system_metrics_history.append(system_metrics)
                
                # Collect process metrics
                if self.target_process and self.target_process.is_running():
                    process_metrics = self._collect_process_metrics()
                    if process_metrics:
                        self.process_metrics_history.append(process_metrics)
                
                # Limit history size to prevent memory issues
                if len(self.system_metrics_history) > self.max_samples:
                    self.system_metrics_history = self.system_metrics_history[-self.max_samples:]
                
                if len(self.process_metrics_history) > self.max_samples:
                    self.process_metrics_history = self.process_metrics_history[-self.max_samples:]
                
                time.sleep(self.sampling_interval)
                
            except Exception as e:
                # Continue monitoring even if individual samples fail
                continue
    
    def _collect_system_metrics(self) -> Optional[SystemMetrics]:
        """Collect current system metrics."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read = disk_io.read_bytes if disk_io else 0
            disk_write = disk_io.write_bytes if disk_io else 0
            
            # Network I/O (optional, can be expensive)
            network_read = 0
            network_write = 0
            if self.config.collect_system_info:
                try:
                    network_io = psutil.net_io_counters()
                    if network_io:
                        network_read = network_io.bytes_recv
                        network_write = network_io.bytes_sent
                except Exception:
                    pass
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available,
                memory_used=memory.used,
                disk_io_read=disk_read,
                disk_io_write=disk_write,
                network_bytes_sent=network_write,
                network_bytes_recv=network_read
            )
            
        except Exception:
            return None
    
    def _collect_process_metrics(self) -> Optional[ProcessMetrics]:
        """Collect metrics for the target process."""
        if not self.target_process:
            return None
        
        try:
            # Basic process info
            cpu_percent = self.target_process.cpu_percent()
            memory_info = self.target_process.memory_info()
            memory_percent = self.target_process.memory_percent()
            num_threads = self.target_process.num_threads()
            
            # I/O info (may not be available on all platforms)
            io_read = 0
            io_write = 0
            try:
                io_counters = self.target_process.io_counters()
                if io_counters:
                    io_read = io_counters.read_bytes
                    io_write = io_counters.write_bytes
            except (psutil.AccessDenied, AttributeError):
                pass
            
            return ProcessMetrics(
                pid=self.target_process.pid,
                cpu_percent=cpu_percent,
                memory_rss=memory_info.rss,
                memory_vms=memory_info.vms,
                memory_percent=memory_percent,
                num_threads=num_threads,
                io_read_bytes=io_read,
                io_write_bytes=io_write
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def _compile_execution_metrics(self) -> ExecutionMetrics:
        """Compile collected metrics into execution summary."""
        # Calculate execution time
        start_time = self.system_metrics_history[0].timestamp if self.system_metrics_history else datetime.now()
        end_time = self.system_metrics_history[-1].timestamp if self.system_metrics_history else datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Calculate aggregated metrics
        peak_memory = 0
        cpu_samples = []
        
        # From process metrics
        if self.process_metrics_history:
            peak_memory = max(pm.memory_rss for pm in self.process_metrics_history)
            cpu_samples.extend(pm.cpu_percent for pm in self.process_metrics_history if pm.cpu_percent > 0)
        
        # From system metrics (fallback)
        if not cpu_samples and self.system_metrics_history:
            cpu_samples.extend(sm.cpu_percent for sm in self.system_metrics_history if sm.cpu_percent > 0)
        
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
        max_cpu = max(cpu_samples) if cpu_samples else 0.0
        
        return ExecutionMetrics(
            execution_time=execution_time,
            start_timestamp=start_time,
            end_timestamp=end_time,
            peak_memory_usage=peak_memory,
            avg_cpu_usage=avg_cpu,
            max_cpu_usage=max_cpu,
            system_metrics=self.system_metrics_history.copy(),
            process_metrics=self.process_metrics_history.copy()
        )
    
    def get_current_system_info(self) -> Dict[str, Any]:
        """Get current system information."""
        if not self.config.collect_system_info:
            return {}
        
        try:
            # System info
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            # CPU info
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory info
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk info
            disk_usage = psutil.disk_usage('/')
            
            return {
                'system': {
                    'platform': sys.platform,
                    'python_version': sys.version,
                    'boot_time': boot_time.isoformat(),
                },
                'cpu': {
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None,
                    'max_frequency_mhz': cpu_freq.max if cpu_freq else None,
                },
                'memory': {
                    'total_bytes': memory.total,
                    'available_bytes': memory.available,
                    'percent_used': memory.percent,
                },
                'swap': {
                    'total_bytes': swap.total,
                    'used_bytes': swap.used,
                    'percent_used': swap.percent,
                },
                'disk': {
                    'total_bytes': disk_usage.total,
                    'used_bytes': disk_usage.used,
                    'free_bytes': disk_usage.free,
                    'percent_used': (disk_usage.used / disk_usage.total) * 100,
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def add_custom_metric(self, name: str, value: Any) -> None:
        """Add a custom metric to the current execution."""
        if self.current_metrics:
            self.current_metrics.custom_metrics[name] = value
    
    def export_metrics(self, file_path: str, format: str = 'json') -> None:
        """Export collected metrics to file."""
        if not self.current_metrics:
            raise ValueError("No metrics available to export")
        
        if format.lower() == 'json':
            self._export_metrics_json(file_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_metrics_json(self, file_path: str) -> None:
        """Export metrics to JSON format."""
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object {obj} is not JSON serializable")
        
        metrics_dict = {
            'execution_time': self.current_metrics.execution_time,
            'start_timestamp': self.current_metrics.start_timestamp.isoformat(),
            'end_timestamp': self.current_metrics.end_timestamp.isoformat(),
            'peak_memory_usage': self.current_metrics.peak_memory_usage,
            'avg_cpu_usage': self.current_metrics.avg_cpu_usage,
            'max_cpu_usage': self.current_metrics.max_cpu_usage,
            'custom_metrics': self.current_metrics.custom_metrics,
            'system_metrics_count': len(self.current_metrics.system_metrics),
            'process_metrics_count': len(self.current_metrics.process_metrics),
        }
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metrics_dict, f, indent=2, default=serialize_datetime)


class SimpleMetricsCollector:
    """Simplified metrics collector for lightweight monitoring."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory: int = 0
    
    def start(self) -> None:
        """Start timing."""
        self.start_time = time.perf_counter()
        try:
            process = psutil.Process()
            self.peak_memory = process.memory_info().rss
        except Exception:
            self.peak_memory = 0
    
    def stop(self) -> Dict[str, float]:
        """Stop timing and return metrics."""
        self.end_time = time.perf_counter()
        
        execution_time = 0.0
        if self.start_time:
            execution_time = self.end_time - self.start_time
        
        try:
            process = psutil.Process()
            current_memory = process.memory_info().rss
            self.peak_memory = max(self.peak_memory, current_memory)
        except Exception:
            pass
        
        return {
            'execution_time': execution_time,
            'peak_memory': self.peak_memory,
            'avg_cpu': 0.0  # Not available in simple collector
        }


def create_metrics_collector(system_config: SystemConfig, 
                           simple: bool = False) -> Any:
    """Factory function to create appropriate metrics collector."""
    if simple or not system_config.monitor_resources:
        return SimpleMetricsCollector()
    else:
        return MetricsCollector(system_config)


if __name__ == "__main__":
    # Test metrics collector
    from utils.config import SystemConfig
    
    config = SystemConfig()
    collector = MetricsCollector(config)
    
    print("Testing metrics collection...")
    
    # Start monitoring
    collector.start_monitoring()
    
    # Simulate some work
    time.sleep(1.0)
    
    # Stop monitoring
    metrics = collector.stop_monitoring()
    
    print(f"Execution time: {metrics.execution_time:.3f}s")
    print(f"Peak memory: {metrics.peak_memory_usage / 1024 / 1024:.2f} MB")
    print(f"Average CPU: {metrics.avg_cpu_usage:.1f}%")
    print(f"System samples: {len(metrics.system_metrics)}")
    
    # Test system info
    system_info = collector.get_current_system_info()
    print(f"System info collected: {len(system_info)} categories")