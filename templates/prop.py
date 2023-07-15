 
import maya.cmds as cmds

from rigpie.components.basic import Basic
from rigpie.pylib.rig import Rig

import rigpie.pylib.attribute as attribute_pylib

class Prop(Rig):
    ''' Prop template '''
    
    def __init__(self):
        super().__init__()
        
        self.rootJoint = "CnRootJnt"
        
        # members
        self.root = ""
        self.cogA = ""
        self.cogB = ""
    
    def registerComponents(self):
        self.root_component = Basic( name="CnRootComponent", 
                                     shapeType = "cube", 
                                     controlOffsets=2, 
                                     joint = self.rootJoint,
                                     lockAndHide = ['v', 's']
        )
                                    
        self.registerComponent(self.root_component)
    
    def prebuild(self):
        super().prebuild()

        if not self.skeleton_path:
            cmds.createNode("joint", n=self.rootJoint, p=self.skeleton_dag)
        
    def build(self):
        super().build()
        
        cmds.parent(self.root_component.name, "CnMasterCCtrl")
        
    def postbuild(self):
        super().postbuild()
        
        # root offset visibility switch
        for ii, offset in enumerate(self.root_component.offset_controls):
            attr = self.master.name+".root"+str(ii)
            attribute_pylib.add(attr, value=0)
            cmds.connectAttr(attr, offset.shape+".visibility")
        
        
