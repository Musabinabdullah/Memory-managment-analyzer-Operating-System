"""
Process Generator for Memory Management Simulator
Generates processes with various characteristics for testing
"""

import random
import time
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ProcessType(Enum):
    """Types of processes for different simulation scenarios"""
    INTERACTIVE = "Interactive"
    BATCH = "Batch"
    SYSTEM = "System"
    REAL_TIME = "Real-time"
    MEMORY_INTENSIVE = "Memory Intensive"


@dataclass
class Process:
    """Represents a process in the system"""
    pid: str
    size: int
    arrival_time: float
    duration: float = 30.0
    priority: int = 1
    process_type: ProcessType = ProcessType.INTERACTIVE
    state: str = "READY"
    
    def __repr__(self):
        return f"Process({self.pid}: {self.size}KB)"


class ProcessGenerator:
    """Generates processes with realistic characteristics"""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize process generator"""
        if seed:
            random.seed(seed)
        self.process_count = 0
        self.generated_history = []
    
    def generate_pid(self) -> str:
        """Generate a unique process ID"""
        self.process_count += 1
        return f"P{self.process_count:04d}"
    
    def generate_random_process(self, min_size: int = 16, max_size: int = 1024) -> Process:
        """Generate a process with random characteristics"""
        size = random.randint(min_size, max_size)
        duration = random.uniform(10, 60)
        
        process = Process(
            pid=self.generate_pid(),
            size=size,
            arrival_time=time.time(),
            duration=duration,
            priority=random.randint(1, 5)
        )
        
        self.generated_history.append(process)
        return process
    
    def generate_single_process(self, size: int, duration: float = 30.0, 
                                priority: int = 1) -> Process:
        """Generate a process with specific parameters"""
        process = Process(
            pid=self.generate_pid(),
            size=size,
            arrival_time=time.time(),
            duration=duration,
            priority=priority
        )
        
        self.generated_history.append(process)
        return process
    
    def generate_batch(self, count: int = 5) -> List[Process]:
        """Generate a batch of random processes"""
        return [self.generate_random_process() for _ in range(count)]