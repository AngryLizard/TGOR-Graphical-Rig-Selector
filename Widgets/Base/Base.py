
####################################################################################

class Writeable():
    
    # Stores this class to a buffer
    def store(self, context, buffer):
        pass
    
    # Loads this class from a buffer
    def load(self, context, buffer):
        pass
    
    # Factors for new list entries
    def create(self, context, baseClass):
        pass
        
####################################################################################

class Buffer():
    
    # Actual data
    _data = {}
    
    # Constructor
    def __init__(self, data):
        self._data = data
        
    def empty(self):
        self._data = {}
    
    def error(self, name, message):
        raise SyntaxError(message + " at [" + name + "]. Input JSON faulty or from another version.")
    
    # Read data from data dictionary given its name and type
    def read(self, name, baseClass, default):
        if name in self._data:
            
            # Get and check data
            data = self._data[name]
            if not isinstance(data, baseClass):
                self.error(name, "Wrong type, expected " + str(baseClass) + ", actually got " + str(type(data)))
            
            return data
        
        return default
    
    # Store data to data dictionary given its name
    def write(self, name, var):
        if name in self._data:
            self.error(name, "Data already exists")
        else:
            self._data[name] = var
    
    # Append dataset to the end of array given its name
    def push(self, name):
        
        # Create new subset if not exists already
        if not name in self._data:
            self._data[name] = []
        
        # Create new buffer with subdata set
        data = {}
        self._data[name].append(data)
        return Buffer(data)
    
    
    # Pop dataset from the end of array given its name
    def pop(self, name):
        
        if name in self._data:
            
            # Shift data from array
            list = self._data[name]
            
            # Pop first element if not empty
            if list:
                return Buffer(list.pop(0))
        return(None)
        
    # Append sub-dataset to this dataset given its name
    def sub(self, name):
        
        # Create new subset if not exists already
        if not name in self._data:
            self._data[name] = {}
        
        # Create new buffer with subdata set
        return Buffer(self._data[name])