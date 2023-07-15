 

import maya.cmds as cmds

from rigpie.pylib.component import Component 
from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.control import Control

import rigpie.pylib.controlshape as controlshape_pylib

class Basic(Component):
    ''' A basic one joint control component '''
    
    def __init__(self, **kwargs):

        self.name = kwargs.get('name', "CnBasicComponent") 
        kwargs['componentMatrix'] = kwargs.get('componentMatrix', None) 
        
        super().__init__(**kwargs)
        
        self.joint = kwargs.get('joint', None)
        self.matrix = kwargs.get('matrix', None)
        self.offsetDescriptors = kwargs.get('offsetDescriptors', [])
        self.size = kwargs.get('size', 10)
        self.shapeType = kwargs.get('shapeType', "sphere")
        self.shapeRotation = kwargs.get('shapeRotation', [0,0,0])
        self.controlColor = kwargs.get('controlColor', None)
        self.thickness = kwargs.get('thickness', 1)
        
        self.controlOffsets = kwargs.get('controlOffsets', 0)
        self.transformOffsets = kwargs.get('transformOffsets', 1)
        
        self.lockAndHide = kwargs.get('lockAndHide', ['v'])
        self.rotationOrder = kwargs.get('rotationOrder', None)
        
        # members
        self.control = None
        self.zero = None
        self.offset_controls = []
        
    def build(self):
        super().build()
        
        offset_controls = []
        parent_offset = self.controls_dag

        name = MayaName(self.name)
        name.category = "Ctrl"
        
        if not self.matrix:
            self.matrix = self.joint
        
        if not self.rotationOrder:
            self.rotationOrder = self.joint 
            
        if self.controlColor == None:
            self.controlColor = controlshape_pylib.getColorBySide(str(name))

        self.control = Control( name=name, 
                                size=self.size, 
                                shapeRotation=self.shapeRotation,
                                color=self.controlColor, 
                                thickness=self.thickness,
                                shapeType=self.shapeType, 
                                lockAndHide=self.lockAndHide, 
                                depth=self.transformOffsets,
                                matrix=self.matrix, 
                                rotationOrder=self.rotationOrder,
                                parent=self.controls_dag 
        )
        parent_offset = self.control.name
        
        # use the descriptor list or iterator on the single descriptor
        if self.offsetDescriptors:
            for description in self.offsetDescriptors:
                if description == "#":
                    description = ""
                
                name = MayaName(self.name)
                name.descriptor = name.descriptor + description
                name.category = "Ctrl"
                
                offset_control = Control( name=name, 
                                          size=self.size, 
                                          shapeRotation=[0,0,90],
                                          color=controlshape_pylib.getColorBySide(str(name)), 
                                          thickness=self.thickness,
                                          shapeType=self.shapeType, 
                                          lockAndHide=self.lockAndHide, 
                                          depth=0, 
                                          matrix=self.matrix, 
                                          rotationOrder=self.rotationOrder,
                                          parent=parent_offset 
                )
                
                offset_controls.append(offset_control)
                
                parent_offset = offset_control.name
                
        else:
            for count in range(self.controlOffsets):
                name = MayaName(self.name)
                name.descriptor = name.descriptor
                name.iterator = count + 1
                name.category = "Ctrl"
                
                offset_control = Control( name=name, 
                                          size=self.size / (count + 1), 
                                          shapeRotation=[0,0,90],
                                          color=controlshape_pylib.getColorBySide(str(name)), 
                                          thickness=self.thickness,
                                          shapeType=self.shapeType, 
                                          lockAndHide=self.lockAndHide, 
                                          depth=0, 
                                          matrix=self.matrix, 
                                          rotationOrder=self.rotationOrder,
                                          parent=parent_offset
                )
                offset_controls.append(offset_control)
                
                parent_offset = offset_control.name
        self.controls.extend(offset_controls)

        self.offset_controls = offset_controls
        self.zero = self.control.zero
        self.registerControl(self.control)

        if self.joint:
            cmds.parentConstraint(parent_offset, self.joint)
            cmds.scaleConstraint(parent_offset, self.joint)

    def postbuild(self):
        super().postbuild()
        
        if self.joint:
            # export joint dictionary
            self.export_joints[self.joint] = None
            self.export_joints_start = [self.joint]
            self.export_joints_end = [self.joint]
    
    def mirror(self):

        original_side = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side = "Rt"
            mirrored_side = "Lf"
            

        newself = Basic(name=self.name.replace(original_side, mirrored_side))
        newself.joint = self.joint.replace(original_side, mirrored_side)

        newself.controlOffsets = self.controlOffsets
        newself.transformOffsets = self.transformOffsets
        
        newself.size = self.size
        newself.shapeType = self.shapeType
        newself.thickness = self.thickness
    
        
        newself.mirrored = 1
        return newself     
