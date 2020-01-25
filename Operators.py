
import bpy
import json

from bpy.types import Operator

from .Widgets.Base import Util
from .Widgets import Selectors
from .Widgets import Surfaces
from .Widgets.Base import Base

####################################################################################


# Main operator class
class TGOR_OT_RigSelectorModal(Operator):
    """Handle interface with mouse events"""
    bl_idname = "view3d.rig_selector"
    bl_label = "Rig Selector Modal Operator"
    
    # Currently active interface
    _active = None
    
    # Current draw handle
    _drawHandle = None
    
        
    # Destroy all loaded interfaces
    @staticmethod
    def destroy(context):
        
        # Disable drawing
        TGOR_OT_RigSelectorModal.toggleEnabled(context, False)
        
        # Clear interfaces
        Util._interfaces.clear()
        
        # Clear selection
        Util._selectedSelector = None
        Util._selectedInterface = None
    
    # Builds interfaces
    @staticmethod
    def build(context):
        
        # Clear interfaces
        Util._interfaces = []
    
    @staticmethod
    def autostore(dummy):
        
        if bpy.context.scene.enableRigSelector.autosave:
            TGOR_OT_RigSelectorModal.storeInterfaces(bpy.context)
    
    @staticmethod
    def toggleEnabled(context, active):
                
        # refresh screen
        if context.area:
            context.area.tag_redraw()  
        
        if active:
                        
            # Set draw handler
            if TGOR_OT_RigSelectorModal._drawHandle is None:
                
                # Add drawing handler
                TGOR_OT_RigSelectorModal._drawHandle = bpy.types.SpaceView3D.draw_handler_add(TGOR_OT_RigSelectorModal.render, (context,), 'WINDOW', 'POST_PIXEL')
                
                # Add storage handler
                if not TGOR_OT_RigSelectorModal.autostore in bpy.app.handlers.save_pre:
                    bpy.app.handlers.save_pre.append(TGOR_OT_RigSelectorModal.autostore)
                    
        elif not TGOR_OT_RigSelectorModal._drawHandle is None:
            
            # Reset draw handler
            bpy.types.SpaceView3D.draw_handler_remove(TGOR_OT_RigSelectorModal._drawHandle, 'WINDOW')
            
            # Remove storage handler
            if TGOR_OT_RigSelectorModal.autostore in bpy.app.handlers.save_pre:
                bpy.app.handlers.save_pre.remove(TGOR_OT_RigSelectorModal.autostore)
                    
            TGOR_OT_RigSelectorModal._drawHandle = None
        
    @staticmethod
    def toggleEdit(context, active):
        
        # Get interfaces to toggle edit mode
        interfaces = Util._interfaces
                
        # Toggle edit mode for all interfaces
        for interface in interfaces:
            interface.toggleEdit(context, active)
        
    
    # Draw all interfaces
    @staticmethod
    def render(context):
        
        # Get interfaces to draw
        interfaces = Util._interfaces
        
        # Get scale setting
        scaleAll = context.scene.enableRigSelector.scaleAll
        
        # Draw each interface
        for interface in interfaces:
            interface.draw(context, (0, 0), scaleAll)
        
    # Add new interface
    @staticmethod
    def addInterface(context):
        interfaces = Util._interfaces
                
        # Create new interface
        interface = Surfaces.Interface((0.0, 0.0), (256.0, 256.0))   
        Util._selectedInterface = interface
        interfaces.append(interface)

        TGOR_OT_RigSelectorModal.toggleEdit(context, context.scene.enableRigSelector.editing)
        return interface
    
    # Remove selected interface
    @staticmethod
    def removeInterface(context):
        interfaces = Util._interfaces
        if Util._selectedInterface:
            
            # Remove interface
            interfaces.remove(Util._selectedInterface)
            Util._selectedInterface = None
    
    
    # Remove selected interface
    @staticmethod
    def addSelectorToInterface(context, selector):
        if Util._selectedInterface:
            
            # Add selector to selected interface
            container = Util._selectedInterface._median._container
            container._selectors.append(selector)
            container.addChild(selector)
            
            # Update selector for initial link
            selector.updateLink(context)
            
    # Store text file
    @staticmethod
    def storeInterfaces(context):
    
        # refresh screen
        context.area.tag_redraw()
        
        # Create buffer
        buffer = Base.Buffer({})
        interfaces = Util._interfaces
        
        # Store grid size
        grid = context.scene.enableRigSelector.grid
        buffer.write("grid", grid)
        
        # Write to buffer
        for interface in interfaces:
            sub = buffer.push("interfaces")
            interface.store(context, sub)
        
        # Store as string
        context.scene.enableRigSelector.storage = json.dumps(buffer._data, indent=2)  
    
    
    # Load text file
    @staticmethod
    def loadInterfaces(context):
        
        # refresh screen
        if context.area:
            context.area.tag_redraw()
        
        # Reset interfaces
        TGOR_OT_RigSelectorModal.destroy(context)
        
        # Load from string
        if context.scene.enableRigSelector.storage:
            data = json.loads(context.scene.enableRigSelector.storage)   
            buffer = Base.Buffer(data) 
            
            # load grid size
            grid = context.scene.enableRigSelector.grid
            context.scene.enableRigSelector.grid = buffer.read("grid", float, grid)
            
            # Create interfaces
            while( True ): 
                sub = buffer.pop("interfaces")
                if sub:
                    interface = TGOR_OT_RigSelectorModal.addInterface(context)
                    interface.load(context, sub)
                else:
                    break
            
            # Toggle modes
            TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector.enabled)
            TGOR_OT_RigSelectorModal.toggleEdit(context, context.scene.enableRigSelector.editing)
    
    
    # Modal class, handles drag and drop etc
    def modal(self, context, event):
                
        # Make sure there is an active interface
        if self._active is None:
            return {'CANCELLED'}
        
        # Redraw as interface is probably moving
        context.area.tag_redraw()
        
        # Get scale setting
        scaleAll = context.scene.enableRigSelector.scaleAll
        
        # Get mouse offset
        pos = ((event.mouse_x - context.region.x) / scaleAll, (event.mouse_y - context.region.y) / scaleAll)
        
        # Update during drag and drop
        if event.type == 'MOUSEMOVE':
            
            # Call hold method
            self._active.hold(context, pos)
        
        elif event.type == 'LEFTMOUSE' or event.type == 'RIGHTMOUSE':
                        
            # Drop and end modal
            if event.value == 'RELEASE':
                
                # Call dropped method
                self._active.drop(context, pos)
                self._active = None
                
                return {'FINISHED'}                

        return {'RUNNING_MODAL'}
    
    # Starts drag and drop or handles click events
    def invoke(self, context, event):
                    
        # Get enabled checkbox
        enableRigSelector = context.scene.enableRigSelector
        startupRigSelector = context.scene.startupRigSelector
        interfaces = Util._interfaces
        
        # Make sure operator is enabled
        if(startupRigSelector.enabled == False):
            return {'PASS_THROUGH'}
        
        # Get scale setting
        scaleAll = enableRigSelector.scaleAll
        
        # Get mouse offset
        pos = ((event.mouse_x - context.region.x) / scaleAll, (event.mouse_y - context.region.y) / scaleAll)

        # Deselect only when clicking inside any interface
        if any([interface.isInside(context, pos) for interface in interfaces]):
            Util._selectedSelector = None
            
        # Check if mouse is over custom interface
        for interface in interfaces:
            right = event.type == 'RIGHTMOUSE'
            if interface.press(context, pos, right, event.shift):
                
                # Register
                self._active = interface
                Util._selectedInterface = interface
                
                # Redraw in case something changed
                context.area.tag_redraw()
                
                # Register modal
                if context.object:
                    context.window_manager.modal_handler_add(self)
                    return {'RUNNING_MODAL'}
                else:
                    return {'CANCELLED'}
            
        # Only interested in mousevenets when hovering over any interface
        return {'PASS_THROUGH'}

