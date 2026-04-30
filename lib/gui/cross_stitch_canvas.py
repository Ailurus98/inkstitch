"""
Main window wrapper assembling the Cross Stitch Canvas GUI components.
"""

import wx
from .grid_state import GridStateManager
from .grid_visualizer import GridVisualizer
from .grid_interaction import GridInteractionEngine
from .undo_manager import UndoManager


class CrossStitchCanvasWindow(wx.Frame):
    def __init__(self, parent, title="Cross Stitch Canvas MVP"):
        super().__init__(parent, title=title, size=(1200, 900))
        
        # Enforce Fixed 50x50 MVP boundaries (Will be loaded from state in Phase 2)
        self.state = GridStateManager(rows=50, cols=50)
        self.undo_mgr = UndoManager(self.state)
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self._init_ui()
        
    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Tool Palette
        toolbar = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_pencil = wx.Button(self, label="Pencil")
        btn_eraser = wx.Button(self, label="Eraser")
        btn_undo = wx.Button(self, label="Undo")
        btn_redo = wx.Button(self, label="Redo")
        
        # Use simple color picker to simulate Thread Palette hex returns for Phase 1
        self.color_picker = wx.ColourPickerCtrl(self, colour=wx.Colour("#CC0000"))
        
        toolbar.Add(btn_pencil, 0, wx.ALL, 5)
        toolbar.Add(btn_eraser, 0, wx.ALL, 5)
        toolbar.Add(btn_undo, 0, wx.ALL, 5)
        toolbar.Add(btn_redo, 0, wx.ALL, 5)
        toolbar.AddSpacer(20)
        toolbar.Add(wx.StaticText(self, label="Active Thread:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        toolbar.Add(self.color_picker, 0, wx.ALL, 5)
        
        # Blank Canvas Workspace
        self.canvas_panel = wx.Panel(self)
        self.canvas_panel.SetBackgroundStyle(wx.BG_STYLE_PAINT) # Avoids flicker on windows
        
        # Link View Logic and Input Handlers
        cell_size = 13.0 # Larger cells for better visibility
        self.visualizer = GridVisualizer(self.canvas_panel, cell_size=cell_size)
        # Center the grid in the canvas
        self.visualizer.offset_x = 225 
        self.visualizer.offset_y = 0
        self.interaction = GridInteractionEngine(self.visualizer, self.state, self.undo_mgr)
        
        # Boot sequence values
        self.interaction.active_thread = self.color_picker.GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
        
        # Subscribe Canvas Raw Events
        self.canvas_panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.canvas_panel.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.canvas_panel.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.canvas_panel.Bind(wx.EVT_MOTION, self.on_mouse_move)

        # Wire Toolbar logic
        btn_pencil.Bind(wx.EVT_BUTTON, lambda e: self.set_tool("pencil"))
        btn_eraser.Bind(wx.EVT_BUTTON, lambda e: self.set_tool("eraser"))
        btn_undo.Bind(wx.EVT_BUTTON, self.on_undo)
        btn_redo.Bind(wx.EVT_BUTTON, self.on_redo)
        self.color_picker.Bind(wx.EVT_COLOURPICKER_CHANGED, self.on_color_changed)
        
        main_sizer.Add(toolbar, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.canvas_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
        self.Layout()
        
    def set_tool(self, tool_name):
        self.interaction.current_tool = tool_name
        
    def on_color_changed(self, event):
        color = self.color_picker.GetColour()
        hex_string = color.GetAsString(wx.C2S_HTML_SYNTAX)
        self.interaction.active_thread = hex_string
        
    def on_undo(self, event):
        new_state = self.undo_mgr.undo(self.state)
        if new_state is not self.state:
            self.state = new_state
            self.interaction.state = self.state
            self.visualizer.mark_all_dirty(self.state)
            self.canvas_panel.Refresh()
            
    def on_redo(self, event):
        new_state = self.undo_mgr.redo(self.state)
        if new_state is not self.state:
            self.state = new_state
            self.interaction.state = self.state
            self.visualizer.mark_all_dirty(self.state)
            self.canvas_panel.Refresh()

    def on_paint(self, event):
        # We dummy-map the thread ID as the palette hex code directly for rendering Phase 1
        palette = { tid: tid for tid in self._get_unique_threads() }
        self.visualizer.on_paint(event, self.state, palette)
        
    def _get_unique_threads(self):
        """Helper to fake a full threaded palette tracking abstraction wrapper."""
        return set([cell.thread_id for pos, cell in self.state.cells.items() if cell.thread_id])

    def on_mouse_down(self, event):
        self.interaction.on_mouse_down(event.GetX(), event.GetY())
        
    def on_mouse_up(self, event):
        self.interaction.on_mouse_up(event.GetX(), event.GetY())
        
    def on_mouse_move(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.interaction.on_mouse_move(event.GetX(), event.GetY())

    def on_close(self, event):
        # Allow GUI blocks to collapse so SVG writes can finish
        self.Destroy()
