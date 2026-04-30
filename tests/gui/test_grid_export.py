"""
Tests DOM conversion logic generating raw outputs formatting the tagged EXPORT_GROUP.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from lib.gui.grid_state import GridStateManager, Cell
from lib.gui.grid_export import build_export_group, export_to_svg, EXPORT_GROUP_ID
from lxml import etree
import inkex

CELL_SIZE = 15.0  # Cell size in pixels, matching canvas GUI

def test_build_export_group():
    state = GridStateManager(50, 50)
    state.set_cell(0, 0, Cell("Red"))
    state.set_cell(0, 1, Cell("Red"))
    state.set_cell(5, 5, Cell("Blue"))
    
    group = build_export_group(state, CELL_SIZE)
    assert isinstance(group, inkex.Group)
    assert group.get("id") == EXPORT_GROUP_ID
    
    # Ensures payload injection functions structurally.
    assert group.get("inkstitch:grid-state") is not None
    
    # Group clustering functions, output contains 2 unique DOM trees matching color count
    assert len(group) == 2
    
def test_export_replacement():
    svg = inkex.SvgDocumentElement()
    layer = inkex.Layer()
    svg.append(layer)
    
    # Sequence 1. Export initial state
    state = GridStateManager()
    state.set_cell(0, 0, Cell("X"))
    export_to_svg(svg, layer, state, CELL_SIZE)
    
    assert len(layer) == 1
    assert layer[0].get("id") == EXPORT_GROUP_ID
    
    # Sequence 2. Export appended state (Testing precise atomic replacement over duplication bug)
    state.set_cell(1, 1, Cell("Y"))
    export_to_svg(svg, layer, state,CELL_SIZE)
    
    assert len(layer) == 1 # Retains strictly a single DOM node bounding the map payload
    
    # Sequence 3. User fully erases screen and triggers export
    state.clear_cell(0, 0)
    state.clear_cell(1, 1)
    export_to_svg(svg, layer, state, CELL_SIZE)
    
    # Verify exact replication of UX Option A behavior tearing the artifact fully.
    assert len(layer) == 0
