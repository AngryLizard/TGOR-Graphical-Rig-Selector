import bpy

from bpy.types import PropertyGroup
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty, PointerProperty

from bpy.app.handlers import persistent
from . import Operators

####################################################################################

# Selector startup properties
class RigSelectorStartupProperties(PropertyGroup):
    
    # Check to enable/disable nearest bone tool
    enabled: BoolProperty(
        name="EnableRigSelector",
        description="Enables rig selector",
        default = False,
        update = Operators.toggleEnabled)
        

# Selector properties
class RigSelectorProperties(PropertyGroup):
    
    # Check to enable/disable nearest bone tool
    editing: BoolProperty(
        name="EditRigSelector",
        description="Edit rig selector",
        default = False,
        update = Operators.toggleEdit)
    
    # Check to enable/disable nearest bone tool
    symmetry: BoolProperty(
        name="SymmetryRigSelector",
        description="Symmetry rig selector",
        default = False)
    
    # Clamp interface position to screen
    clamp: BoolProperty(
        name="ClampRigSelector",
        description="Clamp rig selector",
        default = True)
        
    # Change grid size
    grid: FloatProperty(
        name="GridRigSelector",
        description="Grid size",
        default = 0.0)
    
    # Change vertex scale
    scaleUI: FloatProperty(
        name="ScaleUIRigSelector",
        description="UI Scale size",
        min = 0.1,
        max = 5.0,
        default = 1.0)
        
    # Change vertex scale
    scaleAll: FloatProperty(
        name="ScaleAllRigSelector",
        description="All Scale size",
        min = 0.1,
        max = 5.0,
        default = 1.0)
    
    # Change background alpha
    alpha: FloatProperty(
        name="AlphaRigSelector",
        description="UI background alpha",
        min = 0.0,
        max = 1.0,
        default = 0.2)
        
    # Change layer property
    layer: IntProperty(
        name="LayerRigSelector",
        description="Layer index",
        min = 0,
        max = 31,
        default = 0)
        
    # Change background property
    background: StringProperty(
        name="BackgroundRigSelector",
        description="Background",
        default = "")
        
    # Change background property
    textblock: StringProperty(
        name="TextblockRigSelector",
        description="Textblock",
        default = "")
        
    # Storage field
    storage: StringProperty(
        name="StorageRigSelector",
        description="Storage rig selector",
        default = "")

    # Check to enable/disable nearest bone tool
    autosave: BoolProperty(
        name="Autosave",
        description="Enables autosaving the rig",
        default = False)

####################################################################################

@persistent
def onRigLoad(scene):
    Operators.toggleEnabled(scene.startupRigSelector, bpy.context)


####################################################################################

# Store collections for unregister
classes = [
    RigSelectorStartupProperties,
    RigSelectorProperties,
]

# Register modal and keymapping
def register():
    
    bpy.app.handlers.depsgraph_update_post.append(onRigLoad)

    # Register classes
    from bpy.utils import register_class
    for c in classes:
        register_class(c)
    
    # Register properties
    bpy.types.Scene.enableRigSelector = PointerProperty(type=RigSelectorProperties)
    bpy.types.Scene.startupRigSelector = PointerProperty(type=RigSelectorStartupProperties)

    Operators.register()
    
    
# Unregister modal and keymapping
def unregister():
    
    Operators.unregister()
        
    # Unregister properties
    del bpy.types.Scene.enableRigSelector
    del bpy.types.Scene.startupRigSelector

    # Unregister classes
    from bpy.utils import unregister_class
    for c in reversed(classes):
        unregister_class(c)

    if onRigLoad in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(onRigLoad)