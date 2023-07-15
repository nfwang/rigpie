 
import maya.cmds as cmds

from rigpie.pylib.component import Component
from rigpie.pylib.control import Control
from rigpie.pylib.mayaname import MayaName

import rigpie.pylib.controlshape as controlshape_pylib
import rigpie.pylib.joint as joint_pylib
import rigpie.pylib.coordspace as coordspace_pylib
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.constraints as constraints_pylib

class Piston(Component):
    '''  Given a start and end joint, create a stretchable ik '''
    
    def __init__(self,  **kwargs):
        
        # Required arguments
        kwargs['name'] = kwargs.get('name', "CnPistonComponent")
        
        super().__init__(**kwargs)
        
        self.startJoint = kwargs.get('startJoint', 'CnMainJnt')
        self.endJoint = kwargs.get('endJoint', 'CnMainEndJnt')
        self.size = kwargs.get('upVector', 10)
        self.createControl = kwargs.get('createControl', False)
        self.aimVector = kwargs.get('aimVector', [1,0,0])
        self.upVector = kwargs.get('upVector', [0,1,0])
        self.upVectorAimTransform = kwargs.get('upVectorAimTransform', 'CnMainUpAimJnt')

        # Protected members
        self.controls = []
        self.pins = {}
        
    def mirror(self):
        original_side  = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side = "Rt"
            mirrored_side = "Lf"
            
        
        newself = Piston(name=self.name.replace(original_side, mirrored_side))
        
        newself.startJoint = self.startJoint.replace(original_side, mirrored_side)
        newself.endJoint = self.endJoint.replace(original_side, mirrored_side)
        newself.upVectorAimTransform = self.upVectorAimTransform.replace(original_side, mirrored_side)
        newself.createControl = self.createControl
        
        newself.aimVector = self.aimVector
        newself.upVector = self.upVector
        
        newself.mirrored = 1
        
        return newself
        
    def prebuild(self):
        super().prebuild()
        
    def build(self):

        aim_axis = joint_pylib.getLongAxis(self.endJoint)
        
        # start pin
        pin_start_name = MayaName(self.name)
        pin_start_name.descriptor = pin_start_name.descriptor + "StartPin"
        pin_start_name.category = "Null"
        self.pins["start"] = cmds.createNode("transform", name=pin_start_name, parent=self.controls_dag)

        xform_pylib.align(self.pins["start"], self.startJoint)
        
        # end pin
        pin_end_name = MayaName(self.name)
        pin_end_name.descriptor = pin_end_name.descriptor + "EndPin"
        pin_end_name.category = "Null"
        self.pins["end"] = cmds.createNode("transform", name=pin_end_name, parent=self.controls_dag)

        xform_pylib.align(self.pins["end"], self.endJoint)
        
        scale_transform = None
        
        if self.createControl:
            control_name = MayaName(self.name)
            control_name.category = "Ctrl"
        
            self.control = Control( name=str(control_name),
                                    size=1,
                                    shapeRotation=[0,0,0], 
                                    color=controlshape_pylib.getColorBySide(self.name),
                                    shapeType="cube", 
                                    depth=2,
                                    lockAndHide=["v"],
                                    matrix=self.startJoint, 
                                    inputJoint=self.startJoint, 
                                    parent=self.controls_dag
            )
            self.registerControl(self.control)
            
            cmds.aimConstraint( self.pins["end"], 
                                self.pins["start"], 
                                aimVector=self.aimVector, 
                                upVector=self.upVector, 
                                worldUpType="object", 
                                worldUpObject=self.upVectorAimTransform
            )
            cmds.parent(self.control.zero, self.pins["start"])
            cmds.parentConstraint(self.pins["end"], self.endJoint)
            scale_transform = self.control.offset_transforms[0]
            
        else:
            ikhandle_name = MayaName(self.name)
            ikhandle_name.category = "Ikhandle"
        
            (ikhandle, effector) = cmds.ikHandle(startJoint=self.startJoint, endEffector=self.endJoint, solver="ikRPsolver")
            
            ikhandle = cmds.rename(ikhandle, ikhandle_name)
            cmds.parent(ikhandle, self.rig_dag)
            
            cmds.poleVectorConstraint (self.upVectorAimTransform, ikhandle, weight=1)
            
            constraints_pylib.parentConstraintMaintainOffset(self.pins["start"], self.startJoint)
            cmds.parentConstraint(self.pins["end"], ikhandle)
            
            scale_transform = self.startJoint
        
        # Create a reference transform to make everything work with rig scale
        scale_reference_name = MayaName(self.endJoint)
        scale_reference_name.descriptor = scale_reference_name.descriptor + "ScaleRef"
        scale_reference_name.category = "Null"
        
        scale_reference = cmds.createNode("transform", name=scale_reference_name, p=self.rig_dag)
        
        xform_pylib.align(scale_reference, self.endJoint)
        
        decompose_scale_ref_name = scale_reference_name
        decompose_scale_ref_name.category = "DecomposeMatrix"
        decompose_scale_ref = cmds.createNode("decomposeMatrix",  n=decompose_scale_ref_name)
        cmds.connectAttr(scale_reference + ".worldMatrix", decompose_scale_ref+".inputMatrix")
        
        # measure the distance and connect to scale
        distance_name = MayaName(self.name)
        distance_name.category = "DistanceDimension"
        distance = cmds.createNode("distanceDimShape", n=str(distance_name)+"Shape")
        distance_transform = cmds.rename(cmds.listRelatives(distance, parent=True)[0], distance_name)
        
        cmds.parent( distance_transform, self.rig_dag )
        
        decompose_start_name = MayaName(self.name)
        decompose_start_name.descriptor = decompose_start_name.descriptor + "StartStretch"
        decompose_start_name.category = "DecomposeMatrix"
        decompose_start = cmds.createNode("decomposeMatrix",  n=decompose_start_name)

        decompose_end_name = MayaName(self.name)
        decompose_end_name.descriptor = decompose_end_name.descriptor + "EndStretch"
        decompose_end_name.category = "DecomposeMatrix"
        
        decompose_end = cmds.createNode("decomposeMatrix",  n=decompose_end_name)
        
        cmds.connectAttr(self.pins["start"] + ".worldMatrix", decompose_start+".inputMatrix")
        cmds.connectAttr(self.pins["end"]+".worldMatrix", decompose_end+".inputMatrix" )
        
        cmds.connectAttr(decompose_start+".outputTranslate", distance+".startPoint")
        cmds.connectAttr(decompose_end+".outputTranslate", distance+".endPoint" )

        static_distance_name = MayaName(self.name)
        static_distance_name.descriptor = static_distance_name.descriptor + "Static"
        static_distance_name.category = "DistanceDimension"
        static_distance = cmds.createNode("distanceDimShape", n=str(static_distance_name)+"Shape")
        cmds.rename(cmds.listRelatives(static_distance, parent=True)[0], static_distance_name)        
        cmds.parent(cmds.listRelatives(static_distance, parent=True)[0], self.worldspace_dag)
        
        cmds.connectAttr(decompose_start + ".outputTranslate", static_distance + ".startPoint")
        cmds.connectAttr(decompose_scale_ref + ".outputTranslate", static_distance + ".endPoint")

        # Divide the distance with its current value
        ratio_md_name = MayaName(self.name)
        ratio_md_name.descriptor = ratio_md_name.descriptor + "StretchRatio"
        ratio_md_name.category = "MultiplyDivide"

        ratio_md = cmds.createNode("multiplyDivide", n=ratio_md_name)
        cmds.setAttr(ratio_md+".operation", 2)
        cmds.connectAttr(distance+".distance", ratio_md+".input1X")
        
        cmds.connectAttr(static_distance+".distance", ratio_md+".input2X")

        cmds.connectAttr(ratio_md+".outputX", "{}.scale{}".format(scale_transform, aim_axis))
       
    def postbuild(self):
        super().postbuild()
        
        # export joint dictionary
        self.export_joints[self.startJoint] = None
        self.export_joints_start = [self.startJoint]
        self.export_joints_end = [self.endJoint]
        
