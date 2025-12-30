# Memory Management Analyzer

An interactive web application for visualizing and analyzing Operating System memory management algorithms.

## Features

- **Multiple Allocation Algorithms**: First Fit, Best Fit, Worst Fit, Next Fit, and Buddy System
- **Real-time Visualization**: Interactive memory map showing allocated and free blocks
- **Fragmentation Tracking**: Monitor external and internal fragmentation
- **Process Generation**: Manual, batch, and automatic process generation
- **Statistics Dashboard**: Real-time memory utilization and performance metrics

## Algorithms Implemented

1. **First Fit** - Allocates to the first available block that fits
2. **Best Fit** - Finds the smallest block that can accommodate the process
3. **Worst Fit** - Uses the largest available block
4. **Next Fit** - Continues search from the last allocation point
5. **Buddy System** - Uses power-of-2 sized blocks for allocation

## Running Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Project Structure

```
memory-management-analyzer/
├── streamlit_app.py          # Main entry point
├── requirements.txt          # Dependencies
├── src/
│   ├── main.py              # Application controller
│   ├── memory_simulator.py  # Core allocation algorithms
│   ├── memory_visualizer.py # Visualization components
│   └── process_generator.py # Process generation logic
├── docs/
│   ├── algorithm_docs.md    # Algorithm documentation
│   └── user_manual.md       # User guide
└── tests/
    └── test_algorithms.py   # Unit tests
```

## Usage

1. **Configure Memory**: Set total memory size in the sidebar
2. **Select Algorithm**: Choose from 5 allocation algorithms
3. **Generate Processes**: 
   - Manual: Specify size and add individual processes
   - Batch: Generate 5 or 10 processes at once
   - Auto: Continuously generate processes at intervals
4. **Monitor Performance**: Watch memory map and statistics update in real-time
5. **Free Memory**: Deallocate processes or clear all

## Author

OS Memory Management Simulation Project
