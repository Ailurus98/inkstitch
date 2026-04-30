"""
Tests mapper contracts mapping physical space points into index grids.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from lib.gui.grid_mapper import grid_to_svg, svg_to_grid

def test_grid_to_svg():
    cell_size = 5.0
    assert grid_to_svg(0, 0, cell_size) == (0.0, 0.0)
    assert grid_to_svg(10, 5, cell_size) == (25.0, 50.0)

def test_svg_to_grid():
    cell_size = 5.0
    # Perfect alignment (Top Left of cell 10, 5)
    assert svg_to_grid(25.0, 50.0, cell_size, 100, 100) == (10, 5)
    # Inside the cell body arbitrarily
    assert svg_to_grid(27.0, 53.0, cell_size, 100, 100) == (10, 5)
    
def test_svg_to_grid_clamping():
    cell_size = 5.0
    # Negative bounds clamp explicitly to 0 (top left corner)
    assert svg_to_grid(-10.0, -50.0, cell_size, 100, 100) == (0, 0)
    # Huge bounds clamp explicitly inside absolute canvas boundary to prevent matrix overloads
    assert svg_to_grid(1000.0, 2000.0, cell_size, 50, 50) == (49, 49)
