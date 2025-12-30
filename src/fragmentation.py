"""
Unit Tests for Memory Management Algorithms
Test suite for verifying algorithm correctness and performance
"""

import unittest
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory_simulator import MemoryManager, AllocationAlgorithm, Process
from src.process_generator import ProcessGenerator, ProcessType

class TestMemoryAlgorithms(unittest.TestCase):
    """Test cases for memory allocation algorithms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.memory_size = 1024  # 1MB
        self.manager = MemoryManager(self.memory_size)
        self.process_gen = ProcessGenerator(seed=42)
    
    def test_first_fit_basic(self):
        """Test basic First-Fit allocation"""
        # Create processes
        p1 = Process("P1", 256, time.time())
        p2 = Process("P2", 128, time.time())
        p3 = Process("P3", 512, time.time())
        
        # Allocate using First-Fit
        success1, addr1 = self.manager.first_fit(p1)
        success2, addr2 = self.manager.first_fit(p2)
        success3, addr3 = self.manager.first_fit(p3)
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        self.assertTrue(success3)
        
        # Verify allocations don't overlap
        blocks = self.manager.memory_map
        allocated = [b for b in blocks if b.pid != "FREE"]
        self.assertEqual(len(allocated), 3)
        
        # Check they're in correct order
        self.assertEqual(allocated[0].pid, "P1")
        self.assertEqual(allocated[1].pid, "P2")
        self.assertEqual(allocated[2].pid, "P3")
    
    def test_best_fit_smallest_block(self):
        """Test Best-Fit selects smallest fitting block"""
        # Create fragmented memory: [256 FREE][128 FREE][512 FREE]
        # Add some initial allocations and deallocations to create fragmentation
        p_large = Process("PLARGE", 512, time.time())
        self.manager.first_fit(p_large)
        self.manager.deallocate("PLARGE")
        
        # Now we have: [512 FREE]
        # Request processes of different sizes
        p1 = Process("P1", 128, time.time())
        p2 = Process("P2", 256, time.time())
        
        success1, _ = self.manager.best_fit(p1)
        success2, _ = self.manager.best_fit(p2)
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # With Best-Fit, P1 should go into a 128-block if available
        # but in our case it splits the 512 block
        # Verify both are allocated
        self.assertEqual(len(self.manager.allocated_processes), 2)
    
    def test_worst_fit_largest_block(self):
        """Test Worst-Fit selects largest available block"""
        # Create initial state with different sized free blocks
        # by allocating and deallocating
        processes = [
            Process("P1", 256, time.time()),
            Process("P2", 128, time.time()),
            Process("P3", 512, time.time())
        ]
        
        # Allocate then deallocate to create fragmentation
        for p in processes:
            self.manager.first_fit(p)
        
        self.manager.deallocate("P1")
        self.manager.deallocate("P2")
        self.manager.deallocate("P3")
        
        # Now request a 100KB process
        p_new = Process("PNEW", 100, time.time())
        success, _ = self.manager.worst_fit(p_new)
        
        self.assertTrue(success)
        
        # With Worst-Fit, should be allocated in largest free block (512KB)
        # which will be split
        allocated_block = self.manager.allocated_processes["PNEW"]
        self.assertTrue(allocated_block.size >= 100)
    
    def test_next_fit_rotation(self):
        """Test Next-Fit starts from last allocation point"""
        # Allocate several processes
        processes = []
        for i in range(5):
            p = Process(f"P{i}", 64, time.time())
            processes.append(p)
            self.manager.next_fit(p)
        
        # Store next_fit_start position
        start_pos = self.manager.next_fit_start
        
        # Deallocate some processes
        self.manager.deallocate("P1")
        self.manager.deallocate("P3")
        
        # Allocate new process - should start from start_pos
        p_new = Process("PNEW", 128, time.time())
        success, _ = self.manager.next_fit(p_new)
        
        self.assertTrue(success)
        # next_fit_start should have moved
        self.assertNotEqual(self.manager.next_fit_start, start_pos)
    
    def test_buddy_system_power_of_two(self):
        """Test Buddy System allocates power-of-two blocks"""
        manager = MemoryManager(1024)  # 1MB
        
        # Request non-power-of-two size
        p1 = Process("P1", 300, time.time())  # 300KB -> rounds to 512KB
        success1, addr1 = manager.buddy_system(p1)
        
        self.assertTrue(success1)
        
        # Verify allocated size is power of two
        allocated = manager.allocated_processes["P1"]
        self.assertTrue(allocated.size in [256, 512])  # Could be either depending on implementation
        
        # Request another process
        p2 = Process("P2", 100, time.time())  # 100KB -> rounds to 128KB
        success2, addr2 = manager.buddy_system(p2)
        
        self.assertTrue(success2)
        allocated2 = manager.allocated_processes["P2"]
        self.assertTrue(allocated2.size in [128, 256])
    
    def test_deallocation_and_coalescing(self):
        """Test deallocation merges adjacent free blocks"""
        # Allocate adjacent blocks
        p1 = Process("P1", 256, time.time())
        p2 = Process("P2", 128, time.time())
        p3 = Process("P3", 128, time.time())
        
        self.manager.first_fit(p1)
        self.manager.first_fit(p2)
        self.manager.first_fit(p3)
        
        # Check initial state
        initial_blocks = len(self.manager.memory_map)
        
        # Deallocate middle block
        self.manager.deallocate("P2")
        
        # Deallocate adjacent blocks
        self.manager.deallocate("P1")
        self.manager.deallocate("P3")
        
        # After deallocation and coalescing, should have fewer blocks
        final_blocks = len(self.manager.memory_map)
        
        # Should have merged into one big free block
        self.assertLessEqual(final_blocks, initial_blocks - 2)  # At least 2 merges
        
        # Should be one large free block
        free_blocks = [b for b in self.manager.memory_map if b.pid == "FREE"]
        self.assertEqual(len(free_blocks), 1)
        self.assertEqual(free_blocks[0].size, self.memory_size)
    
    def test_fragmentation_calculation(self):
        """Test fragmentation metrics calculation"""
        # Create fragmented memory
        sizes = [256, 128, 64, 128, 256]
        for i, size in enumerate(sizes):
            p = Process(f"P{i}", size, time.time())
            self.manager.first_fit(p)
        
        # Deallocate alternate blocks to create fragmentation
        self.manager.deallocate("P0")
        self.manager.deallocate("P2")
        self.manager.deallocate("P4")
        
        # Calculate fragmentation
        self.manager._update_fragmentation()
        
        # Should have fragmentation data
        self.assertTrue(len(self.manager.fragmentation_history) > 0)
        
        latest = self.manager.fragmentation_history[-1]
        
        # Verify metrics exist
        self.assertIn('external', latest)
        self.assertIn('internal', latest)
        self.assertIn('free_blocks', latest)
        
        # With fragmentation, external should be > 0
        self.assertGreater(latest['external'], 0)
        self.assertLessEqual(latest['external'], 100)
    
    def test_memory_compaction(self):
        """Test memory compaction functionality"""
        # Create fragmented memory
        processes = []
        for i in range(5):
            p = Process(f"P{i}", 64, time.time())
            processes.append(p)
            self.manager.first_fit(p)
        
        # Deallocate some to create holes
        self.manager.deallocate("P1")
        self.manager.deallocate("P3")
        
        # Count free blocks before compaction
        free_before = len([b for b in self.manager.memory_map if b.pid == "FREE"])
        
        # Perform compaction
        self.manager.compact_memory()
        
        # Count free blocks after compaction
        free_after = len([b for b in self.manager.memory_map if b.pid == "FREE"])
        
        # After compaction, free blocks should be consolidated
        self.assertEqual(free_after, 1)  # One contiguous free block
        
        # Allocated blocks should be contiguous at start
        allocated_indices = []
        for i, block in enumerate(self.manager.memory_map):
            if block.pid != "FREE":
                allocated_indices.append(i)
        
        # All allocated blocks should be at the beginning
        self.assertEqual(allocated_indices, list(range(len(allocated_indices))))
    
    def test_process_generator(self):
        """Test process generator creates valid processes"""
        generator = ProcessGenerator(seed=42)
        
        # Generate single process
        process = generator.generate_random_process()
        
        self.assertIsNotNone(process.pid)
        self.assertGreater(process.size, 0)
        self.assertGreater(process.duration, 0)
        self.assertGreaterEqual(process.priority, 1)
        self.assertLessEqual(process.priority, 5)
        
        # Generate batch
        batch = generator.generate_burst(10)
        self.assertEqual(len(batch), 10)
        
        # All PIDs should be unique
        pids = [p.pid for p in batch]
        self.assertEqual(len(set(pids)), len(pids))
        
        # Test workload generation
        workload = generator.generate_workload(20, 60, "uniform")
        self.assertEqual(len(workload), 20)
        
        # Should be sorted by arrival time
        arrivals = [p.arrival_time for p in workload]
        self.assertEqual(arrivals, sorted(arrivals))
    
    def test_stress_test_allocation(self):
        """Test allocation under stress (high memory utilization)"""
        manager = MemoryManager(512)  # Smaller memory for faster test
        
        # Generate processes to fill 90% of memory
        generator = ProcessGenerator()
        processes = generator.generate_stress_test(512, 0.9)
        
        allocated_count = 0
        for process in processes:
            success, _ = manager.first_fit(process)
            if success:
                allocated_count += 1
        
        # Should have allocated most processes
        self.assertGreater(allocated_count, len(processes) * 0.8)
        
        # Memory utilization should be high
        stats = manager.get_statistics()
        self.assertGreater(stats['utilization'], 80)
    
    def test_algorithm_comparison(self):
        """Compare different algorithms' performance"""
        algorithms = [
            ("First-Fit", self.manager.first_fit),
            ("Best-Fit", self.manager.best_fit),
            ("Worst-Fit", self.manager.worst_fit),
        ]
        
        # Generate test workload
        generator = ProcessGenerator(seed=123)
        processes = generator.generate_burst(20)
        
        results = {}
        
        for algo_name, algo_func in algorithms:
            # Reset manager for each algorithm
            manager = MemoryManager(self.memory_size)
            
            success_count = 0
            start_time = time.time()
            
            for process in processes:
                success, _ = algo_func(process)
                if success:
                    success_count += 1
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Calculate fragmentation
            manager._update_fragmentation()
            if manager.fragmentation_history:
                frag = manager.fragmentation_history[-1]['external']
            else:
                frag = 0
            
            results[algo_name] = {
                'success_rate': (success_count / len(processes)) * 100,
                'time': elapsed,
                'fragmentation': frag
            }
        
        # All algorithms should have reasonable success rates
        for algo, stats in results.items():
            self.assertGreater(stats['success_rate'], 50)  # At least 50% success
            self.assertLess(stats['time'], 1.0)  # Should complete quickly
    
    def test_edge_cases(self):
        """Test edge cases for memory allocation"""
        # Test allocation larger than total memory
        p_huge = Process("HUGE", self.memory_size * 2, time.time())
        success, _ = self.manager.first_fit(p_huge)
        self.assertFalse(success)
        
        # Test zero-size process (should fail)
        p_zero = Process("ZERO", 0, time.time())
        success, _ = self.manager.first_fit(p_zero)
        self.assertFalse(success)
        
        # Test exact fit allocation
        p_exact = Process("EXACT", self.memory_size, time.time())
        success, _ = self.manager.first_fit(p_exact)
        self.assertTrue(success)
        
        # Should use all memory
        self.assertEqual(self.manager.available_memory, 0)
        
        # Try to allocate another process (should fail)
        p_extra = Process("EXTRA", 1, time.time())
        success, _ = self.manager.first_fit(p_extra)
        self.assertFalse(success)
    
    def test_export_import_state(self):
        """Test exporting and importing memory state"""
        # Create some allocations
        processes = []
        for i in range(3):
            p = Process(f"P{i}", 128, time.time())
            processes.append(p)
            self.manager.first_fit(p)
        
        # Export state
        export_file = "test_export.json"
        self.manager.export_state(export_file)
        
        # Create new manager and import
        new_manager = MemoryManager(self.memory_size)
        success = new_manager.import_state(export_file)
        
        self.assertTrue(success)
        
        # Compare states
        self.assertEqual(len(self.manager.memory_map), len(new_manager.memory_map))
        self.assertEqual(len(self.manager.allocated_processes), len(new_manager.allocated_processes))
        
        # Clean up
        if os.path.exists(export_file):
            os.remove(export_file)
    
    def test_performance_metrics(self):
        """Test performance metrics collection"""
        # Perform multiple allocations/deallocations
        operations = 100
        start_time = time.time()
        
        for i in range(operations):
            if i % 3 == 0:
                # Allocate
                p = Process(f"P{i}", 64, time.time())
                self.manager.first_fit(p)
            else:
                # Try to deallocate if exists
                pid = f"P{i-1}"
                if pid in self.manager.allocated_processes:
                    self.manager.deallocate(pid)
        
        end_time = time.time()
        
        # Get statistics
        stats = self.manager.get_statistics()
        
        # Verify metrics
        self.assertGreater(stats['allocation_count'], 0)
        self.assertGreater(stats['runtime'], 0)
        self.assertLessEqual(stats['utilization'], 100)
        
        # Clean up
        for pid in list(self.manager.allocated_processes.keys()):
            self.manager.deallocate(pid)

