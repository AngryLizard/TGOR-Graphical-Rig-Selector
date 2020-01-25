import gpu
import bgl
from gpu_extras.batch import batch_for_shader

from . import Base
from . import Util
       

####################################################################################

class Interactable(Base.Writeable):
    """Interactable Interface element"""
    
    # Position relative to anchor
    _pos = (0.0, 0.0)
    
    # Gets rendered
    _visible = True
    
    # Gets affected by grid
    _grid = False
    
    # Is input active
    _active = False
    
    # Child elements
    _children = []
    
    # Parent element
    _parent = None
    
    # Grab offset
    _grab = (0.0, 0.0)
    _isGrabbing = False
        
    # Constructor
    def __init__(self, pos):
        self._pos = pos
        self._children = []
    
    # Defines, whether a position is inside the grab zone
    def isGrabZone(self, context, pos):
        return False
    
    # Defines, whether a position is inside this element
    def isInside(self, context, pos):
        return False
    
    # Defines click behaviour
    def clicked(self, context, pos, right, shift):
        pass
    
    # Defines dropped behaviour
    def dropped(self, context, pos):
        pass
    
    # add child
    def addChild(self, child):
    
        # Ensure a child only has one parent
        if not child._parent is None:
            child.parent.removeChild(child)
            
        # Ensure child isn't already there
        if child not in self._children:
            self._children.append(child)
        
        # Register parent
        child._parent = self
        return child
        
    # remove child
    def removeChild(self, child):
        
        # Make sure child is in the list
        if child in self._children:
            self._children.remove(child)
        
        # Reset parent
        child._parent = None
        return child
    
    
    # Handles mouse input, returns true if activated
    def press(self, context, pos, right, shift):
        
        # Get mouse offset
        x = pos[0] - self._pos[0]
        y = pos[1] - self._pos[1]
        
        # Check if inside children
        for child in self._children:
            if child.press(context, (x, y), right, shift):
                return True
                    
        # Check if inside
        if self._active and self._visible and self.isInside(context, (x, y)):
                                
            # Check if currently grabbing
            if self.isGrabZone(context, pos):
                self._isGrabbing = True
                self._grab = (x, y)
            else:
                self.clicked(context, (x, y), right, shift)
            
            return True
    
        return False
    
    # Handles mouse dragging
    def hold(self, context, pos):
        
        if self._isGrabbing:
        
            # Move element with mouse
            x = pos[0] - self._grab[0]
            y = pos[1] - self._grab[1]
                        
            self._pos = Util.adaptToGrid((x, y), self._grid)
            
        else:
            # Get mouse offset
            x = pos[0] - self._pos[0]
            y = pos[1] - self._pos[1]
            
            # Hold children
            for child in self._children:
                child.hold(context, (x, y))
    
    
    # Handles mouse dropping
    def drop(self, context, pos):
        
        # Get mouse offset
        x = pos[0] - self._pos[0]
        y = pos[1] - self._pos[1]
        
        # Call dropped event    
        if self._isGrabbing:
            self.dropped(context, (x, y))
    
        # Drop no matter if currently dragging or not
        self._isGrabbing = False
        self._grab = (0.0, 0.0)
        
         # Drop children
        for child in self._children:
            child.drop(context, (x, y))
        
        
    # Draw this element
    def draw(self, context, parent, scale):
                
        # Compute offset position
        x = parent[0] + self._pos[0]
        y = parent[1] + self._pos[1]
        
        # Draw all children
        for child in self._children:
            
            # Abort if not visible
            if child._visible:
                child.draw(context, (x, y), scale)
        
    @Util.Overrides(Base.Writeable)
    def store(self, context, buffer):
        buffer.write("pos", self._pos)
        buffer.write("visible", self._visible)
        buffer.write("active", self._active)
    
    @Util.Overrides(Base.Writeable)
    def load(self, context, buffer):
        _children = []
        _parent = None
        
        self._pos = buffer.read("pos", list, (0,0))
        if not len(self._pos) == 2:
            buffer.error("pos", "Wrong tuple dimensions")
        
        self._visible = buffer.read("visible", bool, True)
        self._active = buffer.read("active", bool, False)


####################################################################################

