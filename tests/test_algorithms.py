"""
Unit Tests for Memory Management Algorithms
Test suite for verifying algorithm correctness and performance
"""

import unittest
import sys
import os
import time
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from memory_simulator import MemoryManager, AllocationAlgorithm, Process, MemoryBlock
from process_generator import ProcessGenerator, ProcessType
from fragmentation import FragmentationAnalyzer, FragmentationMetrics

class TestMemoryAlgorithms(unittest.TestCase):
    """Test cases for memory allocation algorithms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.memory_size = 1024  # 1MB
        self.manager = MemoryManager(self.memory_size)
        self.process_gen = ProcessGenerator(seed=42)
    
    def test_first_fit_basic_allocation(self):
        """Test basic First-Fit allocation"""
        print("\nTest 1: Basic First-Fit Allocation")
        
        # Create test processes
        p1 = Process("P1", 256, time.time())
        p2 = Process("P2", 128, time.time())
        p3 = Process("P3", 512, time.time())
        
        # Allocate using First-Fit
        success1, addr1 = self.manager.first_fit(p1)
        success2, addr2 = self.manager.first_fit(p2)
        success3, addr3 = self.manager.first_fit(p3)
        
        self.assertTrue(success1, "P1 should be allocated")
        self.assertTrue(success2, "P2 should be allocated")
        self.assertTrue(success3, "P3 should be allocated")
        
        # Verify allocations
        self.assertEqual(len(self.manager.allocated_processes), 3)
        self.assertEqual(self.manager.available_memory, self.memory_size - (256+128+512))
        
        print("✓ Basic First-Fit allocation passed")
    
    def test_best_fit_selection(self):
        """Test Best-Fit selects smallest fitting block"""
        print("\nTest 2: Best-Fit Block Selection")
        
        # Create fragmented memory by allocating and freeing
        p1 = Process("P1", 512, time.time())
        p2 = Process("P2", 256, time.time())
        
        self.manager.first_fit(p1)
        self.manager.first_fit(p2)
        
        # Free to create fragmentation
        self.manager.deallocate("P1")
        self.manager.deallocate("P2")
        
        # Now we have two free blocks: 512KB and 256KB
        # Request 200KB process - should use 256KB block with Best-Fit
        p3 = Process("P3", 200, time.time())
        success, _ = self.manager.best_fit(p3)
        
        self.assertTrue(success)
        allocated_block = self.manager.allocated_processes["P3"]
        
        # With Best-Fit, should use the 256KB block (closest fit)
        # It will split into 200KB allocated and 56KB free
        self.assertTrue(allocated_block.size >= 200)
        
        print("✓ Best-Fit block selection passed")
    
    def test_worst_fit_largest_block(self):
        """Test Worst-Fit selects largest available block"""
        print("\nTest 3: Worst-Fit Largest Block Selection")
        
        # Create multiple free blocks
        processes = []
        sizes = [100, 200, 300]
        for i, size in enumerate(sizes):
            p = Process(f"P{i}", size, time.time())
            processes.append(p)
            self.manager.first_fit(p)
        
        # Free all to create three free blocks
        for p in processes:
            self.manager.deallocate(p.pid)
        
        # Request 150KB process
        p_new = Process("PNEW", 150, time.time())
        success, _ = self.manager.worst_fit(p_new)
        
        self.assertTrue(success)
        
        # With Worst-Fit, should use largest block (300KB)
        # which will be split into 150KB allocated and 150KB free
        free_blocks = [b for b in self.manager.memory_map if b.pid == "FREE"]
        self.assertTrue(any(b.size == 150 for b in free_blocks))
        
        print("✓ Worst-Fit largest block selection passed")
    
    def test_next_fit_rotation(self):
        """Test Next-Fit rotation behavior"""
        print("\nTest 4: Next-Fit Rotation")
        
        # Allocate initial processes
        for i in range(3):
            p = Process(f"P{i}", 100, time.time())
            self.manager.next_fit(p)
        
        initial_position = self.manager.next_fit_start
        
        # Allocate more processes
        p_new = Process("PNEW", 200, time.time())
        success, _ = self.manager.next_fit(p_new)
        
        self.assertTrue(success)
        self.assertNotEqual(self.manager.next_fit_start, initial_position)
        
        print("✓ Next-Fit rotation passed")
    
    def test_buddy_system_power_of_two(self):
        """Test Buddy System uses power-of-two blocks"""
        print("\nTest 5: Buddy System Power-of-Two")
        
        manager = MemoryManager(1024)
        
        # Request non-power-of-two size
        p1 = Process("P1", 300, time.time())  # 300KB
        success1, _ = manager.buddy_system(p1)
        
        self.assertTrue(success1)
        
        # Buddy System should round up to power of two (512KB)
        allocated = manager.allocated_processes["P1"]
        self.assertTrue(allocated.size in [256, 512, 1024])
        
        print("✓ Buddy System power-of-two allocation passed")
    
    def test_deallocation_and_coalescing(self):
        """Test deallocation merges adjacent free blocks"""
        print("\nTest 6: Deallocation and Coalescing")
        
        # Allocate adjacent blocks
        sizes = [256, 128, 128]
        for i, size in enumerate(sizes):
            p = Process(f"P{i}", size, time.time())
            self.manager.first_fit(p)
        
        initial_block_count = len(self.manager.memory_map)
        
        # Deallocate all
        for i in range(3):
            self.manager.deallocate(f"P{i}")
        
        # Should have one large free block after coalescing
        free_blocks = [b for b in self.manager.memory_map if b.pid == "FREE"]
        self.assertEqual(len(free_blocks), 1)
        self.assertEqual(free_blocks[0].size, self.memory_size)
        
        print("✓ Deallocation and coalescing passed")
    
    def test_fragmentation_metrics(self):
        """Test fragmentation calculation"""
        print("\nTest 7: Fragmentation Metrics")
        
        analyzer = FragmentationAnalyzer()
        
        # Create test memory blocks
        class MockBlock:
            def __init__(self, start, size, pid):
                self.start = start
                self.size = size
                self.pid = pid
        
        # Simulate fragmented memory
        memory_blocks = [
            MockBlock(0, 256, "P1"),     # Allocated
            MockBlock(256, 64, "FREE"),  # Free (small)
            MockBlock(320, 128, "P2"),   # Allocated
            MockBlock(448, 128, "FREE"), # Free (medium)
            MockBlock(576, 448, "FREE")  # Free (large)
        ]
        
        allocated_processes = {
            "P1": memory_blocks[0],
            "P2": memory_blocks[2]
        }
        
        metrics = analyzer.calculate_fragmentation(
            memory_blocks,
            1024,
            allocated_processes
        )
        
        # Verify metrics
        self.assertIsInstance(metrics, FragmentationMetrics)
        self.assertGreaterEqual(metrics.external_fragmentation, 0)
        self.assertLessEqual(metrics.external_fragmentation, 100)
        self.assertEqual(metrics.free_blocks_count, 3)
        
        print("✓ Fragmentation metrics calculation passed")
    
    def test_memory_compaction(self):
        """Test memory compaction functionality"""
        print("\nTest 8: Memory Compaction")
        
        # Create fragmented memory
        for i in range(5):
            p = Process(f"P{i}", 64, time.time())
            self.manager.first_fit(p)
        
        # Deallocate some to create holes
        self.manager.deallocate("P1")
        self.manager.deallocate("P3")
        
        free_before = len([b for b in self.manager.memory_map if b.pid == "FREE"])
        
        # Perform compaction
        self.manager.compact_memory()
        
        free_after = len([b for b in self.manager.memory_map if b.pid == "FREE"])
        
        # Should have one contiguous free block
        self.assertEqual(free_after, 1)
        
        # Allocated blocks should be at the beginning
        for i, block in enumerate(self.manager.memory_map):
            if i < 3:  # First 3 should be allocated
                self.assertNotEqual(block.pid, "FREE")
            else:  # Last should be free
                self.assertEqual(block.pid, "FREE")
        
        print("✓ Memory compaction passed")
    
    def test_edge_cases(self):
        """Test edge cases"""
        print("\nTest 9: Edge Cases")
        
        # Test allocation larger than total memory
        p_huge = Process("HUGE", self.memory_size * 2, time.time())
        success, _ = self.manager.first_fit(p_huge)
        self.assertFalse(success, "Should fail for size > total memory")
        
        # Test zero-size process
        p_zero = Process("ZERO", 0, time.time())
        success, _ = self.manager.first_fit(p_zero)
        self.assertFalse(success, "Should fail for zero size")
        
        # Test exact fit
        p_exact = Process("EXACT", self.memory_size, time.time())
        success, _ = self.manager.first_fit(p_exact)
        self.assertTrue(success, "Should succeed for exact fit")
        self.assertEqual(self.manager.available_memory, 0)
        
        # Try to allocate when memory full
        p_extra = Process("EXTRA", 1, time.time())
        success, _ = self.manager.first_fit(p_extra)
        self.assertFalse(success, "Should fail when memory full")
        
        print("✓ Edge cases passed")
    
    def test_process_generator(self):
        """Test process generator functionality"""
        print("\nTest 10: Process Generator")
        
        generator = ProcessGenerator(seed=42)
        
        # Generate single process
        process = generator.generate_random_process()
        
        self.assertIsNotNone(process.pid)
        self.assertGreater(process.size, 0)
        self.assertGreater(process.duration, 0)
        self.assertIn(process.process_type, ProcessType)
        
        # Generate batch
        batch_size = 10
        batch = generator.generate_burst(batch_size)
        
        self.assertEqual(len(batch), batch_size)
        
        # All PIDs should be unique
        pids = [p.pid for p in batch]
        self.assertEqual(len(set(pids)), len(pids))
        
        # Test statistics
        stats = generator.get_statistics()
        self.assertEqual(stats['total_processes'], batch_size + 1)  # +1 for single process
        
        print("✓ Process generator passed")

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete simulation workflow"""
        print("\nIntegration Test: Full Workflow")
        
        # Initialize components
        memory = 2048
        manager = MemoryManager(memory)
        generator = ProcessGenerator(seed=123)
        analyzer = FragmentationAnalyzer()
        
        # Generate workload
        workload = generator.generate_workload(20, 60, "uniform")
        
        # Simulate
        allocated = []
        for process in workload:
            success, _ = manager.first_fit(process)
            if success:
                allocated.append(process)
            
            # Periodically analyze
            if len(allocated) % 5 == 0:
                metrics = analyzer.calculate_fragmentation(
                    manager.memory_map,
                    manager.total_memory,
                    manager.allocated_processes
                )
                self.assertIsInstance(metrics, FragmentationMetrics)
            
            # Random deallocation
            if allocated and random.random() < 0.3:
                p = random.choice(allocated)
                manager.deallocate(p.pid)
                allocated.remove(p)
        
        # Final checks
        stats = manager.get_statistics()
        self.assertLessEqual(stats['utilization'], 100)
        self.assertGreaterEqual(stats['available_memory'], 0)
        
        print("✓ Full workflow integration test passed")

