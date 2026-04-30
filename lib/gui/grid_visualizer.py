"""
Rendering Layer for the Cross Stitch Canvas.

Responsible for taking the pure logic state from GridStateManager
and interpreting it into a screen-space pixel map using wx.
"""

import wx
from typing import Set, Tuple, List
from .grid_state import GridStateManager, Cell
from .grid_mapper import grid_to_svg


class GridVisualizer:
    def __init__(self, parent_window: wx.Window, cell_size: float):
        self.window = parent_window
        self.cell_size = cell_size
        
        # View Transforms (User Zoom/Pan)
        self.scale: float = 1.0
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        
        # HiDPI explicit scaling factor (Device property) MUST strictly be separated from zoom
        self.dpi_scale: float = self._compute_dpi_scale()
        
        # Tracking explicit regions to repaint
        self.dirty_cells: Set[Tuple[int, int]] = set()
        
    def _compute_dpi_scale(self) -> float:
        """Query wx for actual screen scaling to properly render fine geometry."""
        if hasattr(self.window, "GetContentScaleFactor"):
            return self.window.GetContentScaleFactor()
        elif hasattr(self.window, "GetDPIScaleFactor"):
            return self.window.GetDPIScaleFactor()
        return 1.0
        
    def mark_dirty(self, row: int, col: int) -> None:
        """Add a cell to the repaint queue."""
        self.dirty_cells.add((row, col))
        
    def mark_all_dirty(self, state: GridStateManager) -> None:
        """Queue the entire grid for a complete repaint sequence."""
        for r in range(state.rows):
            for c in range(state.cols):
                self.dirty_cells.add((r, c))
                
    def request_render(self, state: GridStateManager) -> None:
        """
        Called when interactions finish a batch. Safely transfers UI invalidation.
        """
        if not self.dirty_cells:
            return
            
        cells_to_draw = self.dirty_cells.copy()
        self.dirty_cells.clear()
        
        # Push paint trigger bounded by region to asynchronous GUI cycle
        wx.CallAfter(self._flush_dirty_as_region, cells_to_draw, state)

    def _flush_dirty_as_region(self, cells_to_draw: Set[Tuple[int, int]], state: GridStateManager) -> None:
        """
        Compute bounding rect of dirty cells to avoid intense individual 1x1 cell draw queues.
        Calls self.window.RefreshRect.
        """
        if not cells_to_draw:
            return
            
        # Fallback Rule: If the dirty subset > 30% of canvas, doing scatter bounds is more costly than a full Refresh
        threshold = state.rows * state.cols * 0.3
        if len(cells_to_draw) > threshold:
            self.window.Refresh()
            return
            
        min_r = min(r for r, c in cells_to_draw)
        max_r = max(r for r, c in cells_to_draw)
        min_c = min(c for r, c in cells_to_draw)
        max_c = max(c for r, c in cells_to_draw)
        
        # Calculate bounding box bounds back into screen space
        x1, y1 = self.logical_to_screen(min_r, min_c)
        x2, y2 = self.logical_to_screen(max_r + 1, max_c + 1)
        
        # Enveloping Rect dimensions representing the union bounds of the drag trail
        rect = wx.Rect(int(x1), int(y1), int(x2 - x1) + 1, int(y2 - y1) + 1)
        self.window.RefreshRect(rect, eraseBackground=False)

    def logical_to_screen(self, row: int, col: int) -> Tuple[float, float]:
        """Project from logical abstract indices strictly to final GUI rendering points."""
        svg_x, svg_y = grid_to_svg(row, col, self.cell_size)
        
        # Apply Transforms: User View Layer
        zoom_x = (svg_x * self.scale) + self.offset_x
        zoom_y = (svg_y * self.scale) + self.offset_y
        
        # Apply Transforms: Hardware Pixel Layer
        return zoom_x * self.dpi_scale, zoom_y * self.dpi_scale

    def on_paint(self, event, state: GridStateManager, palette_colors: dict) -> None:
        """
        Hooked directly directly to parent EVT_PAINT.
        """
        dc = wx.BufferedPaintDC(self.window)
        # Handle clear background
        dc.SetBackground(wx.Brush(wx.Colour(245, 245, 245)))
        dc.Clear()
        
        # Note: Paint routing draws entirely inside the requested subset boundaries requested via RefreshRect
        
        self._draw_grid_lines(dc, state)
        
        for (r, c), cell in state.cells.items():
            self._draw_cell(dc, r, c, cell, palette_colors)
            
    def _draw_grid_lines(self, dc: wx.DC, state: GridStateManager):
        """Phase 1 basic grid wireframe styling."""
        
        for r in range(state.rows + 1):
            if r % 5 == 0:
                dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))  # Black for every fifth row, thicker
            else:
                dc.SetPen(wx.Pen(wx.Colour(0, 0, 139), 1))  # Dark blue for others
            sx1, sy1 = self.logical_to_screen(r, 0)
            sx2, sy2 = self.logical_to_screen(r, state.cols)
            dc.DrawLine(int(sx1), int(sy1), int(sx2), int(sy2))
            
        for c in range(state.cols + 1):
            if c % 5 == 0:
                dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))  # Black for every fifth column, thicker
            else:
                dc.SetPen(wx.Pen(wx.Colour(0, 0, 139), 1))  # Dark blue for others
            sx1, sy1 = self.logical_to_screen(0, c)
            sx2, sy2 = self.logical_to_screen(state.rows, c)
            dc.DrawLine(int(sx1), int(sy1), int(sx2), int(sy2))

    def _draw_cell(self, dc: wx.DC, r: int, c: int, cell: Cell, palette_colors: dict):
        """Draw individual grid cells utilizing provided thread_id identifiers."""
        hex_col = palette_colors.get(cell.thread_id, "#444444")
        dc.SetPen(wx.Pen(wx.Colour(hex_col), 2, wx.PENSTYLE_SOLID))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        
        sx1, sy1 = self.logical_to_screen(r, c)
        sx2, sy2 = self.logical_to_screen(r + 1, c + 1)
        
        # Inset the cross slightly so it doesn't overlap the grid lines
        padding = min((sx2 - sx1), (sy2 - sy1)) * 0.15
        sx1 += padding
        sy1 += padding
        sx2 -= padding
        sy2 -= padding

        dc.DrawLine(int(sx1), int(sy1), int(sx2), int(sy2))
        dc.DrawLine(int(sx1), int(sy2), int(sx2), int(sy1))
