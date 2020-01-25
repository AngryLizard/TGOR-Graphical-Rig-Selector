import bpy

import gpu
import bgl
from gpu_extras.batch import batch_for_shader

from .Base import Symbols
from .Base import Util
from . import Elements

####################################################################################

class Selector(Symbols.Interactable):
    """Selector button element"""
    
    # Currently adding vertices
    _build = True
    
    # Currently moving vertices
    _edit = True
        
    # Twin selector in symmetry mode
    _twin = -1
    _mirror = False
    
    # Shape vertex positions (convex)
    _vertices = []
    _medians = []
    
    # Shape colour
    _default = (0.0, 0.0, 0.0, 1.0)
                
    # Constructor
    def __init__(self, pos, colour):
        super().__init__(pos)
        self._default = colour
        self._grid = True
        self._active = True
        self._mirror = False
        self._medians = []
        
        # Add first vertex
        vertex = Elements.Vertex((0.0, 0.0), 8.0, 0, self.adaptVertex)
        self._vertices = [vertex]
        self.addChild(vertex)
        
        # Create medians
        self.updateMedians()
    
    # Checks if this selector is linked to something
    def isLinked(self, context):
        return(False)
    
    # Checks if link is visible
    def isLinkVisible(self, context):
        return(True)
    
    # Check if link is selected
    def isLinkSelected(self, context):
        return(False)
    
    # Selection action triggered
    def selectLink(self, context):
        pass
    
    # Clear selection
    def deselectAll(self, context):
        pass
    
    # Update link to new option
    def updateLink(self, context):
        pass
    
    # Get link colour
    def getLinkColour(self, context):
        return((0.0, 0.0, 0.0, 1.0))
    
    # Gets twin from stored twin index
    def getTwin(self):
        
        # Get twin if in range
        if self._parent and 0 <= self._twin and self._twin < len(self._parent._selectors):
            return (self._parent._selectors[self._twin])
        return None
    
    @Util.Overrides(Symbols.Interactable)
    def isInside(self, context, pos):
        
        # Make sure there are enough vertices
        num = len(self._vertices)
        if num <= 2:
            return False
        
        # Get general direction
        dir = self.cross(self._vertices[0]._pos, self._vertices[1]._pos, self._vertices[2]._pos)
        for index in range(0, num):
            
            # Check if always on the same side
            cross = self.cross(self._vertices[index-1]._pos, self._vertices[index]._pos, pos)
            if cross * dir < 0.0:
                return False
        
        return True
    
    @Util.Overrides(Symbols.Interactable)
    def isGrabZone(self, context, pos):
        return self._edit
    
    
    @Util.Overrides(Symbols.Interactable)
    def draw(self, context, parent, scale):
                           
        # Compute position
        x = parent[0] + self._pos[0]
        y = parent[1] + self._pos[1]
        
        # Cache twin
        twin = self.getTwin()
        
        # Also link twin if mirrored
        selected = False
        if (Util._selectedSelector == self or (self._mirror and Util._selectedSelector == twin)):
            

            # Adapt link if changed
            if self._edit:
                selected = True
                self.updateLink(context)
        
        # Set alpha for selected state
        if self.isLinkSelected(context):
            alpha = 0.5
        else:
            alpha = 0.1
        
        # Get colour
        if self._build:
            colour = (1,1,1,0.5)
        else:
            
            # Make sure colour is set
            colour = self._default
            
            # Adapt link colour if available
            if self.isLinked(context):
                colour = self.getLinkColour(context)
        
        # Generate vertex data
        positions = []
        for vertex in self._vertices:
            positions.append((x + vertex._pos[0], y + vertex._pos[1]))
        
        # Generate settings
        border = (1.0, 1.0, 1.0, alpha) if selected else colour
        colour = (colour[0], colour[1], colour[2], colour[3] * alpha)

        # Generate vertex data
        positions = [(x + vertex._pos[0], y + vertex._pos[1]) for vertex in self._vertices]
        vertices = [(px * scale, py * scale) for px,py in positions]
        last = len(vertices)
        origin = (  sum([vx for vx, vy in vertices]) / last, 
                    sum([vy for vx, vy in vertices]) / last)
        vertices.append(origin)
        indices = [(i, (i+1)%last, last) for i in range(0, last)]
        edges = [(i, (i+1)%last) for i in range(0, last)]
        
        for mode, idx, col in [('TRIS', indices, colour), ('LINES', edges, border)]:

            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            batch = batch_for_shader(shader, mode, {"pos": vertices}, indices=idx)

            bgl.glEnable(bgl.GL_BLEND)
            shader.bind()
            shader.uniform_float("color", col)
            batch.draw(shader)
            bgl.glDisable(bgl.GL_BLEND)

        '''
        # Generate settings
        border = (1.0, 1.0, 1.0, 1.0) if selected else colour
        settings = [(bgl.GL_LINE_LOOP, border, 1.0), (bgl.GL_POLYGON, colour, alpha)]
        
        # Render box
        for mode, col, coeff in settings:
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glBegin(mode)
            bgl.glColor4f(col[0], col[1], col[2], col[3] * coeff)
            for x, y in positions:
                bgl.glVertex2f(x * scale, y * scale)
            bgl.glEnd()
        '''
            
        # Only draw vertices (children) when editing or building
        if self._edit:
            super().draw(context, parent, scale)
    
    
    @Util.Overrides(Symbols.Interactable)
    def clicked(self, context, pos, right, shift):
        
        # Finish other selector in progress
        if Util._selectedSelector:
            Util._selectedSelector.finish(context)
        
        # Select this selector
        Util._selectedSelector = self
        
        if self._build:
            
            # Finish build
            self.finish(context)
            
        else:
            
            if not shift:
                self.deselectAll(context)
            self.selectLink(context)
            
    
    @Util.Overrides(Symbols.Interactable)
    def dropped(self, context, pos):
        
        # Adapt to grid
        pos = Util.adaptToGrid(pos, self._grid)
        
        # Select this selector
        self.clicked(context, (0,0), False, False)
        
        # Finish building when moving vertices
        self.finish(context)
        
        # Move mirrored only vertically
        if self._mirror:
            self._pos = (0.0, self._pos[1])
        
        # Cache twin
        twin = self.getTwin()
        
        # Move twin
        if twin and self._parent:
            twin._pos = (-self._pos[0], self._pos[1])
        
        # Get bounds
        if self._parent:
            
            x = pos[0] + self._pos[0] + self._parent._pos[0] + self._parent._parent._pos[0]
            y = pos[1] + self._pos[1] + self._parent._pos[1] + self._parent._parent._pos[1]
            xc = self._parent._parent._parent._size[0]
            yc = self._parent._parent._parent._size[1]
                    
            # Delete if out of bounds
            if x < 0.0 or x >= xc or y < 0.0 or y >= yc:
                
                # Delete twin first
                if twin:
                    self._parent.removeSelector(context, twin)
                
                self._parent.removeSelector(context, self)
        
        # Update medians
        self.updateMedians()
            
    # Checks whether current setup is convex
    def isConvex(self):
        
        # Make sure there are enough vertices
        num = len(self._vertices)
        if num <= 2:
            return True
        
        # Get general direction
        dir = self.cross(self._vertices[0]._pos, self._vertices[1]._pos, self._vertices[2]._pos)
        for index in range(0, num):
            
            # Check if always on the same side
            cross = self.cross(self._vertices[index-2]._pos, self._vertices[index-1]._pos, self._vertices[index]._pos)
            if cross * dir < 0.0:
                return False
        
        return True
    
    # Update visibility depending on target bone visibility
    def updateVisibility(self, context):
        
        # Assume visibility
        self._visible = True
        
        # See if link is visible (always visible in edit mode)
        if self.isLinked(context) and not self._edit:
            if(not self.isLinkVisible(context)):
                self._visible = False
                
        return self._visible
    
    # Finishes building
    def finish(self, context):
        
        if self._build and self._parent:
            self._build = False
            
            # Cache twin
            twin = self.getTwin()
        
            # Remove if unfinished
            if len(self._vertices) < 3:
                
                # Remove twin too
                if twin:
                    self._parent.removeSelector(context, twin)
                    
                self._parent.removeSelector(context, self)
                
                    
            else:
                
                # Create twi if symmetry mode is on
                symmetry = context.scene.enableRigSelector.symmetry
                if symmetry and self._parent:
                    
                    # Create twin for every vertex
                    for vertex in self._vertices:
                        x = self._parent._pos[0] - self._pos[0] - vertex._pos[0]
                        y = self._parent._pos[1] + self._pos[1] + vertex._pos[1]
                        self._parent.addVertex(context, (x, y))
                    
                    # Cache building
                    building  = self._parent.getBuilding()
                    
                    # Finish twin
                    if building:
                        self._twin = self._parent._building
                        building._build = False
                        twin = self.getTwin()
                        twin._twin = self._parent._selectors.index(self)
        
            # Adapt link
            if self._edit:
                self.updateLink(context)
                
                # Adapt twin too
                if twin:
                    twin.updateLink(context)
        
            # Update medians
            self.updateMedians()
    
    # Change size depending on vertex
    def adaptVertex(self, context, vertex):
        
        # Correct mirror
        self.correctMirror(context, vertex)
        
        # Make sure selector is properly connected
        num = len(self._vertices)
        if self._parent:
            
            # Cache twin
            twin = self.getTwin()
            
            x = vertex._pos[0] + self._pos[0] + self._parent._pos[0] + self._parent._parent._pos[0]
            y = vertex._pos[1] + self._pos[1] + self._parent._pos[1] + self._parent._parent._pos[1]
            xc = self._parent._parent._parent._size[0]
            yc = self._parent._parent._parent._size[1]
                    
            # Delete if out of bounds, switching while building and not already mirrored
            isMirrored = self._mirror and (vertex._index == 0 or vertex._index == num-1)
            isSwitchingMedian = ((self._pos[0] + vertex._pos[0]) * self._pos[0]) < 0
            isOutOfBounds = x < 0.0 or x >= xc or y < 0.0 or y >= yc
            if (isOutOfBounds and not isMirrored) or (self._build and isSwitchingMedian):
                            
                # Remove if triangle or less,
                if num <= 3:
                    
                    # Remove twin too
                    if twin:
                        self._parent.removeSelector(context, twin)
                        
                    self._parent.removeSelector(context, self)
                else:
                    
                    # Remove vertex from selector
                    self._vertices.remove(vertex)
                    self.removeChild(vertex)
                    
                    # Update indices
                    num = len(self._vertices)
                    for i in range(vertex._index, num):
                        self._vertices[i]._index = i
                    
                    # Create mirror if switch happened
                    if self._build and isSwitchingMedian:
                        
                        # Set to mirror mode
                        if self.connectWithMedian(context):
                            self._mirror = True
                        
                        # Close polygons off and generate twin (if successful)
                        self.finish(context)
                        
                        # Set twin to mirror too
                        if twin:
                            twin._mirror = self._mirror
                        
                    elif twin:
                    
                        # Remove from twin
                        mirror = twin._vertices[vertex._index]
                        twin._vertices.remove(mirror)
                        twin.removeChild(mirror)
                        
                        # Update indices
                        for i in range(0, num):
                            twin._vertices[i]._index = i
                    
                        # Update medians
                        twin.updateMedians()
                            
            else:
            
                # Move always allowed if triangle or less
                if num >= 4:
                    
                    # Make sure this selector stays convex
                    self.correctConvex(context, vertex)
                                    
                # Morph twin
                if twin:
                    
                    # Get twin vertex
                    index = vertex._index
                    mirror = twin._vertices[index]
                    if mirror:
                        
                        # Move twin vertex
                        x = self._pos[0] + vertex._pos[0] + twin._pos[0]
                        y = self._pos[1] + vertex._pos[1] - twin._pos[1]
                        mirror._pos = (-x, y)
                    
                    # Update twin medians
                    twin.updateMedians()
        
        
        # Select this selector (and finish it if building)
        self.clicked(context, (0,0), False, False)
                    
        # Update medians
        self.updateMedians()
    
    # Corrects head and tail for mirrored mode
    def correctMirror(self, context, vertex):
        
        # Move only on median if mirror
        if self._mirror :
            if (vertex == self._vertices[0]) or (vertex == self._vertices[-1]):
                vertex._pos = (0.0, vertex._pos[1])
    
    # Corrects a vertex that makes this selector out of bounds
    def correctConvex(self, context, vertex):
        
        if not self.isConvex():
            
            # Get next and previous vertices
            num = len(self._vertices)
            snd = self._vertices[vertex._index - 1]
            trd = self._vertices[(vertex._index + 1) % num]
            
            # If not convex anymore, move to average
            x = (snd._pos[0] + trd._pos[0]) / 2
            y = (snd._pos[1] + trd._pos[1]) / 2
            vertex._pos = (x, y)
            self.correctMirror(context, vertex)
    
    # Toggles edit mode on or off
    def toggleEdit(self, context, active):
        
        # Toggle all vertices
        for vertex in self._vertices:
            vertex._active = active
        
        # Toggle edit mode
        self._edit = active
        self.finish(context)
        
        # Update medians
        self.updateMedians()
    
    
    # Adds a vertex to a new button or current focus
    def addVertex(self, context, pos):    
        
        # Adapt to grid
        pos = Util.adaptToGrid(pos, self._grid)
        
        # See if added vertex is on other side of median
        symmetry = context.scene.enableRigSelector.symmetry
        if symmetry and pos[0] * self._pos[0] < 0.0:
            
            # Can't mirror a segment
            if len(self._vertices) < 2:
                return
                    
            # Set to mirror mode
            if self.connectWithMedian(context):
                self._mirror = True
            
            # Close polygons off and generate twin (if successful)
            self.finish(context)
            
            # Cache twin
            twin = self.getTwin()
            
            # Set twin to mirror too
            if twin:
                twin._mirror = self._mirror
                
        else:
            
            # Compute position and index from input
            x = pos[0] - self._pos[0]
            y = pos[1] - self._pos[1]
                        
            i = len(self._vertices)
            
            # Check if valid
            if i >= 3:
                
                # Get polygon direction, first edge and last edge, check if polygon is convex (needed for hit-check)
                dir = self.cross(self._vertices[0]._pos, self._vertices[1]._pos, self._vertices[2]._pos)
                fst = self.cross((x, y), self._vertices[0]._pos, self._vertices[1]._pos)
                lst = self.cross(self._vertices[-2]._pos, self._vertices[-1]._pos, (x, y))
                
                if lst * dir < 0 or fst * dir < 0:
                    self.finish(context)
                    return
            
            # Add new vertex
            vertex = Elements.Vertex((x, y), 8.0, i, self.adaptVertex)
            self._vertices.append(vertex)
            self.addChild(vertex)
        
        # Update medians
        self.updateMedians()
    
    # Connects this selector with the median if possible
    def connectWithMedian(self, context):
    
        # Compute heights
        first = self._vertices[0]._pos[1]
        last = self._vertices[-1]._pos[1]
        top = (-self._pos[0], first)
        bot = (-self._pos[0], last)
                
        # Identify whether the resulting shape is still convex
        fst = self.cross(self._vertices[-2]._pos, self._vertices[-1]._pos, bot)
        snd = self.cross(self._vertices[-1]._pos, bot, top)
        trd = self.cross(bot, top, self._vertices[0]._pos)
        frt = self.cross(top, self._vertices[0]._pos, self._vertices[1]._pos)
        
        if fst * snd < 0 or snd * trd < 0 or trd * frt < 0:
            return False
        
        
        # Set X shift
        shift = self._pos[0]
        
        # Move all vertices to counteract moving selector to the median
        for vertex in self._vertices:
            vertex._pos = (vertex._pos[0] + shift , vertex._pos[1])
            vertex._index = vertex._index + 1
        
        # Move position to the center
        self._pos = (0.0, self._pos[1])
        
        # Insert head vertex at median
        head = Elements.Vertex((0.0, first), 8.0, 0, self.adaptVertex)
        self._vertices.insert(0, head)
        self.addChild(head)
        
        # Insert tail vertex at median
        tail = Elements.Vertex((0.0, last), 8.0, len(self._vertices), self.adaptVertex)
        self._vertices.append(tail)
        self.addChild(tail)
        
        return True                
    
    
    # Computes 2D cross product (b - a, c - a)
    def cross(self, a, b, c):
        diff = (b[0] - a[0], b[1] - a[1])
        rel = (c[0] - a[0], c[1] - a[1])
        return diff[0] * rel[1] - diff[1] * rel[0]
    
    
    # Update median array
    def updateMedians(self):
        
        # Remove medians if too many
        num = len(self._vertices)
        while len(self._medians) > num:
            median = self._medians.pop()
            self.removeChild(median)
        
        # Add medians if too few
        while len(self._medians) < num:
            median = Elements.Vertex((0, 0), 4.0, -1, self.adaptMedian)
            self._medians.append(median)
            self.addChild(median)
        
        # Update all medians
        for i in range(0, num):
            
            # Update index
            median = self._medians[i]
            median._index = i
            
            # Update position
            before = self._vertices[i - 1]
            after = self._vertices[i]
            median._pos = ((before._pos[0] + after._pos[0]) / 2, (before._pos[1] + after._pos[1]) / 2)
            median._active = median._visible = self._edit
    
    
    # Add new vertex if median moves
    def adaptMedian(self, context, median):
                
        # Create new vertex
        vertex = Elements.Vertex(median._pos, 8.0, -1, self.adaptVertex)
        self._vertices.insert(median._index, vertex)
        self.addChild(vertex)
        
        # Update all vertices
        num = len(self._vertices)
        for i in range(median._index, num):
            self._vertices[i]._index = i
        
        # Make sure this selector stays convex
        self.correctConvex(context, vertex)
        
        # Cache twin
        twin = self.getTwin()
        
        # Morph twin
        if twin and self._parent:
            
            # Compute twin vertex position
            x = self._pos[0] + vertex._pos[0] + twin._pos[0]
            y = self._pos[1] + vertex._pos[1] - twin._pos[1]
                
            # Create new twin vertex
            mirror = Elements.Vertex((-x, y), 8.0, -1, twin.adaptVertex)
            twin._vertices.insert(median._index, mirror)
            twin.addChild(mirror)
            
            # Update all vertices
            for i in range(median._index, num):
                twin._vertices[i]._index = i
                
            # Update twin medians
            twin.updateMedians()
        
        # Update medians
        self.updateMedians()
    
        # Finish if building
        self.finish(context)
    
        
    @Util.Overrides(Symbols.Interactable)
    def store(self, context, buffer):
                
        buffer.write("build", self._build)
        buffer.write("mirror", self._mirror)
        
        for vertex in self._vertices:
            sub = buffer.push("vertices")
            vertex.store(context, sub)
        
        buffer.write("twin", self._twin)
        
        super().store(context, buffer)
    
    @Util.Overrides(Symbols.Interactable)
    def load(self, context, buffer):
        
        self._edit = False
        
        self._build = buffer.read("build", bool, False)
        self._mirror = buffer.read("mirror", bool, False)
        
        for vertex in self._vertices:
            self.removeChild(vertex)
        self._vertices = []
        
        while( True ):
            sub = buffer.pop("vertices")
            if sub:
                vertex = Elements.Vertex((0, 0), 8.0, -1, self.adaptVertex)
                self._vertices.append(vertex)
                self.addChild(vertex)
                vertex.load(context, sub)
                vertex._active = self._edit
            else:
                break
                
        if not self.isConvex():
            buffer.error("vertices", 'Shape not convex')
        
        self._twin = buffer.read("twin", int, -1)
        self.updateMedians()
        
        super().load(context, buffer)
        