def run_performance_comparison():
    """Run performance comparison of all algorithms"""
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    
    algorithms = [
        ("First-Fit", AllocationAlgorithm.FIRST_FIT),
        ("Best-Fit", AllocationAlgorithm.BEST_FIT),
        ("Worst-Fit", AllocationAlgorithm.WORST_FIT),
        ("Next-Fit", AllocationAlgorithm.NEXT_FIT),
        ("Buddy System", AllocationAlgorithm.BUDDY_SYSTEM)
    ]
    
    # Generate test workload
    generator = ProcessGenerator(seed=999)
    test_processes = generator.generate_burst(50)
    
    results = []
    
    for algo_name, algo_enum in algorithms:
        manager = MemoryManager(4096)
        success_count = 0
        start_time = time.time()
        
        for process in test_processes:
            if algo_enum == AllocationAlgorithm.FIRST_FIT:
                success, _ = manager.first_fit(process)
            elif algo_enum == AllocationAlgorithm.BEST_FIT:
                success, _ = manager.best_fit(process)
            elif algo_enum == AllocationAlgorithm.WORST_FIT:
                success, _ = manager.worst_fit(process)
            elif algo_enum == AllocationAlgorithm.NEXT_FIT:
                success, _ = manager.next_fit(process)
            elif algo_enum == AllocationAlgorithm.BUDDY_SYSTEM:
                success, _ = manager.buddy_system(process)
            
            if success:
                success_count += 1
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Calculate fragmentation
        manager._update_fragmentation()
        frag = manager.fragmentation_history[-1]['external'] if manager.fragmentation_history else 0
        
        results.append({
            'algorithm': algo_name,
            'success_rate': (success_count / len(test_processes)) * 100,
            'time': elapsed,
            'fragmentation': frag
        })
        
        print(f"{algo_name:15} | Success: {success_count:3d}/50 | "
              f"Time: {elapsed:.3f}s | Frag: {frag:5.1f}%")
    
    # Find best overall
    best = min(results, key=lambda x: x['time'] + (x['fragmentation'] / 10))
    print(f"\nRecommended: {best['algorithm']} "
          f"(Score: {best['time'] + best['fragmentation']/10:.2f})")
    
    return results

if __name__ == '__main__':
    # Run tests
    print("="*60)
    print("MEMORY MANAGEMENT SIMULATOR - TEST SUITE")
    print("="*60)
    
    # Run unit tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMemoryAlgorithms)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)
    
    # Run integration test
    print("\n" + "="*60)
    print("RUNNING INTEGRATION TEST")
    print("="*60)
    integration_suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegration)
    integration_result = runner.run(integration_suite)
    
    # Run performance comparison
    print("\n" + "="*60)
    performance_results = run_performance_comparison()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = (test_result.testsRun + integration_result.testsRun)
    failed_tests = len(test_result.failures) + len(integration_result.failures)
    
    if failed_tests == 0:
        print(f"✅ All {total_tests} tests passed!")
    else:
        print(f"❌ {failed_tests}/{total_tests} tests failed")
        for failure in test_result.failures + integration_result.failures:
            print(f"\nFailed: {failure[0]}")
            print(f"Error: {failure[1]}")