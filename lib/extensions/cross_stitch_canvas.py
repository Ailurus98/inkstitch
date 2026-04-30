#!/usr/bin/env python
# coding=utf-8

"""
Entry point for the Cross Stitch Canvas inkstitch extension.
"""

import sys
import wx
import inkex

# For Ink/Stitch standard routing we mock sys.path in standard extensions if needed,
# however since these scripts are run dynamically within an Inkstitch context we path 
# relative components.
from lib.gui.cross_stitch_canvas import CrossStitchCanvasWindow
from lib.gui.grid_export import export_to_svg


class CrossStitchCanvas(inkex.EffectExtension):
    """
    Standard Inkstitch Hook implementation launching our new specialized interactive GUI.
    """
    def add_arguments(self, pars):
        # Boilerplate stub matching normal Inkstitch `Helper` templates
        pass

    def effect(self):
        # Get active layer pointer to enforce SVG grouping behavior
        # (Using a stubbed fallback for get_current_layer to run correctly without breaking if refactored)
        layer = self.svg.get_current_layer()
        
        # Initiate underlying Wx Python context
        app = wx.App(False)
        frame = CrossStitchCanvasWindow(None)
        
        # Ink/Stitch UI panels must block program thread so they can run safely
        frame.Show()
        app.MainLoop()
        
        # Once closed, we extract final internal memory state and emit vectors
        if hasattr(frame, 'state'):
            export_to_svg(
                svg_doc=self.svg,
                layer=layer,
                grid_state=frame.state,
                cell_size=13.0, # Match canvas cell size
                correction_transform=layer.transform
            )
            
if __name__ == '__main__':
    CrossStitchCanvasExtension().run()
