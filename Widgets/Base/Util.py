import bpy

# Override Decorator
def Overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider

# Floating point range
def frange(a, b, it):
  while a < b:
    yield a
    a += it
    
# Rounds towards a
def roundTowards(x, a=0.5, step=1.0):
    f = x % step
    return x - f if f < a * step else x + step - f

# Checks if grid is active and adapts to it
def adaptToGrid(pos, active):

    # See if grid is active
    grid = bpy.context.scene.enableRigSelector.grid
    if active and grid > 0.0:
        x = roundTowards(pos[0], 0.5, grid)
        y = roundTowards(pos[1], 0.5, grid)
    
        return (x, y)
    return (pos)


# Currently active interfaces
_interfaces = []

# Currently selected selector
_selectedSelector = None

# Currently selected selector
_selectedInterface = None