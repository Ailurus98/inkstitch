"""
Unit tests for data state validation and immutability.
"""

import sys, os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from lib.gui.grid_state import GridStateManager, Cell, MAX_ROWS, MAX_COLS


def test_grid_bounds():
    with pytest.raises(ValueError):
        GridStateManager(rows=MAX_ROWS + 1, cols=50)

    with pytest.raises(ValueError):
        GridStateManager(rows=50, cols=-1)
        
    state = GridStateManager(rows=50, cols=50)
    assert state.in_bounds(0, 0)
    assert not state.in_bounds(50, 50)
    
def test_cell_storage():
    state = GridStateManager(rows=10, cols=10)
    state.set_cell(5, 5, Cell())

    assert state.get_cell(5, 5) is not None
    assert state.get_cell(0, 0) is None

    with pytest.raises(ValueError):
        state.set_cell(20, 20, Cell())

def test_clone_isolation():
    state = GridStateManager(10, 10)
    state.set_cell(1, 1, Cell())

    new_state = state.clone()
    new_state.set_cell(2, 2, Cell())

    # Original unaffected by changes to the clone
    assert state.get_cell(1, 1) is not None
    assert state.get_cell(2, 2) is None

    # Clone has both cells
    assert new_state.get_cell(1, 1) is not None
    assert new_state.get_cell(2, 2) is not None
