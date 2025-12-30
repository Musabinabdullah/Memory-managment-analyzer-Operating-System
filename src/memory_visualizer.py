"""
Memory Visualizer for Memory Management Simulator
Provides Streamlit-friendly visualization utilities for the memory map
and fragmentation charts used by the main application.
"""

from typing import List
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time


class MemoryVisualizer:
    """Visualizes the memory map and fragmentation history."""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager

    def display_memory_map(self):
        """Render a horizontal memory map showing allocated/free blocks."""
        blocks = self.memory_manager.memory_map
        total = self.memory_manager.total_memory

        if not blocks:
            st.info("No memory blocks to display")
            return

        fig = go.Figure()
        shapes = []
        annotations = []

        for block in blocks:
            x0 = block.start
            x1 = block.start + block.size
            color = "lightgrey" if block.pid == "FREE" else "#5DADE2"
            shapes.append({
                "type": "rect",
                "x0": x0,
                "x1": x1,
                "y0": 0,
                "y1": 1,
                "fillcolor": color,
                "line": {"width": 1, "color": "#111"},
                "opacity": 0.9,
            })

            label = f"{block.pid}\n{block.size}KB"
            annotations.append({
                "x": x0 + block.size / 2,
                "y": 0.5,
                "text": label,
                "showarrow": False,
                "font": {"size": 10}
            })

        fig.update_layout(
            shapes=shapes,
            annotations=annotations,
            xaxis=dict(range=[0, max(total, sum(b.size for b in blocks))], title="Memory (KB)"),
            yaxis=dict(visible=False),
            height=150,
            margin=dict(l=10, r=10, t=10, b=10)
        )

        st.subheader("Memory Map")
        st.plotly_chart(fig, use_container_width=True)

        # Also display textual map below
        rows = []
        for block in blocks:
            rows.append({
                "Start": block.start,
                "End": block.start + block.size - 1,
                "Size (KB)": block.size,
                "PID": block.pid,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df)

    def display_fragmentation_chart(self):
        """Plot fragmentation history (external/internal) over time."""
        history = self.memory_manager.fragmentation_history

        st.subheader("Fragmentation History")
        if not history:
            st.info("No fragmentation data available yet")
            return

        df = pd.DataFrame(history)
        # convert timestamps to relative seconds for readability
        t0 = df['time'].min()
        df['elapsed'] = df['time'] - t0

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['elapsed'], y=df['external'], mode='lines+markers', name='External (%)'))
        fig.add_trace(go.Scatter(x=df['elapsed'], y=df['internal'], mode='lines+markers', name='Internal (KB)'))
        fig.update_layout(xaxis_title='Seconds', yaxis_title='Value')

        st.plotly_chart(fig, use_container_width=True)
