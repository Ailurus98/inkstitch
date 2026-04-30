"""
Tests snapshot semantics and bounding logic caps.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from lib.gui.grid_state import GridStateManager, Cell
from lib.gui.undo_manager import UndoManager, MAX_UNDO_STEPS

def test_undo_stack_accumulates():
    state = GridStateManager(10, 10)
    mgr = UndoManager(state)
    assert not mgr.can_undo()
    
    state.set_cell(0, 0, Cell(thread_id="A"))
    # Save UX frame representing standard snapshot pattern during UI Down sequence.
    mgr.save_state(state)
    
    state.set_cell(1, 1, Cell(thread_id="B"))
    mgr.save_state(state)
    
    assert mgr.can_undo()
    assert len(mgr.undo_stack) == 3 # Boot baseline + 2 interactive saves

def test_undo_redo_reversals():
    state = GridStateManager(10, 10)
    mgr = UndoManager(state)
    
    # State 1 (base empty)
    
    mgr.save_state(state)
    state.set_cell(0, 0, Cell("A"))
    # State 2 (painted 0,0)
    
    mgr.save_state(state)
    state.set_cell(1, 1, Cell("B"))
    # State 3 (painted 1,1)
    
    assert state.get_cell(1, 1) is not None
    
    # Request reversion
    state = mgr.undo(state)
    assert state.get_cell(1, 1) is None
    assert state.get_cell(0, 0).thread_id == "A"
    
    # Request second reversion targeting boot block
    state = mgr.undo(state)
    assert state.get_cell(0, 0) is None
    
    # Validate redo trace pushing into forward buffer seamlessly
    state = mgr.redo(state)
    assert state.get_cell(0, 0).thread_id == "A"
    assert state.get_cell(1, 1) is None

def test_max_undo_steps():
    state = GridStateManager(10, 10)
    mgr = UndoManager(state)
    
    for i in range(20):
        mgr.save_state(state)
        state.set_cell(0, 0, Cell(str(i)))
        
    # Cap operates uniformly avoiding blowout.
    assert len(mgr.undo_stack) == MAX_UNDO_STEPS + 1
