 
import maya.cmds as cmds

from rigpie.pylib.component import Component
from rigpie.pylib.control import Control
from rigpie.pylib.mayaname import MayaName

import rigpie.pylib.attribute as attribute
import rigpie.pylib.controlshape as controlshape_pylib

class Tree(Component):
    ''' Component built off of a hierarchy of joints '''
    
    def __init__(self, **kwargs):

        # Required arguments
        self.name = kwargs.get('name', 'CnTreeComponent')
        
        self.startJoint = kwargs.get('startJoint', 'CnRootJnt')
        self.jointList = kwargs.get('jointList', None)
        self.ignoreList = kwargs.get('ignoreList', [])
        self.ctrlsOnEndJoints = kwargs.get('ctrlsOnEndJoints', False)
        self.size = kwargs.get('size', 2)
        self.shapeType = kwargs.get('shapeType', 'cube')
        self.shapeRotation = kwargs.get('shapeRotation', [0,0,0])
        
        super(Tree, self).__init__(**kwargs)
        
        self.ctrlColor = kwargs.get('ctrlColor', None)
        self.lockAndHide = kwargs.get('lockAndHide', ['v'])

    def prebuild(self):
        super().prebuild()
        
    def build(self):

        jnts = []
        
        if not self.ctrlColor:
            self.ctrlColor = controlshape_pylib.getColorBySide(self.name)
        
        if self.jointList:
            for jnt in self.jointList:
                jnts.append(jnt)
                
                children = cmds.listRelatives(jnt, ad=True, type="joint")
                if children:
                    jnts.extend(children)
        else:
            jnts = [self.startJoint] + cmds.listRelatives(self.startJoint, ad=True, type="joint")

        # remove the joints and all it's children from the ignore list
        for jnt in self.ignoreList:
            jnts.remove(jnt)
            
            all_descendants = cmds.listRelatives(jnt, allDescendents=True, type="joint")
            
            if all_descendants:
                for descendants in all_descendants:
                    jnts.remove(descendants)
        
        parent_dict = {}
        
        for jnt in jnts:
            if self.ctrlsOnEndJoints == False:
                if cmds.listRelatives(jnt, c=1) == None:
                    continue
        
            control_name = MayaName(jnt)
            control_name.descriptor = control_name.descriptor + "Fk"
            control_name.category = "Ctrl"
            
            ctrl = Control( name=control_name, 
                            color=controlshape_pylib.getColorBySide(jnt),
                            size=self.size, 
                            shapeType=self.shapeType,
                            lockAndHide=self.lockAndHide, 
                            parent=self.controls_dag, 
                            matrix=jnt, 
                            shapeRotation=self.shapeRotation, 
                            inputJoint=jnt
            )
            self.registerControl(ctrl)
            
            if self.jointList:
                parent_joint = cmds.listRelatives(jnt, parent=True)[0]
                if parent_joint not in jnts:
                    self.export_joints[jnt] = None
                    continue
                    
                self.export_joints[jnt] = None
                self.export_joints_start.append(jnt)
                
            elif jnt == self.startJoint:
                self.export_joints[jnt] = None
                
                continue
            
            parent_joint = cmds.listRelatives(jnt, parent=True)[0]
            
            parent_name = MayaName(parent_joint)
            parent_name.descriptor = parent_name.descriptor + "Fk"
            parent_name.category = "Ctrl"
            parent_dict[ctrl.zero] = str(parent_name)
            
            # export joints
            self.export_joints[jnt] = parent_joint
            
            if not (cmds.listRelatives(jnt, children=True, type="joint")):
                self.export_joints_end.append(jnt)
            
            
        for zero in parent_dict:
            cmds.parent(zero, parent_dict[zero])

    def mirror(self):
        original_side = "Lf"
        mirrored_side = "Rt"
        if self.name[0:2] == "Rt":
            original_side = "Rt"
            mirrored_side = "Lf"
            

        newself = Tree(name=self.name.replace(original_side, mirrored_side))
        
        newself.startJoint = self.startJoint.replace(original_side, mirrored_side)
        
        if self.jointList:
            newself.jointList = [ "%s" % joint.replace(original_side, mirrored_side) for joint in self.jointList]

        if self.ignoreList:
            newself.ignoreList = [ "%s" % joint.replace(original_side, mirrored_side) for joint in self.ignoreList]
        else:
            newself.ignoreList = []
        
        newself.ctrlsOnEndJoints = self.ctrlsOnEndJoints
        
        newself.size = self.size
        newself.shapeType = self.shapeType
        newself.shapeRotation = self.shapeRotation
        
        return newself
        
    def prebuild(self):
        super().prebuild()