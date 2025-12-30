"""
Memory Management Simulator - Main Application
Controller for the memory management simulation system
"""

import streamlit as st
from memory_simulator import MemoryManager, AllocationAlgorithm
from memory_visualizer import MemoryVisualizer
from process_generator import ProcessGenerator
import threading
import time

class MemoryManagementApp:
    def __init__(self):
        """Initialize the main application"""
        self.memory_manager = None
        self.visualizer = None
        self.process_generator = None
        self.simulation_thread = None
        self.is_running = False
        
    def setup(self):
        """Setup the application configuration"""
        st.set_page_config(
            page_title="Memory Management Simulator",
            page_icon="💾",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize or retrieve from session state
        if 'app_state' not in st.session_state:
            self.memory_manager = MemoryManager(1024)
            self.process_generator = ProcessGenerator()
            st.session_state.app_state = {
                'memory_manager': self.memory_manager,
                'process_generator': self.process_generator,
                'simulation_active': False,
                'algorithm': AllocationAlgorithm.FIRST_FIT,
                'process_history': [],
                'auto_generation': False,
                'generation_interval': 5
            }
        else:
            # Retrieve from session state
            self.memory_manager = st.session_state.app_state['memory_manager']
            self.process_generator = st.session_state.app_state['process_generator']
        
        # Always create new visualizer with current memory_manager
        self.visualizer = MemoryVisualizer(self.memory_manager)
    
    def create_sidebar(self):
        """Create the sidebar controls"""
        with st.sidebar:
            st.title("🎮 Control Panel")
            
            # Memory Configuration
            st.subheader("📊 Memory Configuration")
            col1, col2 = st.columns(2)
            with col1:
                memory_size = st.number_input(
                    "Memory Size (KB):",
                    min_value=256,
                    max_value=8192,
                    value=1024,
                    step=256
                )
            with col2:
                block_size = st.number_input(
                    "Default Block (KB):",
                    min_value=16,
                    max_value=256,
                    value=64,
                    step=16
                )
            
            if st.button("🔄 Initialize Memory", type="primary", use_container_width=True):
                self.memory_manager = MemoryManager(memory_size)
                st.session_state.app_state['memory_manager'] = self.memory_manager
                st.success(f"Memory initialized: {memory_size}KB")
                st.rerun()
            
            # Algorithm Selection
            st.subheader("⚙️ Algorithm Settings")
            algorithm = st.selectbox(
                "Allocation Algorithm:",
                options=list(AllocationAlgorithm),
                format_func=lambda x: x.value,
                index=0
            )
            st.session_state.app_state['algorithm'] = algorithm
            
            # Process Generation Settings
            st.subheader("🎲 Process Generation")
            
            # Auto Generation Toggle
            if 'auto_running' not in st.session_state:
                st.session_state.auto_running = False
            if 'last_auto_gen' not in st.session_state:
                st.session_state.last_auto_gen = 0
            
            col1, col2 = st.columns(2)
            with col1:
                auto_min = st.number_input("Min Size (KB)", 16, 256, 32, key="auto_min")
            with col2:
                auto_max = st.number_input("Max Size (KB)", 64, 1024, 256, key="auto_max")
            
            auto_interval = st.slider("Interval (seconds)", 1, 10, 3, key="auto_interval")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start Auto-Gen", use_container_width=True, disabled=st.session_state.auto_running):
                    st.session_state.auto_running = True
                    st.session_state.last_auto_gen = time.time()
                    st.rerun()
            with col2:
                if st.button("⏸️ Stop Auto-Gen", use_container_width=True, disabled=not st.session_state.auto_running):
                    st.session_state.auto_running = False
                    st.rerun()
            
            if st.session_state.auto_running:
                current_time = time.time()
                if current_time - st.session_state.last_auto_gen >= auto_interval:
                    process = self.process_generator.generate_random_process(auto_min, auto_max)
                    if self.allocate_process(process):
                        st.session_state.app_state['process_history'].append(process)
                        st.success(f"✅ Auto-generated: {process.pid} ({process.size}KB)")
                    else:
                        st.warning(f"⚠️ Failed to allocate {process.pid} ({process.size}KB)")
                    st.session_state.last_auto_gen = current_time
                time.sleep(0.5)
                st.rerun()
            
            # Manual Process Control
            st.subheader("✋ Manual Control")
            col1, col2 = st.columns(2)
            with col1:
                manual_size = st.number_input("Process Size", 16, 512, 64)
            with col2:
                manual_duration = st.number_input("Duration", 1, 300, 30)
            
            if st.button("➕ Add Process", use_container_width=True):
                process = self.process_generator.generate_single_process(
                    size=manual_size,
                    duration=manual_duration
                )
                success = self.allocate_process(process)
                if success:
                    st.session_state.app_state['process_history'].append(process)
                    st.success(f"Process {process.pid} allocated!")
                else:
                    st.error(f"Failed to allocate process {process.pid}")
                st.rerun()
            
            # Batch Operations
            st.subheader("📦 Batch Operations")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Generate 5 Processes", use_container_width=True):
                    processes = self.process_generator.generate_batch(5)
                    allocated = 0
                    for process in processes:
                        if self.allocate_process(process):
                            st.session_state.app_state['process_history'].append(process)
                            allocated += 1
                    st.success(f"Allocated {allocated}/{len(processes)}")
                    st.rerun()
            
            with col2:
                if st.button("Generate 10 Processes", use_container_width=True):
                    processes = self.process_generator.generate_batch(10)
                    allocated = 0
                    for process in processes:
                        if self.allocate_process(process):
                            st.session_state.app_state['process_history'].append(process)
                            allocated += 1
                    st.success(f"Allocated {allocated}/{len(processes)}")
                    st.rerun()
            
            # Deallocate Section
            st.subheader("🗑️ Deallocate Processes")
            if self.memory_manager.allocated_processes:
                pid_to_free = st.selectbox(
                    "Select Process to Free:",
                    options=list(self.memory_manager.allocated_processes.keys())
                )
                if st.button("Free Selected Process", use_container_width=True):
                    if self.memory_manager.deallocate(pid_to_free):
                        st.success(f"Process {pid_to_free} deallocated!")
                        st.rerun()
                    else:
                        st.error("Deallocation failed!")
            
            # Clear All
            if st.button("🧹 Clear All Processes", type="secondary", use_container_width=True):
                self.clear_all_processes()
                st.success("All processes cleared!")
                st.rerun()
            
            # Export/Import
            st.subheader("💾 Data Management")
            if st.button("Export Memory State", use_container_width=True):
                self.export_memory_state()
            if st.button("Import Memory State", use_container_width=True):
                self.import_memory_state()
    
    def allocate_process(self, process):
        """Allocate a process using selected algorithm"""
        algorithm = st.session_state.app_state['algorithm']
        
        if algorithm == AllocationAlgorithm.FIRST_FIT:
            return self.memory_manager.first_fit(process)[0]
        elif algorithm == AllocationAlgorithm.BEST_FIT:
            return self.memory_manager.best_fit(process)[0]
        elif algorithm == AllocationAlgorithm.WORST_FIT:
            return self.memory_manager.worst_fit(process)[0]
        elif algorithm == AllocationAlgorithm.NEXT_FIT:
            return self.memory_manager.next_fit(process)[0]
        elif algorithm == AllocationAlgorithm.BUDDY_SYSTEM:
            return self.memory_manager.buddy_system(process)[0]
        return False
    
    def start_auto_generation(self, min_size, max_size, interval):
        """Start automatic process generation thread"""
        def auto_generate():
            while st.session_state.app_state['auto_generation']:
                process = self.process_generator.generate_random_process(min_size, max_size)
                if self.allocate_process(process):
                    st.session_state.app_state['process_history'].append(process)
                time.sleep(interval)
        
        if not self.is_running:
            self.is_running = True
            self.simulation_thread = threading.Thread(target=auto_generate)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
    
    def clear_all_processes(self):
        """Clear all allocated processes"""
        for pid in list(self.memory_manager.allocated_processes.keys()):
            self.memory_manager.deallocate(pid)
        st.session_state.app_state['process_history'] = []
    
    def export_memory_state(self):
        """Export current memory state to file"""
        import json
        state = {
            'memory_map': [
                {
                    'start': block.start,
                    'size': block.size,
                    'pid': block.pid
                }
                for block in self.memory_manager.memory_map
            ],
            'processes': [
                {
                    'pid': process.pid,
                    'size': process.size,
                    'arrival_time': process.arrival_time,
                    'duration': process.duration
                }
                for process in st.session_state.app_state['process_history']
            ]
        }
        
        with open('memory_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        st.success("Memory state exported to memory_state.json")
    
    def import_memory_state(self):
        """Import memory state from file"""
        import json
        try:
            with open('memory_state.json', 'r') as f:
                state = json.load(f)
            
            # Recreate memory manager
            self.memory_manager = MemoryManager(1024)
            self.memory_manager.memory_map = []
            
            # Restore memory map
            for block_data in state['memory_map']:
                block = type('Block', (), {})()
                block.start = block_data['start']
                block.size = block_data['size']
                block.pid = block_data['pid']
                block.end = block.start + block.size - 1
                self.memory_manager.memory_map.append(block)
            
            # Restore processes
            st.session_state.app_state['process_history'] = []
            for proc_data in state['processes']:
                from process_generator import Process
                process = Process(
                    pid=proc_data['pid'],
                    size=proc_data['size'],
                    arrival_time=proc_data['arrival_time'],
                    duration=proc_data['duration']
                )
                st.session_state.app_state['process_history'].append(process)
            
            st.success("Memory state imported successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to import: {str(e)}")
    
    def run(self):
        """Main application runner"""
        self.setup()
        
        # Header
        st.title("💾 Memory Management Simulator")
        st.markdown("**OS Memory Allocation Algorithms - Real-time Simulation**")
        st.markdown("---")
        
        # Create layout
        self.create_sidebar()
        
        # Main content area
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Display memory visualization
            if self.visualizer:
                self.visualizer.display_memory_map()
                self.visualizer.display_fragmentation_chart()
        
        with col2:
            # Display statistics
            self.display_statistics()
            self.display_process_list()
        
        # Algorithm comparison
        st.markdown("---")
        self.display_algorithm_comparison()
        
        # System info footer
        st.markdown("---")
        st.caption(f"🎓 Operating Systems Simulation | Total Memory: {self.memory_manager.total_memory}KB | "
                  f"Algorithm: {st.session_state.app_state['algorithm'].value}")
    
    def display_statistics(self):
        """Display memory statistics"""
        st.subheader("📈 Statistics")
        stats = self.memory_manager.get_statistics()
        
        st.metric("Memory Utilization", f"{stats['utilization']:.1f}%")
        st.metric("External Fragmentation", f"{stats['external_fragmentation']:.1f}%")
        st.metric("Internal Fragmentation", f"{stats['internal_fragmentation']:.0f} KB")
        st.metric("Free Memory", f"{stats['available_memory']} KB")
        st.metric("Memory Blocks", stats['memory_blocks'])
        st.metric("Allocated Processes", stats['allocated_processes'])
    
    def display_process_list(self):
        """Display list of running processes"""
        st.subheader("📋 Active Processes")
        
        if self.memory_manager.allocated_processes:
            for pid, block in self.memory_manager.allocated_processes.items():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{pid}**")
                        st.caption(f"Size: {block.size}KB | Range: {block.start}-{block.end}")
                    with col2:
                        if st.button("❌", key=f"free_{pid}"):
                            self.memory_manager.deallocate(pid)
                            st.rerun()
        else:
            st.info("No active processes")
    
    def display_algorithm_comparison(self):
        """Display algorithm comparison chart"""
        st.subheader("📊 Algorithm Performance Comparison")
        
        # Simulate performance for different algorithms
        algorithms = list(AllocationAlgorithm)
        performance_data = []
        
        for algo in algorithms:
            # Simulate allocation success rate
            temp_manager = MemoryManager(1024)
            test_generator = ProcessGenerator()
            test_processes = test_generator.generate_batch(20)
            
            success_count = 0
            for process in test_processes:
                if algo == AllocationAlgorithm.FIRST_FIT:
                    success, _ = temp_manager.first_fit(process)
                elif algo == AllocationAlgorithm.BEST_FIT:
                    success, _ = temp_manager.best_fit(process)
                elif algo == AllocationAlgorithm.WORST_FIT:
                    success, _ = temp_manager.worst_fit(process)
                elif algo == AllocationAlgorithm.NEXT_FIT:
                    success, _ = temp_manager.next_fit(process)
                elif algo == AllocationAlgorithm.BUDDY_SYSTEM:
                    success, _ = temp_manager.buddy_system(process)
                
                if success:
                    success_count += 1
            
            performance_data.append({
                'Algorithm': algo.value,
                'Success Rate': (success_count / len(test_processes)) * 100,
                'Fragmentation': temp_manager.fragmentation_history[-1]['external'] if temp_manager.fragmentation_history else 0
            })
        
        # Display as metrics
        cols = st.columns(len(algorithms))
        for idx, data in enumerate(performance_data):
            with cols[idx]:
                st.metric(
                    data['Algorithm'],
                    f"{data['Success Rate']:.1f}%",
                    f"Frag: {data['Fragmentation']:.1f}%"
                )

# Run the application
if __name__ == "__main__":
    app = MemoryManagementApp()
    app.run()