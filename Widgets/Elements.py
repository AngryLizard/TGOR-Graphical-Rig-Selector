import bpy

import gpu
import bgl
from gpu_extras.batch import batch_for_shader

from .Base import Symbols
from .Base import Util

from . import Surfaces

####################################################################################

class Vertex(Symbols.Circle):
    """Interface element"""
        
    # Update callback
    _update = None
            
    # Update callback
    _index = -1
    
    # Constructor
    def __init__(self, pos, radius, index, callback):
        super().__init__(pos, radius)
        self._active = True
        self._grid = True
        self._index = index
        self._update = callback
        self._colour = (0.4, 0.4, 0.4, 0.9)
        
    
    @Util.Overrides(Symbols.Interactable)
    def isGrabZone(self, context, pos):
        return True
    
    @Util.Overrides(Symbols.Interactable)
    def dropped(self, context, pos):
        
        # Check update
        if self._update:
            self._update(context, self)
    
    @Util.Overrides(Symbols.Interactable)
    def store(self, context, buffer):
        
        buffer.write("index", self._index)
        
        super().store(context, buffer)
    
    @Util.Overrides(Symbols.Interactable)
    def load(self, context, buffer):
        
        self._index = buffer.read("index", int, "0")
        if self._index <= -1:
            buffer.error("index", "Negative index")
            
        super().load(context, buffer)


####################################################################################

class Median(Symbols.Rectangle):
    """Median Interface element, contains all the selector buttons"""
        
    # Container
    _container = None
    
    # Constructor
    def __init__(self):
        super().__init__((0.0, 0.0), (3.0, 0.0))
        self._colour = (0.0, 0.0, 0.0, 0.5)
                
        self._container = self.addChild(Surfaces.Container())
    
    # Removes a selector
    def removeSelector(self, context, selector):
        self._container.removeSelector(context, selector)
    
    # Toggles edit mode on or off
    def toggleEdit(self, context, active):
        self._container.toggleEdit(context, active)
    
    # Adds a vertex to a new button or current focus
    def addVertex(self, context, pos):
        x = pos[0] - self._pos[0]
        y = pos[1] - self._pos[1]
        
        self._container.addVertex(context, (x, y))
    
    @Util.Overrides(Symbols.Rectangle)
    def draw(self, context, parent, scale):
    
        symmetry = bpy.context.scene.enableRigSelector.symmetry
        self._colour = (0.0, 0.0, 0.0, 0.5) if symmetry else (0.0, 0.0, 0.0, 0.0)
            
        super().draw(context, parent, scale)
        
    
    # Update visibility depending on whether any buttons are visible
    def updateVisibility(self, context):
        
        # Only draw if container is active
        self._visible = self._container.updateVisibility(context)
        return self._visible
    
    
    @Util.Overrides(Symbols.Rectangle)
    def store(self, context, buffer):
        
        sub = buffer.sub("container")
        self._container.store(context, sub)
                
        super().store(context, buffer)
    
    @Util.Overrides(Symbols.Rectangle)
    def load(self, context, buffer):
        
        sub = buffer.sub("container")
        self._container.load(context, sub)
        
        super().load(context, buffer)