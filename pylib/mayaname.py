 

import maya.cmds as cmds

class MayaName(object):
    ''' Class for naming things consistently.
    
        Current Convention:
    
        Side: first two characters  expected values: ['Lf','Rt','Cn']
        Category: Last capitalized word.
        Iterator: Integers before the category
        Descriptor: Everything else is the descriptor.
        Instance: numbers at the end after the last capitalized letter ("category")
        
        Iterators and Instance numbers are optional
    ''' 

    def __init__(self,*args):
        object.__init__(self)

        self.side = "Cn"
        self.descriptor = "Default"
        self.iterator = "" # Optional
        self.category = "Ctrl"
        self.instance = ""  # Optional

        if args:
            if isinstance(args[0], str):
                self.setNameFromString(*args)
            else:
                self.side = args[0].side
                self.descriptor = args[0].descriptor
                self.iterator = args[0].iterator
                self.category = args[0].category
                self.instance = args[0].instance
            
        
    def setNameFromString(self, *args):
        '''Given a string, fill out a name class '''
        
        self.side = args[0][0] + args[0][1]
        string_arg = args[0]
        
        iterator_index = None
        category_index = None
        instance_index = None
        
        iterator = False
        instance = False
        
        if string_arg[-1].isdigit():
            instance = True
            
        for ii in range(len(string_arg)-1, -1, -1):
            if instance and (not string_arg[ii].isdigit() and (not category_index) and (not instance_index)):
                instance_index = ii
                continue
        
            if (string_arg[ii].isupper()) and (not category_index):
                category_index = ii
                continue
            
            if not instance:
                if string_arg[ii].isdigit() and category_index:
                    iterator = True
                
                if not string_arg[ii].isdigit() and category_index:
                    iterator_index = ii
                    break
            else:
                if string_arg[ii].isdigit() and category_index and instance_index:
                    iterator = True
            
                if not string_arg[ii].isdigit() and category_index and instance_index:
                    iterator_index = ii
                    break
        
        if instance:
            self.instance = string_arg[instance_index+1:len(string_arg)+1]        
            self.category = string_arg[category_index:instance_index+1]
        else:
            self.category = string_arg[category_index:len(string_arg)+1]
            
        if iterator:
            self.iterator = string_arg[iterator_index+1:category_index]
            self.descriptor = string_arg[2:iterator_index+1]
        else:
            self.descriptor = string_arg[2:category_index]
    
    def __str__(self):
        return "{0}{1}{2}{3}{4}".format(self.side, self.descriptor, self.iterator, self.category, self.instance)
        