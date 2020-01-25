import bpy

import gpu
import bgl
from gpu_extras.batch import batch_for_shader

from .Base import Symbols
from .Base import Util
from . import Elements
from . import Selectors

####################################################################################

class Interface(Symbols.Rectangle):
    """Interface element"""
        
    # Corners for resize
    _corners = []
    
    # Background image name
    _background = ""
    
    # Median
    _median = None
    _medianVertex = None
    _medianRatio = 0.5
    _heightVertex = None
    _heightRatio = 0.5
    
    # Edit state
    _edit = False
        
    # Constructor
    def __init__(self, pos, size):
        super().__init__(pos, size)
        self._active = True
        self._colour = (0.1, 0.1, 0.1, 0.2)
        self._corners = []
        
        self._median = self.addChild(Elements.Median())
    
    @Util.Overrides(Symbols.Interactable)
    def isGrabZone(self, context, pos):
        return not self._edit
    
    @Util.Overrides(Symbols.Interactable)
    def dropped(self, context, pos):
        
        if context.scene.enableRigSelector.clamp:
            
            # Get scale setting
            scaleAll = context.scene.enableRigSelector.scaleAll
            
            # Screen size
            screenX = context.region.width / scaleAll - self._size[0]
            screenY = context.region.height / scaleAll - self._size[1]
            
            self._pos = (max(self._pos[0], 0.0), max(self._pos[1], 0.0))
            self._pos = (min(self._pos[0], screenX), min(self._pos[1], screenY))
    
    @Util.Overrides(Symbols.Interactable)
    def clicked(self, context, pos, right, shift):
        
        # Add Vertex
        self._median.addVertex(context, pos)
    
    @Util.Overrides(Symbols.Rectangle)
    def draw(self, context, parent, scale):
        
        # Make sure interface is inside screen
        self.dropped(context, (0.0, 0.0))
        
        # Set correct median position
        self._median._container._pos = (0.0, self._size[1] * self._heightRatio)
        self._median._pos = (self._size[0] * self._medianRatio - self._median._size[0] / 2, 0.0)
        self._median._size = (self._median._size[0], self._size[1])
        
        # Compute background colour
        self._border = None
        setting = context.scene.enableRigSelector.alpha
        if Util._selectedInterface == self:
            if self._edit:
                self._border = (1.0, 1.0, 1.0, 0.8)
                self._colour = (0.2, 0.1, 0.1, setting)
            else:
                self._colour = (0.1, 0.1, 0.1, setting)
        else:
            if self._edit:
                self._colour = (0.2, 0.1, 0.1, 0.8 * setting)
            else:
                self._colour = (0.1, 0.1, 0.1, 0.8 * setting)
        
        # Get background image
        if self._background and self._background in bpy.data.images:
            self._image = bpy.data.images[self._background]
        
        # Only draw background if any buttons are active
        if self._median.updateVisibility(context):
            super().draw(context, parent, scale)
    
    # Enable or disable edit mode
    def toggleEdit(self, context, active):
        
        # Toggle median
        if self._median:
            self._median.toggleEdit(context, active)
        
        # Set mode
        self._edit = active
        
        # Adapt edit vertices
        if active: 
            if not self._corners:
            
                # Create corner vertices
                self._corners.append(self.addChild(Elements.Vertex((0.0, 0.0), 6.0, 0, self.adaptSize)))
                self._corners.append(self.addChild(Elements.Vertex((self._size[0], 0.0), 6.0, 1, self.adaptSize)))
                self._corners.append(self.addChild(Elements.Vertex((0.0, self._size[1]), 6.0, 2, self.adaptSize)))
                self._corners.append(self.addChild(Elements.Vertex((self._size[0], self._size[1]), 6.0, 3, self.adaptSize)))
                self._corners[0]._grid = False
                self._corners[1]._grid = False
                self._corners[2]._grid = False
                self._corners[3]._grid = False
                
                # Create median vertex
                self._medianVertex = self.addChild(Elements.Vertex((self._median._pos[0] + 1, -8.0), 6.0, 4, self.adaptMedian))
                self._heightVertex = self.addChild(Elements.Vertex((-8.0, self._median._container._pos[1] + 1), 6.0, 5, self.adaptHeight))
                self._medianVertex._grid = False
                self._heightVertex._grid = False
                
        elif self._corners:
            
            # Remove corner
            self.removeChild(self._corners[0])
            self.removeChild(self._corners[1])
            self.removeChild(self._corners[2])
            self.removeChild(self._corners[3])
            self._corners.clear()
            
            # Remove median vertex
            self.removeChild(self._medianVertex)
            self._medianVertex = None
            self.removeChild(self._heightVertex)
            self._heightVertex = None
    
    
    # Change size depending on vertex
    def adaptSize(self, context, vertex):
        
        # Change position/size depending on edit vertices
        if vertex._index == 0:
            self._pos = (self._pos[0] + vertex._pos[0], self._pos[1] + vertex._pos[1])
            self._size = (self._size[0] - vertex._pos[0], self._size[1] - vertex._pos[1])
            vertex._pos = (0.0, 0.0)
            
        elif vertex._index == 1:
            self._pos = (self._pos[0], self._pos[1] + vertex._pos[1])
            self._size = (vertex._pos[0], self._size[1] - vertex._pos[1])
            vertex._pos = (self._size[0], 0.0)
            
        elif vertex._index == 2:
            self._pos = (self._pos[0] + vertex._pos[0], self._pos[1])
            self._size = (self._size[0] - vertex._pos[0], vertex._pos[1])
            vertex._pos = (0.0, self._size[1])
            
        elif vertex._index == 3:
            self._pos = (self._pos[0], self._pos[1])
            self._size = (vertex._pos[0], vertex._pos[1])
            vertex._pos = (self._size[0], self._size[1])
        
        # Make sure interface is not inverted
        self._size = (max(self._size[0], 64.0), max(self._size[1], 64.0))
        
        # Limit position
        self._corners[0]._pos = (0.0,            0.0)
        self._corners[1]._pos = (self._size[0],  0.0)
        self._corners[2]._pos = (0.0,            self._size[1])
        self._corners[3]._pos = (self._size[0],  self._size[1])
        
        # Set correct median vertex position
        self._medianVertex._pos = (self._size[0] * self._medianRatio + 1, -8.0)
        self._heightVertex._pos = (-8.0, self._size[1] * self._heightRatio + 1)
    
    # Change median depending on vertex
    def adaptMedian(self, context, vertex):
        
        self._medianRatio = min(max(vertex._pos[0] / self._size[0], 0.0), 1.0)
        
        # Set correct median vertex position
        vertex._pos = (self._size[0] * self._medianRatio + 1, -8.0)
    
    # Change height depending on vertex
    def adaptHeight(self, context, vertex):
        
        self._heightRatio = min(max(vertex._pos[1] / self._size[1], 0.0), 1.0)
        
        # Set correct median vertex position
        vertex._pos = (-8.0, self._size[1] * self._heightRatio + 1)
        
    
    # Computes actual position on screen with anchors
    def coord(self, context, scale):
        
        # Get base offset
        pos = super().coord()
        
        # Get screen values
        screenX = context.region.width / scale
        screenY = context.region.height / scale
        offsetX = screenX * self._anchor[0]
        offsetY = screenY * self._anchor[1]
        
        # Compute actual corners from interface coords
        l = pos[0] + offsetX - self._size[0] * self._anchor[0]
        r = pos[1] + offsetY - self._size[1] * self._anchor[1]
        
        # Clamp to not go outside the screen
        x = max( 0.0, min(screenX - self._size[0], l))
        y = max( 0.0, min(screenY - self._size[1], r))
        
        return (x, y)
    
    
    @Util.Overrides(Symbols.Rectangle)
    def store(self, context, buffer):
        
        buffer.write("width", self._medianRatio)
        buffer.write("height", self._heightRatio)
        buffer.write("background", self._background)
        
        sub = buffer.sub("median")
        self._median.store(context, sub)
        
        super().store(context, buffer)
    
    @Util.Overrides(Symbols.Rectangle)
    def load(self, context, buffer):
        
        self._medianRatio = buffer.read("width", float, 0.5)
        self._heightRatio = buffer.read("height", float, 0.5)
        self._background = buffer.read("background", str, "")
        if self._background and self._background in bpy.data.images:
            self._image = bpy.data.images[self._background]
            if self._image.has_data:
                self._image.update()
                
        sub = buffer.sub("median")
        self._median.load(context, sub)
        
        super().load(context, buffer)


    