####################################################################################

class BoneSelector(Selector):
    """Bone selector button element"""
    
    # Reference names
    _linked = False
    _object = ""
    _bone = ""
    
    # Constructor
    def __init__(self, pos):
        super().__init__(pos, (0.9, 0.7, 0.7, 0.9))

    
    @Util.Overrides(Selector)
    def isLinked(self, context):
        return(self._linked)
    
    
    @Util.Overrides(Selector)
    def isLinkVisible(self, context):
        
        obj = self.getLinkedObject(context)
        if obj:
            return obj.visible_get()#is_visible(context.scene)
        
        bone = self.getLinkedBone(context)
        if bone: 
            armature = context.scene.objects.get(self._object)
            return (not bone.bone.hide and self.checkLayer(armature, bone.bone))
        
        return(False)
    
    # Checks if bone is visible given its layers 
    # (TODO: Find official way to check if bone is visible, context.visible_pose_bones only works for active object)
    def checkLayer(self, armature, bone):
        
        # Check if there are any layers where both bone and armature have true
        for layer in range(0, 32):
            if bone.layers[layer]:
                if armature.data.layers[layer]:
                    return True
        return False
    
    @Util.Overrides(Selector)
    def isLinkSelected(self, context):
        
        obj = self.getLinkedObject(context)
        if obj:
            return obj.select
        
        bone = self.getLinkedBone(context)
        if bone: 
            return (bone.bone.select)
        
        return (False)
    
    
    @Util.Overrides(Selector)
    def selectLink(self, context):
        
        # Find linked object
        obj = context.scene.objects.get(self._object)
        
        # Check if object is visible
        if obj and obj.visible_get(): #is_visible(context.scene):
            
            if obj.type == 'ARMATURE' and self._bone:
                
                # Set armature active
                context.view_layer.objects.active = obj
                
                # Set pose mode
                bpy.ops.object.mode_set(mode='POSE')
                
                # Get linked bone
                bone = self.getLinkedBone(context)
                if bone:
                    
                    # Select bone
                    bone.bone.select = not bone.bone.select
                    
                    # Set bone active
                    if bone.bone.select:
                        obj.select_set(True)
                        obj.data.bones.active = bone.bone
            else:
                
                # Select object
                obj.select_set(not obj.select_get())
                
                # Set object active
                if obj.select_get():
                   context.view_layer.objects.active = obj
    
    
    @Util.Overrides(Selector)
    def deselectAll(self, context):
        
        # Deselect all pose bones
        if not context.selected_objects is None :
            for obj in context.selected_objects :
                obj.select_set(False)
        
        # Deselect all pose bones
        if not context.selected_pose_bones is None :
            for bone in context.selected_pose_bones :
                bone.bone.select = False
            
    
    @Util.Overrides(Selector)
    def updateLink(self, context):
                
        # Find armature to link
        obj = context.active_object
        if obj:
            if obj.type == 'ARMATURE' and obj.mode == 'POSE':
                
                # Find bone to link
                bone = context.active_pose_bone
                if bone and bone.bone.select and bone.name in obj.pose.bones:
                    
                    # Set link status
                    self._linked = True
                    self._object = obj.name
                    self._bone = bone.name
                    
                    # Also link twin if mirrored
                    twin = self.getTwin()
                    if self._mirror and twin:
                        twin._linked = True
                        twin._object = obj.name
                        twin._bone = bone.name
            else:
                self._linked = True
                self._object = obj.name
                self._bone = ""
                
                    
    @Util.Overrides(Selector)
    def getLinkColour(self, context):
        
        # Get linked bone
        bone = self.getLinkedBone(context)
        if bone and bone.bone_group:
            
            # set to group colour
            set = bone.bone_group.colors.normal
            return (set[0], set[1], set[2], 0.9)
        
        # Use default colour if no bone was found
        return self._default
            
    
    # Gets linked to bone
    def getLinkedBone(self, context):
        
        if self._linked:
            
            # Find armature
            armature = context.scene.objects.get(self._object)
            if armature and armature.type == 'ARMATURE' and armature.mode == 'POSE' and self._bone:
                
                # Find bone
                bone = armature.pose.bones.get(self._bone)
                if bone:
                    return bone
        return None
    
    # Gets linked to object
    def getLinkedObject(self, context):
        
        if self._linked:
            
            # Find object and make sure it's not linked to a bone
            obj = context.scene.objects.get(self._object)
            if obj and not (obj.type == 'ARMATURE' and obj.mode == 'POSE' and self._bone):
                return obj
        return None
    
    @Util.Overrides(Symbols.Interactable)
    def store(self, context, buffer):
        
        buffer.write("linked", self._linked)
        buffer.write("armature", self._object)
        buffer.write("bone", self._bone)
        
        super().store(context, buffer)
    
    @Util.Overrides(Symbols.Interactable)
    def load(self, context, buffer):
        
        self._linked = buffer.read("linked", bool, False)
        self._object = buffer.read("armature", str, "")
        self._bone = buffer.read("bone", str, "")
        
        super().load(context, buffer)


