"""
End to end UI event loop integration validation map.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from lib.gui.grid_state import GridStateManager, Cell
from lib.gui.undo_manager import UndoManager
from lib.gui.cross_stitch_canvas import CrossStitchCanvasWindow
from lib.gui.grid_export import export_to_svg
from lib.gui.grid_visualizer import GridVisualizer
from lib.gui.grid_interaction import GridInteractionEngine
import inkex
import wx

def test_canvas_e2e():
    app = wx.App(False)
    frame = CrossStitchCanvasWindow(None)
    
    engine = frame.interaction
    state = frame.state
    undo_mgr = frame.undo_mgr
    
    # Configure tool stroke
    engine.active_thread = "Red"
    engine.current_tool = "pencil"
    
    # Fire simulated bounds sequence modeling exactly what physical hardware passes
    engine.on_mouse_down(10.0, 10.0)
    engine.on_mouse_move(15.0, 15.0) 
    engine.on_mouse_up(20.0, 20.0)
    
    initial_paint_count = len(state.cells)
    assert initial_paint_count > 0, "Interaction engine failed to mount visual mutations on simulated drag."
    
    # Core Regression Action: Simulate GUI level click mapping
    new_state = undo_mgr.undo(state)
    frame.state = new_state
    
    assert len(frame.state.cells) == 0, "Undo UI sequence isolated integration failed."
    
    # Validate trace pushes smoothly ahead simulating typical accident recovery
    frame.state = undo_mgr.redo(frame.state)
    assert len(frame.state.cells) == initial_paint_count
    
    # Export system captures state payload safely
    svg = inkex.SvgDocumentElement()
    layer = inkex.Layer()
    svg.append(layer)
    export_to_svg(svg, layer, frame.state, 5.0)
    
    assert len(layer) == 1
    
    # Tear UI boundaries to avoid test block leaks
    frame.Destroy()
    app.Destroy()
