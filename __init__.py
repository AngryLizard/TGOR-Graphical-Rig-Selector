import bpy

from bpy.types import Panel

from .Widgets.Base import Util
from . import Groups
from . import Operators

bl_info = {
    "name": "TGOR Rig Selector Interface",
    "author": "Hopfel, updated by RED_EYE)",
    "version": (2, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Properties > Rig Selector",
    "description": "Enables the user to select bones with a custom floating viewport interface and gives an ability to create/edit these interfaces.",
    "warning": "",
    "wiki_url": "",
    "category": "Animation"
    }

####################################################################################

# Selector panel for settings
class TGOR_PT_RigSelectorPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_label = "Rig Selector"
    
    startup = False
    
    def draw(self, context):
        
        # Get enable/disable checkbox
        layout = self.layout
        enableRigSelector = context.scene.enableRigSelector
        startupRigSelector = context.scene.startupRigSelector
        
        row = layout.row(align=True)
        row.prop(startupRigSelector, "enabled", text="Enabled")
        
        if startupRigSelector.enabled:
            
            # display the properties
            layout.label(text="Options", icon='SETTINGS')
            box = layout.box()
            row = box.row(align=True)
            row.prop(enableRigSelector, "editing", text="Editing")
            row.prop(enableRigSelector, "symmetry", text="Symmetry")
            row.prop(enableRigSelector, "clamp", text="Clamp")
            
            row = box.row(align=True)
            row.prop(enableRigSelector, "grid", text="Grid size")
            row.prop(enableRigSelector, "alpha", text="Background")
            row = box.row(align=True)
            row.prop(enableRigSelector, "scaleUI", text="Vertex scale")
            row.prop(enableRigSelector, "scaleAll", text="All scale")
                    
            layout.label(text="Add/Remove", icon='ZOOM_IN')
            box = layout.box()
            row = box.row(align=True)
            row.prop(enableRigSelector, "layer", text="Layer")
            row.operator("view3d.rig_layerselector", text = "Layer selector")
            
            row = box.row(align=True)
            row.prop_search(enableRigSelector, "background", bpy.data, "images", text="", icon='IMAGE_DATA')
            row.operator("view3d.rig_imageselector", text = "Set Background")
                    
            row = box.row(align=True)
            row.operator("view3d.rig_add", text = "Add interfaces")
            row.operator("view3d.rig_remove", text = "Remove interfaces")
            
            layout.label(text="Storage", icon='SYSTEM')
            box = layout.box()     
            row = box.row(align=True)
            row.prop_search(enableRigSelector, "textblock", bpy.data, "texts", text="", icon='TEXT')
                   
            row = box.row(align=True)
            row.operator("view3d.rig_store", text = "Save interfaces")
            row.operator("view3d.rig_load", text = "Load interfaces")

            row = box.row(align=True)
            row.prop(enableRigSelector, "autosave", text="Autosave")
            
            # Init operation on first draw
            if Util._interfaces == None:
                
                # Build interfaces
                Operators.TGOR_OT_RigSelectorModal.build(context)

                # Toggle depending on current selection
                Operators.TGOR_OT_RigSelectorModal.toggleEnabled(context, startupRigSelector)
                Operators.toggleEdit(context.scene.enableRigSelector, context)

####################################################################################


# Store collections for unregister
classes = [
    TGOR_PT_RigSelectorPanel
]

# Store collections for unregister
keymaps = []

# Register modal and keymapping
def register():
    
    # Register classes
    from bpy.utils import register_class
    for c in classes:
        register_class(c)
    
    # Regsiter keymap to left mouse
    keyconfigs = bpy.context.window_manager.keyconfigs.addon
    if keyconfigs:
        keyMap = keyconfigs.keymaps.new(name='3D View', space_type='VIEW_3D')
        item = keyMap.keymap_items.new(idname='view3d.rig_selector', type='LEFTMOUSE', value='PRESS', shift=False)
        keymaps.append((keyMap, item))
        item = keyMap.keymap_items.new(idname='view3d.rig_selector', type='LEFTMOUSE', value='PRESS', shift=True)
        keymaps.append((keyMap, item))
        #item = keyMap.keymap_items.new(idname='view3d.rig_selector', type='RIGHTMOUSE', value='PRESS', shift=False)
        #keymaps.append((keyMap, item))
        #item = keyMap.keymap_items.new(idname='view3d.rig_selector', type='RIGHTMOUSE', value='PRESS', shift=True)
        #keymaps.append((keyMap, item))

    Groups.register()
    

# Unregister modal and keymapping
def unregister():

    Operators.TGOR_OT_RigSelectorModal.destroy(bpy.context)
    
    Groups.unregister()
    
    # Unregister keymap to left mouse
    for keyMap, item in keymaps:
        keyMap.keymap_items.remove(item)
    keymaps.clear()

    # Unregister classes
    from bpy.utils import unregister_class
    for c in reversed(classes):
        unregister_class(c)


if __name__ == "__main__":
            
    register()