####################################################################################

class LayerSelector(Selector):
    """Layer selector button element"""
    
    # Reference names
    _layer = -1
    _armature = ""
    
    # Constructor
    def __init__(self, pos, layer = 0):
        super().__init__(pos, (0.9, 0.9, 0.7, 0.9))
        self._layer = layer
    
    @Util.Overrides(Selector)
    def isLinked(self, context):
        return(True)
    
    
    @Util.Overrides(Selector)
    def isLinkVisible(self, context):
        # Find linked armature
        armature = context.scene.objects.get(self._armature)
        
        # Check if armature is visible
        if armature and armature.visible_get():#is_visible(context.scene):
            return (True)
        
        return(False)
    
    
    @Util.Overrides(Selector)
    def isLinkSelected(self, context):
        
        # Find armature
        armature = self.getLinked(context)
        if armature:
            return (armature.data.layers[self._layer])
        return (False)
    
    
    @Util.Overrides(Selector)
    def selectLink(self, context):
    
        # Find armature
        armature = self.getLinked(context)
        if armature:
            
            # Do not change state in edit mode
            if not self._edit:
                
                # Toggle layer visibility
                armature.data.layers[self._layer] = not armature.data.layers[self._layer]
            
            # Set armature active in edit mode only
            if self._edit:
                
                # Deselect all pose bones
                if context.selected_objects :
                    for obj in context.selected_objects :
                        obj.select_set(False)
                
                context.view_layer.objects.active = armature
                armature.select_set(True)
    
    
    @Util.Overrides(Selector)
    def deselectAll(self, context):
        pass
            
    
    @Util.Overrides(Selector)
    def updateLink(self, context):
        
        # Check if selected object is an armature
        armature = context.active_object
        if armature and armature.type == 'ARMATURE':
            
            # Link with armature
            self._armature = armature.name
                    
    @Util.Overrides(Selector)
    def getLinkColour(self, context):
        return self._default
        
    # Gets linked to armature
    def getLinked(self, context):
        
        # Find armature
        armature = context.scene.objects.get(self._armature)
        if armature and armature.type == 'ARMATURE' :
            return armature
        
        return None
    
    @Util.Overrides(Selector)
    def store(self, context, buffer):
        
        buffer.write("layer", self._layer)
        buffer.write("armature", self._armature)
        
        super().store(context, buffer)
    
    @Util.Overrides(Selector)
    def load(self, context, buffer):
        
        self._layer = buffer.read("layer", int, 0)
        self._armature = buffer.read("armature", str, "")
        super().load(context, buffer)