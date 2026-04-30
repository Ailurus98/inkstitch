"""
Performance regression tests for Cross Stitch Canvas.
"""

import time
import pytest
import sys
import os

# Ensure the library root is in sys path if this test is run standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from lib.gui.grid_state import GridStateManager, Cell


def test_clone_performance():
    """
    Ensure the clone process completely avoids slow deepcopy operations and 
    finishes under 50ms to maintain smooth UX during dragging/undo operations.
    """
    state = GridStateManager(rows=100, cols=100)
    
    # Paint 2000 random cells sparsely simulating a high-density fill area
    count = 0
    for r in range(100):
        for c in range(100):
            if count >= 2000:
                break
            if (r + c) % 2 == 0:
                state.set_cell(r, c, Cell(thread_id="#F00"))
                count += 1
                
    assert len(state.cells) == 2000
    
    # Measure clone cost strictly on logic level
    start_t = time.perf_counter()
    new_state = state.clone()
    end_t = time.perf_counter()
    
    elapsed_ms = (end_t - start_t) * 1000.0
    
    # Check baseline data replication validity
    assert id(state.cells) != id(new_state.cells)
    assert len(new_state.cells) == 2000
    
    # Check memory isolation (Modifying one should not alter the other)
    state.clear_cell(0, 0)
    assert len(state.cells) < 2000
    assert len(new_state.cells) == 2000
    
    # The performance boundary is tightly coupled to UX. >50ms indicates deepcopy rot.
    assert elapsed_ms < 50.0, f"Clone performance regression: took {elapsed_ms:.2f}ms (Budget is 50.0ms)"