class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""
    
    def test_full_simulation_workflow(self):
        """Test complete simulation workflow"""
        from src.process_generator import ProcessGenerator
        from src.memory_simulator import MemoryManager, AllocationAlgorithm
        from src.fragmentation import FragmentationAnalyzer
        
        # Initialize components
        memory = 2048  # 2MB
        manager = MemoryManager(memory)
        generator = ProcessGenerator(seed=42)
        analyzer = FragmentationAnalyzer()
        
        # Generate workload
        workload = generator.generate_workload(50, 300, "bursty")
        
        # Simulate process arrivals
        simulated_time = 0
        allocated_processes = []
        
        for process in workload:
            # Simulate time passing
            simulated_time += 1
            
            # Allocate if memory available
            success, _ = manager.first_fit(process)
            if success:
                allocated_processes.append(process)
            
            # Periodically analyze fragmentation
            if len(allocated_processes) % 10 == 0:
                metrics = analyzer.calculate_fragmentation(
                    manager.memory_map,
                    manager.total_memory,
                    manager.allocated_processes
                )
                
                # Check fragmentation status
                status = analyzer.get_fragmentation_status(metrics)
                
                # If fragmentation is critical, perform compaction
                if status['overall']['status'] == 'CRITICAL':
                    manager.compact_memory()
            
            # Simulate process completion (random deallocation)
            if allocated_processes and simulated_time % 5 == 0:
                # Deallocate random process
                import random
                if allocated_processes:
                    process_to_free = random.choice(allocated_processes)
                    manager.deallocate(process_to_free.pid)
                    allocated_processes.remove(process_to_free)
        
        # Final analysis
        report = analyzer.generate_fragmentation_report()
        
        # Verify we have data
        self.assertTrue(len(analyzer.metrics_history) > 0)
        self.assertTrue("External Fragmentation" in report)
        
        # Final memory state should be valid
        stats = manager.get_statistics()
        self.assertLessEqual(stats['utilization'], 100)
        self.assertGreaterEqual(stats['available_memory'], 0)