class Rectangle(Interactable):
    """Rectangle element"""
    
    # Width and height of box
    _size = (0.0, 0.0)
    
    # Background image if loaded
    _image = None
    
    # Border colour or none for no border
    _border = None
    
    # Box colour
    _colour = (0.0, 0.0, 0.0, 1.0)
    
    # Constructor
    def __init__(self, pos, size):
        super().__init__(pos)
        self._size = size
    
    
    @Util.Overrides(Interactable)
    def isInside(self, context, pos):
        return 0.0 <= pos[0] and pos[0] < self._size[0] and 0.0 <= pos[1] and pos[1] < self._size[1]
    
    @Util.Overrides(Interactable)
    def draw(self, context, parent, scale):
                
        # Compute actual corners from interface coords
        xo = parent[0] + self._pos[0]
        yo = parent[1] + self._pos[1]
        xc = xo + self._size[0]
        yc = yo + self._size[1]
        
        # Render image if available
        if self._image and self._image.has_data:
            
            vertex_shader = '''

                uniform mat4 ModelViewProjectionMatrix;

                in vec2 texCoord;
                in vec2 pos;
                out vec2 texCoord_interp;

                void main()
                {
                gl_Position = ModelViewProjectionMatrix * vec4(pos.xy, 0.0f, 1.0f);
                gl_Position.z = 1.0;
                texCoord_interp = texCoord;
                }

            '''
            fragment_shader = '''
                in vec2 texCoord_interp;
                out vec4 fragColor;

                uniform float alpha;
                uniform sampler2D image;

                void main()
                {
                vec4 c = texture(image, texCoord_interp);
                c.w = c.w * alpha;
                fragColor = c;
                }

            '''
            shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
            batch = batch_for_shader(
                shader, 'TRI_FAN',
                {
                    "pos": ((xo * scale, yo * scale), (xc * scale, yo * scale),
                            (xc * scale, yc * scale), (xo * scale, yc * scale)),
                    "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
                },
            )

            if self._image.gl_load():
                raise Exception()

            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, self._image.bindcode)

            bgl.glEnable(bgl.GL_BLEND)
            shader.bind()
            shader.uniform_int("image", 0)
            shader.uniform_float("alpha", self._colour[3])
            batch.draw(shader)
            bgl.glDisable(bgl.GL_BLEND)

        else:

            # Render box
            vertices = ((xo * scale, yo * scale), (xc * scale, yo * scale),
                        (xo * scale, yc * scale), (xc * scale, yc * scale))

            indices = ((0, 1, 2), (2, 1, 3))

            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

            bgl.glEnable(bgl.GL_BLEND)
            shader.bind()
            shader.uniform_float("color", self._colour)
            batch.draw(shader)
            bgl.glDisable(bgl.GL_BLEND)


        # Render border
        if self._border:

            vertices = (((xo - 10) * scale, (yo - 10) * scale), ((xc + 10) * scale, (yo - 10) * scale),
                        ((xo - 10) * scale, (yc + 10) * scale), ((xc + 10) * scale, (yc + 10) * scale))

            indices = ((0, 1), (1, 3), (3, 2), (2, 0))

            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)

            bgl.glEnable(bgl.GL_BLEND)
            shader.bind()
            shader.uniform_float("color", self._border)
            batch.draw(shader)
            bgl.glDisable(bgl.GL_BLEND)


        '''
        # Generate box data
        positions = [[xo, yo], [xo, yc], [xc, yc], [xc, yo]]
        settings = [bgl.GL_QUADS, bgl.GL_LINE_LOOP]
                
        # Render image if available
        if self._image and self._image.has_data:
            
            self._image.gl_load(bgl.GL_NEAREST, bgl.GL_NEAREST)
            bgl.glColor4f(1.0, 1.0, 1.0, self._colour[3])
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, self._image.bindcode[0])
            bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
            
            bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)
            bgl.glEnable(bgl.GL_TEXTURE_2D)
            bgl.glEnable(bgl.GL_BLEND)

            bgl.glBegin(bgl.GL_QUADS)
            bgl.glTexCoord2f(0,0)
            bgl.glVertex2f(xo * scale, yo * scale)
            bgl.glTexCoord2f(0,1)
            bgl.glVertex2f(xo * scale, yc * scale)
            bgl.glTexCoord2f(1,1)
            bgl.glVertex2f(xc * scale, yc * scale)
            bgl.glTexCoord2f(1,0)
            bgl.glVertex2f(xc * scale, yo * scale)
            bgl.glEnd()
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_TEXTURE_2D)
            
        else:
        
            # Render box
            for mode in settings:
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glBegin(mode)
                bgl.glColor4f(self._colour[0], self._colour[1], self._colour[2], self._colour[3])
                for x, y in positions:
                    bgl.glVertex2f(x * scale, y * scale)
                bgl.glEnd()
            
        
        # Render border
        if self._border:
            positions = [[xo - 10, yo - 10], [xo - 10, yc + 10], [xc + 10, yc + 10], [xc + 10, yo - 10]]
        
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glBegin(bgl.GL_LINE_LOOP)
            bgl.glColor4f(self._border[0], self._border[1], self._border[2], self._border[3])
            for x, y in positions:
                bgl.glVertex2f(x * scale, y * scale)
            bgl.glEnd()
        '''
        
        super().draw(context, parent, scale)
        
    @Util.Overrides(Interactable)
    def store(self, context, buffer):
        
        buffer.write("size", self._size)
        
        super().store(context, buffer)
    
    @Util.Overrides(Interactable)
    def load(self, context, buffer):
        
        self._size = buffer.read("size", list, (0,0))
        if not len(self._size) == 2:
            buffer.error("size", "Wrong tuple dimensions")
            
        super().load(context, buffer)
                 
