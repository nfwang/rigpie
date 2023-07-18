 

import maya.cmds as cmds

from rigpie.pylib.component import Component
from rigpie.pylib.control import Control
from rigpie.pylib.mayaname import MayaName

import rigpie.pylib.controlshape as controlshape_pylib
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.rig as rig_pylib
import rigpie.pylib.rmath as rmath_pylib

class Hand(Component):
    ''' Hand component with fingers '''
    def __init__(self, **kwargs):

        kwargs['name'] = kwargs['name'] if 'name' in kwargs and kwargs['name'] is not None else "LfHandComponent"

        super().__init__(**kwargs)
        
        self.fingers = kwargs.get('fingers', ["LfIndex0Jnt","LfMiddle0Jnt","LfRing0Jnt","LfPinky0Jnt"])
        self.numDigits = kwargs.get('numDigits', [3,3,3,3])
        self.metaCarps = kwargs.get('metaCarps', [True, True, True, True])
        self.thumbJoint = kwargs.get('thumbJoint', "LfThumb1Jnt")
        self.thumbJointDigits = kwargs.get('thumbJointDigits', 3)
        
        # members
        self.component_options = ""
        self.finger_controls = {} # [index, middle, ring, pinky, thumb]
        self.metacarpel_controls = [] # [index, middle, ring, pinky, thumb]
        self.zeroPoseRot = {"finger": [0, 0, 0], "thumb":[135, -45, -45]}
        
        self.mirrored = 0

    def mirror(self):

        original_side  = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side  = "Rt"
            mirrored_side = "Lf"
            

        newself = Hand(name=self.name.replace(original_side, mirrored_side))
        
        newself.numDigits = self.numDigits
        newself.fingers = [ "%s" % name.replace(original_side,mirrored_side) for name in self.fingers ]
        newself.thumbJoint = self.thumbJoint.replace(original_side, mirrored_side)
        
        newself.metaCarps = self.metaCarps
        newself.zeroPoseRot = {"finger": [-180, 0, 0], "thumb":[-45, 45, 45]}
        newself.thumbJointDigits = self.thumbJointDigits
        
        newself.mirrored = 1
        
        return newself

    def prebuild(self):
        super().prebuild()
        
        # get the center of all the start joints as the position of the component dag

        m = rmath_pylib.Transform()
        pos = rmath_pylib.Vector()
        
        # get the center to align the pin
        for joint in self.fingers:
            pos += rmath_pylib.Vector(joint)
        
        pos = pos / float(len(self.fingers))
        
        m.setTranslation(pos)
        self.componentMatrix = list(m)

        
    def build(self):
    
        super().build()

        # Finger controls
        for ii in range(len(self.fingers)):
            finger_controls = []    
            finger_joint = self.fingers[ii]
            numDigits = self.numDigits[ii]
            metaCarp  = self.metaCarps[ii]
            
            parnt = self.controls_dag
            
            parent_joint = None
            if metaCarp:
                ctrl_name = MayaName(finger_joint)
                ctrl_name.category = "Ctrl"
                
                ctrl = Control( name=ctrl_name, 
                                size=1, 
                                shapeRotation=[0,0,90], 
                                shapeType="cube", 
                                color=controlshape_pylib.getColorBySide(finger_joint), 
                                lockAndHide=["t","s","v"], 
                                matrix=finger_joint, 
                                inputJoint=finger_joint,
                                parent=parnt
                )
                
                parnt = ctrl.name
                self.metacarpel_controls.append(ctrl)
                self.registerControl(ctrl)
                
                self.export_joints[finger_joint] = None
                parent_joint = finger_joint
                
            # export joints
            self.export_joints_start.append(finger_joint)
            
            for jj in range(1, numDigits+1):
                joint_name = MayaName(finger_joint)
                joint_name.iterator = str(jj)
                
                ctrl_name = MayaName(finger_joint)
                ctrl_name.category = "Ctrl"
                ctrl_name.iterator = str(jj)
                ctrl = Control( name=str(ctrl_name), 
                                size=1, 
                                shapeRotation=[0,0,90],
                                shapeType="cube", 
                                color=controlshape_pylib.getColorBySide(str(joint_name)), 
                                matrix=str(joint_name), 
                                lockAndHide=["t","s","v"], 
                                inputJoint=str(joint_name),
                                parent=parnt
                )
                
                self.registerControl(ctrl)

                finger_controls.append(ctrl)
                
                if parent_joint:
                    self.export_joints[str(joint_name)] = parent_joint
                
                parnt = ctrl.name
                parent_joint = str(joint_name)
                
            name = MayaName(self.fingers[ii])
            self.finger_controls[name.descriptor] = finger_controls
        
        # Thumb
        if cmds.objExists(self.thumbJoint):
            parnt = self.controls_dag
            finger_controls = []
            
            thumb_root_name = MayaName(self.thumbJoint)
            thumb_digit_start = int(thumb_root_name.iterator)
            
            self.export_joints_start.append(self.thumbJoint)
            parent_joint = None
            self.export_joints[self.thumbJoint] = None
            
            for ii in range(thumb_digit_start, self.thumbJointDigits + thumb_digit_start):

                joint_name = MayaName(self.thumbJoint)
                joint_name.iterator = str(ii)
                
                ctrl_name = MayaName(self.thumbJoint)
                ctrl_name.category = "Ctrl"
                ctrl_name.iterator = str(ii)

                ctrl = Control( name=str(ctrl_name), 
                                size=1, 
                                shapeRotation=[0,0,90], 
                                shapeType="cube", 
                                color=controlshape_pylib.getColorBySide(self.thumbJoint), 
                                matrix=str(joint_name), 
                                lockAndHide=["t","s","v"], 
                                inputJoint=str(joint_name),
                                parent=parnt
                )
                
                self.registerControl(ctrl)
                
                if parent_joint:
                    self.export_joints[str(joint_name)] = parent_joint
                
                parnt = ctrl.name
                parent_joint = str(joint_name)
                
                finger_controls.append(ctrl)
            
            name = MayaName(self.thumbJoint)
            self.finger_controls[name.descriptor] = finger_controls

        
    def postbuild(self):
        super().postbuild()