####################################################################################

class Container(Symbols.Interactable):
    """Container Interface element, contains all the selector buttons"""
    
    # Currently building button
    _building = -1
    
    # Stored selectors
    _selectors = []
    
    # Stored selectors
    _default = (0.9, 0.7, 0.7, 0.9)
    
    # Constructor
    def __init__(self):
        super().__init__((0.0, 0.0))
        self._selectors = []
        
        
    # Gets building button from stored building index
    def getBuilding(self):
        
        # Get building if in range
        if 0 <= self._building and self._building < len(self._selectors):
            return (self._selectors[self._building])
        return None
    
    # Removes a selector
    def removeSelector(self, context, selector):
        
        # Finish building
        building = self.getBuilding()
        self._building = -1
        if building:
            building.finish(context)
        
        # Only remove if exists in this interface
        if selector in self._selectors:
            
            # Update all twin references
            index = self._selectors.index(selector)
            for entry in self._selectors:
                if entry._twin > index:
                    entry._twin = entry._twin - 1
            
            # Actualls remove selector
            self._selectors.remove(selector)
            self.removeChild(selector)
    
    # Toggles edit mode on or off
    def toggleEdit(self, context, active):
        
        # Toggle all selectors
        for selector in self._selectors:
            selector.toggleEdit(context, active)
    
    # Adds a vertex to a new button or current focus
    def addVertex(self, context, pos):
        
        x = pos[0] - self._pos[0]
        y = pos[1] - self._pos[1]
        
        # Cache building
        building  = self.getBuilding()
        if building and building._build:
            
            # Add vertex to current build
            building.addVertex(context, (x, y))
            
        else:
            
            # Create new selector
            building = Selectors.BoneSelector(Util.adaptToGrid((x, y), True))
            self._selectors.append(building)
            self.addChild(building)
            self._building = self._selectors.index(building)
            
            # Select on creation
            Util._selectedSelector = building
    
    
    @Util.Overrides(Symbols.Interactable)
    def draw(self, context, parent, scale):
        
        # Get interface information 
        if self._parent and self._parent._parent:
            size = self._parent._parent._size
            ratio = (self._parent._parent._medianRatio, self._parent._parent._heightRatio)
            origin = (parent[0] - self._parent._pos[0], parent[1] - self._parent._pos[1])
            center = (parent[0], parent[1] + self._pos[1])
            corner = (origin[0] + size[0], parent[1] + size[1])
            
            # Render grid       
            grid = context.scene.enableRigSelector.grid
            if grid > 0.0 and self._parent._parent._edit:
                
                # Computes amount of lines
                offset = (Util.roundTowards(size[0] * ratio[0], 0.5, grid), Util.roundTowards(size[1] * ratio[1], 0.5, grid))
                start = (center[0] - offset[0], center[1] - offset[1])
                end = (start[0] + size[0], start[1] + size[1])
                
                # Prevent overdraw
                if start[0] < origin[0]:
                    start = (start[0] + grid, start[1])
                if start[1] < origin[1]:
                    start = (start[0], start[1] + grid)
                if end[0] > origin[0] + size[0]:
                    end = (end[0] - grid, end[1])
                if end[1] > origin[1] + size[1]:
                    end = (end[0], end[1] - grid)
                
                hor = [[(px * scale, origin[1] * scale), (px * scale, corner[1] * scale)] for px in Util.frange(start[0], end[0], grid)]
                ver = [[(origin[0] * scale, py * scale), (corner[0] * scale, py * scale)] for py in Util.frange(start[1], end[1], grid)]
                vertices = [vertex for pair in (hor + ver) for vertex in pair]
                indices = [(2*i, 2*i + 1) for i in range(0, len(hor + ver))]

                shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)

                bgl.glEnable(bgl.GL_BLEND)
                shader.bind()
                shader.uniform_float("color", (0.0, 0.0, 0.0, 0.1))
                batch.draw(shader)
                bgl.glDisable(bgl.GL_BLEND)

                '''
                # Set GL options
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glLineWidth(1)
                bgl.glColor4f(0.0, 0.0, 0.0, 0.1)
                                
                # Render vertical lines
                for x in Util.frange(start[0], end[0], grid):
                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex2f(x * scale, origin[1] * scale)
                    bgl.glVertex2f(x * scale, corner[1] * scale)
                    bgl.glEnd()
                
                # Render horizontal lines   
                for y in Util.frange(start[1], end[1], grid):
                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex2f(origin[0] * scale, y * scale)
                    bgl.glVertex2f(corner[0] * scale, y * scale)
                    bgl.glEnd()
                '''
            
        super().draw(context, parent, scale)
    
    
    
    # Update visibility depending on whether any buttons are visible
    def updateVisibility(self, context):
                
        # Update all selector visibility
        active = False
        for selector in self._selectors:
            active = selector.updateVisibility(context) or active
        
        # Only draw median if any selectors are active
        self._visible = active or not self._selectors
        return self._visible
    

    @Util.Overrides(Symbols.Interactable)
    def store(self, context, buffer):
        
        for selector in self._selectors:
            sub = buffer.push("selectors")
            sub.write("class", type(selector).__name__)
            selector.store(context, sub)
        
        buffer.write("building", self._building)
        
        super().store(context, buffer)
    
    
    @Util.Overrides(Symbols.Interactable)
    def load(self, context, buffer):
        
        for selector in self._selectors:
            self.removeChild(selector)
        self._selectors = []
        
        while( True ):
            sub = buffer.pop("selectors")
            if sub:
                name = sub.read("class", str, "Selectors.Selector")
                Class = eval("Selectors." + name)
                if Class:
                    selector = Class((0, 0))
                    self._selectors.append(selector)
                    self.addChild(selector)
                    selector.load(context, sub)
                else:
                    buffer.error("selectors", "Class " + name + " not found.")
            else:
                break
        
        self._building = buffer.read("building", int, -1)
        
        super().load(context, buffer)        