####################################################################################

class Circle(Interactable):
    """Rectangle element"""
    
    # Width and height of box
    _radius = 0.0
    
    # Circle colour
    _colour = (0.0, 0.0, 0.0, 1.0)
    
    # Constructor
    def __init__(self, pos, radius):
        super().__init__(pos)
        self._radius = radius
        
    @Util.Overrides(Interactable)
    def isInside(self, context, pos):
        # Get scale setting
        scaleUI = context.scene.enableRigSelector.scaleUI
        
        # Check if inside radius
        radius = self._radius * scaleUI
        square = (pos[0]*pos[0] + pos[1]*pos[1])
        return square < radius * radius
    
    @Util.Overrides(Interactable)
    def draw(self, context, parent, scale):
        
        # Get scale setting
        scaleUI = context.scene.enableRigSelector.scaleUI
        
        # Compute actual corners from interface coords (draw diamond shape)
        x = parent[0] + self._pos[0]
        xo = x - self._radius * scaleUI
        xc = x + self._radius * scaleUI
        
        y = parent[1] + self._pos[1]
        yo = y - self._radius * scaleUI
        yc = y + self._radius * scaleUI
        
        # Generate diamond data
        vertices = ((xo * scale, yo * scale), (xc * scale, yo * scale),
                    (xo * scale, yc * scale), (xc * scale, yc * scale))

        indices = ((0, 1, 2), (2, 1, 3))

        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

        bgl.glEnable(bgl.GL_BLEND)
        shader.bind()
        shader.uniform_float("color", self._colour)
        batch.draw(shader)
        bgl.glDisable(bgl.GL_BLEND)

        '''
        # Generate diamond data
        positions = [[x0, y], [x, y0], [x1, y], [x, y1]]
        settings = [bgl.GL_QUADS, bgl.GL_LINE_LOOP]
        
        colour = self._colour
        
        # Render box
        for mode in settings:
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glBegin(mode)
            bgl.glColor4f(colour[0], colour[1], colour[2], colour[3])
            for x, y in positions:
                bgl.glVertex2f(x * scale, y * scale)
            bgl.glEnd()
        '''
            
        super().draw(context, parent, scale)
        
    @Util.Overrides(Interactable)
    def store(self, context, buffer):
        
        buffer.write("radius", self._radius)
        
        super().store(context, buffer)
    
    @Util.Overrides(Interactable)
    def load(self, context, buffer):
        
        self._radius = buffer.read("radius", float, 0.0)
        if self._radius < 0.0:
            buffer.error("radius", "Negative radius")
        
        super().load(context, buffer)