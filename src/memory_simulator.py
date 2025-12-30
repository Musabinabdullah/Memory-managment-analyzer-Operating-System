"""
Memory Management Simulator - Core Algorithms
OS Memory Management Algorithms Implementation
"""
import time
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

class AllocationAlgorithm(Enum):
    FIRST_FIT = "First Fit"
    BEST_FIT = "Best Fit"
    WORST_FIT = "Worst Fit"
    NEXT_FIT = "Next Fit"
    BUDDY_SYSTEM = "Buddy System"

class MemoryBlock:
    def __init__(self, start: int, size: int, pid: str = "FREE"):
        self.start = start
        self.size = size
        self.end = start + size - 1
        self.pid = pid  # Process ID or "FREE"
        self.next = None
        self.prev = None
        
    def __repr__(self):
        return f"[{self.start}-{self.end}] {self.pid} ({self.size}KB)"

@dataclass
class Process:
    pid: str
    size: int
    arrival_time: float
    duration: float = 10.0  # How long process runs

class MemoryManager:
    def __init__(self, total_memory: int = 1024):
        self.total_memory = total_memory
        self.available_memory = total_memory
        self.memory_map = [MemoryBlock(0, total_memory, "FREE")]
        self.allocated_processes = {}
        self.free_list = self.memory_map[:]
        self.fragmentation_history = []
        self.allocation_count = 0
        self.next_fit_start = 0
        # Initialize fragmentation tracking
        self._update_fragmentation()
        
    def first_fit(self, process: Process) -> Tuple[bool, int]:
        """First Fit Allocation Algorithm"""
        for i, block in enumerate(self.memory_map):
            if block.pid == "FREE" and block.size >= process.size:
                return self._allocate_block(i, block, process)
        return False, -1
    
    def best_fit(self, process: Process) -> Tuple[bool, int]:
        """Best Fit Allocation Algorithm"""
        best_block = None
        best_index = -1
        min_waste = float('inf')
        
        for i, block in enumerate(self.memory_map):
            if block.pid == "FREE" and block.size >= process.size:
                waste = block.size - process.size
                if waste < min_waste:
                    min_waste = waste
                    best_block = block
                    best_index = i
        
        if best_block:
            return self._allocate_block(best_index, best_block, process)
        return False, -1
    
    def worst_fit(self, process: Process) -> Tuple[bool, int]:
        """Worst Fit Allocation Algorithm"""
        worst_block = None
        worst_index = -1
        max_size = -1
        
        for i, block in enumerate(self.memory_map):
            if block.pid == "FREE" and block.size >= process.size:
                if block.size > max_size:
                    max_size = block.size
                    worst_block = block
                    worst_index = i
        
        if worst_block:
            return self._allocate_block(worst_index, worst_block, process)
        return False, -1
    
    def next_fit(self, process: Process) -> Tuple[bool, int]:
        """Next Fit Allocation Algorithm"""
        n = len(self.memory_map)
        for i in range(n):
            idx = (self.next_fit_start + i) % n
            block = self.memory_map[idx]
            if block.pid == "FREE" and block.size >= process.size:
                self.next_fit_start = (idx + 1) % n
                return self._allocate_block(idx, block, process)
        return False, -1
    
    def buddy_system(self, process: Process) -> Tuple[bool, int]:
        """Buddy System Allocation"""
        # Find smallest power of 2 >= process size
        size_needed = self._next_power_of_two(process.size)
        
        # Check free blocks of appropriate size
        for i, block in enumerate(self.memory_map):
            if block.pid == "FREE" and block.size == size_needed:
                return self._allocate_block(i, block, process)
            elif block.pid == "FREE" and block.size > size_needed:
                # Split block recursively
                self._split_buddy_block(i, block, size_needed)
                return self._allocate_block(i, self.memory_map[i], process)
        
        return False, -1
    
    def _next_power_of_two(self, n: int) -> int:
        """Find next power of two >= n"""
        return 1 << (n - 1).bit_length()
    
    def _split_buddy_block(self, index: int, block: MemoryBlock, target_size: int):
        """Recursively split block in buddy system"""
        while block.size > target_size:
            new_size = block.size // 2
            new_block = MemoryBlock(block.start + new_size, new_size, "FREE")
            block.size = new_size
            block.end = block.start + new_size - 1
            self.memory_map.insert(index + 1, new_block)
    
    def _allocate_block(self, index: int, block: MemoryBlock, process: Process) -> Tuple[bool, int]:
        """Allocate memory block to process"""
        if block.size == process.size:
            # Exact fit
            block.pid = process.pid
            self.allocated_processes[process.pid] = block
            self.available_memory -= process.size
        else:
            # Split block
            remaining = block.size - process.size
            block.size = process.size
            block.end = block.start + process.size - 1
            block.pid = process.pid
            
            # Add remaining free block
            free_block = MemoryBlock(block.end + 1, remaining, "FREE")
            self.memory_map.insert(index + 1, free_block)
            
            self.allocated_processes[process.pid] = block
            self.available_memory -= process.size
        
        self.allocation_count += 1
        self._update_fragmentation()
        return True, block.start
    
    def deallocate(self, pid: str) -> bool:
        """Deallocate memory for a process"""
        if pid not in self.allocated_processes:
            return False
        
        block = self.allocated_processes[pid]
        block.pid = "FREE"
        self.available_memory += block.size
        del self.allocated_processes[pid]
        
        # Merge adjacent free blocks (coalescing)
        self._merge_free_blocks()
        self._update_fragmentation()
        
        return True
    
    def _merge_free_blocks(self):
        """Merge adjacent free blocks"""
        i = 0
        while i < len(self.memory_map) - 1:
            curr = self.memory_map[i]
            next_block = self.memory_map[i + 1]
            
            if curr.pid == "FREE" and next_block.pid == "FREE":
                # Merge blocks
                curr.size += next_block.size
                curr.end = curr.start + curr.size - 1
                self.memory_map.pop(i + 1)
            else:
                i += 1
    
    def _update_fragmentation(self):
        """Calculate and store fragmentation metrics"""
        total_free = sum(block.size for block in self.memory_map if block.pid == "FREE")
        free_blocks = [block for block in self.memory_map if block.pid == "FREE"]
        
        if total_free == 0:
            external_frag = 0
        else:
            max_free_block = max((block.size for block in free_blocks), default=0)
            external_frag = 1 - (max_free_block / total_free) if total_free > 0 else 0
        
        internal_frag = sum(
            block.size - process.size 
            for pid, block in self.allocated_processes.items() 
            if (process := self._get_process_by_pid(pid)) and block.size > process.size
        )
        
        self.fragmentation_history.append({
            'time': time.time(),
            'external': external_frag * 100,  # Percentage
            'internal': internal_frag,
            'total_free': total_free,
            'free_blocks': len(free_blocks)
        })
    
    def _get_process_by_pid(self, pid: str) -> Optional[Process]:
        """Helper to get process by PID (would come from process generator)"""
        # In real implementation, would look up from process list
        return Process(pid=pid, size=self.allocated_processes[pid].size, arrival_time=time.time())
    
    def get_memory_map_display(self) -> str:
        """Generate text representation of memory map"""
        display = "=" * 80 + "\n"
        display += "MEMORY MAP\n"
        display += "=" * 80 + "\n"
        
        for block in self.memory_map:
            status = "FREE" if block.pid == "FREE" else f"PID:{block.pid}"
            display += f"[{block.start:5d}-{block.end:5d}] {status:15} {block.size:5d}KB\n"
        
        display += "=" * 80 + "\n"
        display += f"Total Memory: {self.total_memory}KB | Available: {self.available_memory}KB\n"
        display += f"Allocated Processes: {len(self.allocated_processes)}\n"
        return display
    
    def get_statistics(self) -> dict:
        """Get comprehensive statistics"""
        if self.fragmentation_history:
            current_frag = self.fragmentation_history[-1]
        else:
            current_frag = {'external': 0, 'internal': 0, 'total_free': self.total_memory}
        
        return {
            'total_memory': self.total_memory,
            'available_memory': self.available_memory,
            'utilization': ((self.total_memory - self.available_memory) / self.total_memory) * 100,
            'allocated_processes': len(self.allocated_processes),
            'free_blocks': len([b for b in self.memory_map if b.pid == "FREE"]),
            'external_fragmentation': current_frag['external'],
            'internal_fragmentation': current_frag['internal'],
            'allocation_count': self.allocation_count,
            'memory_blocks': len(self.memory_map)
        }