####################################################################################

# Toggles whole system on or off
def toggleEnabled(self, context):
    
    TGOR_OT_RigSelectorModal.toggleEnabled(context, self.enabled)
    
    if self.enabled:
        TGOR_OT_RigSelectorModal.loadInterfaces(context)
        
    if not self.enabled and context.scene.enableRigSelector.autosave:
        TGOR_OT_RigSelectorModal.storeInterfaces(context)
        
####################################################################################

# Toggles editing mode on or off
def toggleEdit(self, context):
        
    TGOR_OT_RigSelectorModal.toggleEdit(context, self.editing)


####################################################################################

# Add interface operator
class TGOR_OT_RigSelectorAdd(Operator):
    """Add interfaces"""
    bl_idname = "view3d.rig_add"
    bl_label = "Add interface"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        
        # refresh screen
        context.area.tag_redraw()
        TGOR_OT_RigSelectorModal.addInterface(context)
          
        # Toggle modes
        TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector)
        TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector)
        
        return {'FINISHED'}

# Remove interface operator
class TGOR_OT_RigSelectorRemove(Operator):
    """Remove interfaces"""
    bl_idname = "view3d.rig_remove"
    bl_label = "Remove Interface"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        # refresh screen
        context.area.tag_redraw()
        TGOR_OT_RigSelectorModal.removeInterface(context)
        
        # Toggle modes
        TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector)
        TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector)
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    


