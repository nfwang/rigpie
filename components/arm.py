 

import maya.cmds as cmds

from rigpie.components.limb import TwoSegmentLimb

from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.control import Control
import rigpie.pylib.attribute as attribute
import rigpie.pylib.controlshape as controlshape_pylib
import rigpie.pylib.constraints as constraints
import rigpie.pylib.xform as xform
import rigpie.pylib.rig as rig

class Arm(TwoSegmentLimb):
    def __init__(self, **kwargs):

        kwargs['name'] = kwargs.get('name', "LfArmComponent")
        kwargs['componentMatrix'] = kwargs.get('componentMatrix', None)
        
        kwargs['startJoint'] = kwargs.get('startJoint', "LfShoulderJnt")
        kwargs['midJoint'] = kwargs.get('midJoint', "LfElbowJnt")
        kwargs['endJoint'] = kwargs.get('endJoint', "LfWristJnt")
        
        super(Arm, self).__init__(**kwargs)
        
        self.clavicleJoint = kwargs.get('clavicleJoint', "LfClavicleJnt")
        self.lowerTwistJnt = kwargs.get('lowerTwistJnt', None)
        
        self.benderStartUpVector = [0, 1, 0]
        self.benderMidUpVector = [0, 0, 1]
        
        self.lowerTwistAimVector = [1, 0, 0]
        self.lowerTwistUpVector = [0, 0, 1]
        
        self.pvDir = -1
        self.ikWorld = True
        self.ikRotationOrder = "yxz"
        
        self.zeroPoseRot = [0, 0, 0]
        self.upVectorMove = [0,0,-20]
        self.clavShapeRot = [-90,-90,0]
        
        self.defaultIk = 0
        
        # Protected members
        self.clavicle_control     = ""
        
    def mirror(self):
        
        original_side = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side  = "Rt"
            replace = "Lf"
        
        componentMatrix = None
        if self.componentMatrix:
            componentMatrix = self.componentMatrix.replace(original_side, mirrored_side)
        
        newself = Arm( name=self.name.replace(original_side, mirrored_side), componentMatrix=componentMatrix)
        
        newself.clavicleJoint = self.clavicleJoint.replace(original_side, mirrored_side)
        newself.startJoint = self.startJoint.replace(original_side, mirrored_side)
        newself.midJoint = self.midJoint.replace(original_side, mirrored_side)
        newself.endJoint = self.endJoint.replace(original_side, mirrored_side)
        
        if self.lowerTwistJnt:
            newself.lowerTwistJnt = self.lowerTwistJnt.replace(original_side, mirrored_side)

        newself.startGimbal = self.startGimbal
        newself.endGimbal = self.endGimbal        

        newself.startFkOffset = self.startFkOffset

        newself.lowerTwistAimVector = [-1, 0, 0]
        newself.lowerTwistUpVector = [0, 0, -1]
        newself.zeroPoseRot  = [-180, 0, 0]
        
        newself.clavShapeRot = [90,-90,0]
        
        newself.hingeControl = self.hingeControl
        newself.benderControls = self.benderControls
        
        newself.upAxis = self.upAxis
        newself.benderUpVector = self.benderUpVector
        
        newself.mirrored = 1
        
        return newself
        
    def prebuild(self):
        super().prebuild()
        
        if self.componentMatrix == None:
            self.componentMatrix = self.clavicleJoint
        
    def build(self):
        super().build()
        
        ## Clavicle ##
        if cmds.objExists(self.clavicleJoint):
            clavicle_control_name = MayaName(self.clavicleJoint)
            clavicle_control_name.category = "Ctrl"
        
            self.clavicle_control = Control( name=clavicle_control_name, 
                                             size=5, 
                                             shapeRotation=self.clavShapeRot, 
                                             color=controlshape_pylib.getColorBySide(self.clavicleJoint), 
                                             depth=2,
                                             shapeType="turtle", 
                                             matrix=self.clavicleJoint, 
                                             parent=self.controls_dag, 
                                             inputJoint=self.clavicleJoint,
                                             lockAndHide=["t","s","v"]
            )
            self.registerControl(self.clavicle_control)
        
        # parent limb start pin to clavicle
        cmds.parent(self.pins["start"], self.clavicleJoint) 
        
        # use the ik for stretch
        cmds.parentConstraint(self.ik.name, self.end_stretch_transform)

    
    def postbuild(self):
        super().postbuild()
        
        self.bind_joints.append(self.clavicleJoint)
        
        # export joint dictionary
        self.export_joints[self.export_joints_start[0]] = self.clavicleJoint
        self.export_joints_start = [self.clavicleJoint]
        self.export_joints[self.clavicleJoint] = None
        