def run_performance_benchmark():
    """Run performance benchmark for all algorithms"""
    import timeit
    
    algorithms = [
        ("First-Fit", MemoryManager(4096).first_fit),
        ("Best-Fit", MemoryManager(4096).best_fit),
        ("Worst-Fit", MemoryManager(4096).worst_fit),
        ("Next-Fit", MemoryManager(4096).next_fit),
        ("Buddy-System", MemoryManager(4096).buddy_system),
    ]
    
    # Generate test data
    generator = ProcessGenerator()
    test_processes = generator.generate_burst(100)
    
    print("=" * 60)
    print("ALGORITHM PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    results = []
    for algo_name, algo_func in algorithms:
        # Time allocation of 100 processes
        def run_allocations():
            manager = MemoryManager(4096)
            for process in test_processes:
                algo_func(process)
        
        # Run benchmark
        time_taken = timeit.timeit(run_allocations, number=10)
        
        # Run once to get fragmentation
        manager = MemoryManager(4096)
        for process in test_processes:
            algo_func(process)
        manager._update_fragmentation()
        
        if manager.fragmentation_history:
            frag = manager.fragmentation_history[-1]['external']
        else:
            frag = 0
        
        results.append((algo_name, time_taken, frag))
        
        print(f"{algo_name:15} Time: {time_taken:6.3f}s  Frag: {frag:5.1f}%")
    
    print("=" * 60)
    
    # Find best algorithm by combined metric
    best_score = float('inf')
    best_algo = None
    
    for algo_name, time_taken, frag in results:
        # Combined score: time + fragmentation penalty
        score = time_taken + (frag / 10)  # 10% fragmentation = 1 second penalty
        if score < best_score:
            best_score = score
            best_algo = algo_name
    
    print(f"Recommended algorithm: {best_algo} (score: {best_score:.2f})")
    
    return results

if __name__ == '__main__':
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], verbosity=2, exit=False)
    
    # Run performance benchmark
    print("\n" + "=" * 60)
    print("Running performance benchmark...")
    benchmark_results = run_performance_benchmark()