# Select layer operator
class TGOR_OT_RigSelectorAddLayerSelector(Operator):
    """Add layer selector to interfaces"""
    bl_idname = "view3d.rig_layerselector"
    bl_label = "Rig Layer Selector Operator"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
                
        # Refresh screen
        context.area.tag_redraw()
        
        # Make sure grid size is viable
        grid = context.scene.enableRigSelector.grid
        if grid < 10.0:
            grid = 10.0
        
        # Get layer index
        layer = context.scene.enableRigSelector.layer
        if layer < 0 or layer >= 32:
            self.report({'ERROR'}, "Layer index invalid")
        else :
            # Create layer selector
            selector = Selectors.LayerSelector((0.0, 0.0), layer)
            selector._build = False
            
            # Create vertices
            selector.addVertex(context, (grid * 2, 0.0))
            selector.addVertex(context, (grid * 2, grid * 2))
            selector.addVertex(context, (0.0, grid * 2))
            
            # Add layer selector
            TGOR_OT_RigSelectorModal.addSelectorToInterface(context, selector)
            
            # Toggle modes
            TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector)
            TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector)   
        
        return {'FINISHED'}
    

# Select image operator
class TGOR_OT_RigSelectorSetImageSelector(Operator):
    """Add image to interfaces"""
    bl_idname = "view3d.rig_imageselector"
    bl_label = "Rig Image Selector Operator"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        
        if Util._selectedInterface:
            
            # Refresh screen
            context.area.tag_redraw()
            
            # Get background image
            background = context.scene.enableRigSelector.background
            if background and background in bpy.data.images:
                image = bpy.data.images[background]
                
                if image.has_data:
                    image.update()

                    size = (max(image.size[0], 32), max(image.size[1], 32))
                    Util._selectedInterface._size = size
                    Util._selectedInterface._image = image
                    Util._selectedInterface._background = background
                    
                    # Make sure image doesn't get removed from blend file
                    image.use_fake_user = True
                    try:
                        image.pack()
                    except RuntimeError:
                        print('Failed to pack image')
                    
                    # Toggle modes
                    TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector)
                    toggleEdit(context.scene.enableRigSelector, context)
                else:
                    self.report({'ERROR'}, "Image has no data")
                
            else:
                
                # Reset image
                Util._selectedInterface._image = None
                Util._selectedInterface._background = ""
        
        else:
            self.report({'ERROR'}, "No interface selected")
            
        
        return {'FINISHED'}
    
# Store operator
class TGOR_OT_RigSelectorStore(Operator):
    """Store interfaces"""
    bl_idname = "view3d.rig_store"
    bl_label = "Rig Selector Storage Operator"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        
        TGOR_OT_RigSelectorModal.storeInterfaces(context)
        
        textblock = context.scene.enableRigSelector.textblock
        if not textblock:
            textblock = 'RigExport'
            
        if textblock in bpy.data.texts:
            text = bpy.data.texts[textblock]
        else:
            text = bpy.data.texts.new('RigExport')
            context.scene.enableRigSelector.textblock = 'RigExport'
        
        storage = context.scene.enableRigSelector.storage
        text.from_string(storage)
        
        return {'FINISHED'}



# Loading operator
class TGOR_OT_RigSelectorLoad(Operator):
    """Load interfaces"""
    bl_idname = "view3d.rig_load"
    bl_label = "Rig Selector Loading Operator"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        
        textblock = context.scene.enableRigSelector.textblock
        if not textblock:
            textblock = 'RigExport'
        
        if textblock in bpy.data.texts:
            text = bpy.data.texts[textblock]
            
            storage = text.as_string()
            context.scene.enableRigSelector.storage = storage
            
            TGOR_OT_RigSelectorModal.loadInterfaces(context)
        
        return {'FINISHED'}

# Toggle edit operator
class TGOR_OT_RigSelectorToggleEdit(Operator):
    """Toggle interfaces edit"""
    bl_idname = "view3d.rig_toggle_edit"
    bl_label = "Rig Selector Toggle Edit Operator"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        
        # Toggle edit state
        context.scene.enableRigSelector.editing = not context.scene.enableRigSelector.editing
            
        # Toggle modes
        TGOR_OT_RigSelectorModal.toggleEnabled(context, context.scene.startupRigSelector.enabled)
        TGOR_OT_RigSelectorModal.toggleEdit(context, context.scene.enableRigSelector.editing)
        
        return {'FINISHED'}

####################################################################################

# Store collections for unregister
classes = [
    TGOR_OT_RigSelectorModal,
    TGOR_OT_RigSelectorAdd,
    TGOR_OT_RigSelectorRemove,
    TGOR_OT_RigSelectorAddLayerSelector,
    TGOR_OT_RigSelectorSetImageSelector,
    TGOR_OT_RigSelectorStore,
    TGOR_OT_RigSelectorLoad,
    TGOR_OT_RigSelectorToggleEdit,
]

# Register modal and keymapping
def register():
    
    # Register classes
    from bpy.utils import register_class
    for c in classes:
        register_class(c)
    
# Unregister modal and keymapping
def unregister():

    # Unregister classes
    from bpy.utils import unregister_class
    for c in reversed(classes):
        unregister_class(c)