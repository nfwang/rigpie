 
import maya.cmds as cmds

from rigpie.components.limb import TwoSegmentLimb
from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.control import Control

import rigpie.pylib.rig as rig
import rigpie.pylib.attribute as attribute
import rigpie.pylib.shape as shape_pylib
import rigpie.pylib.constraints as constraints

class Leg(TwoSegmentLimb):
    ''' Leg component '''

    def __init__(self, **kwargs):
        
        kwargs['name'] = kwargs.get('name', "LfLegComponent")
        kwargs['componentMatrix'] = kwargs.get('componentMatrix', "LfThighJnt")
        
        super().__init__(**kwargs)

        self.startJoint = "LfThighJnt"
        self.midJoint = "LfKneeJnt"
        self.endJoint = "LfAnkleJnt"
        
        self.ballJoint = "LfBallJnt"
        self.toeJoint = "LfToeJnt"
        self.bankOutJoint = "LfBankOutJnt"
        self.bankInJoint = "LfBankInJnt"
        self.heelJoint = "LfHeelJnt"
        
        self.ikRotationOrder = "zxy"
        
        self.benderUpVector = [1, 0, 0]
        
        self.ikWorld = True
        self.pivotIKShape = "turtle"
        self.poleVectorMove = [0,0,20]
        
        
        self.defaultIk = 1
        
        # members
        self.start_fk = ""
        self.mid_fk = ""
        self.end_fk = ""
        self.ball_fk = ""
        self.ball_pivot = ""
        self.heel_pivot = ""
        self.bank_in_pivot = ""
        self.bank_out_pivot = ""
        self.toe_pivot = ""
        
    def mirror(self):
        
        original_side  = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side = "Rt"
            mirrored_side = "Lf"
            

        newself = Leg(name=self.name.replace(original_side, mirrored_side), componentMatrix=self.startJoint.replace(original_side, mirrored_side))
        
        newself.startJoint = self.startJoint.replace(original_side, mirrored_side)
        newself.midJoint   = self.midJoint.replace(original_side, mirrored_side)
        newself.endJoint   = self.endJoint.replace(original_side, mirrored_side)        
        
        newself.ballJoint  = self.ballJoint.replace(original_side, mirrored_side)
        newself.toeJoint   = self.toeJoint.replace(original_side, mirrored_side)
        newself.bankInJoint = self.bankInJoint.replace(original_side, mirrored_side)
        newself.bankOutJoint = self.bankOutJoint.replace(original_side, mirrored_side)
        newself.heelJoint = self.heelJoint.replace(original_side, mirrored_side)

        newself.hingeControl = self.hingeControl
        newself.benderControls = self.benderControls
        newself.benderUpVector = self.benderUpVector
        newself.upAxis = self.upAxis

        
        newself.startFkOffset = self.startFkOffset
        newself.zeroPoseRot = [-180, 0, 0]
        
        
        newself.mirrored   = 1
        
        return newself
        
    def build(self):
        super().build()

        # SegmentScaleCompensate has to be turned on for ik stretch to work
        cmds.setAttr(self.ballJoint+".segmentScaleCompensate", 1)
        cmds.setAttr(self.toeJoint+".segmentScaleCompensate", 1)

        ## Foot Roll Ctrls ##
        ball_fk_control_name = MayaName(self.ballJoint)
        ball_fk_control_name.descriptor = ball_fk_control_name.descriptor + "Fk"
        ball_fk_control_name.category = "Ctrl"
        
        self.ball_fk = Control( name=str(ball_fk_control_name), 
                                size=5, 
                                shapeRotation=[0,0,90],
                                shapeType="circle", 
                                color=shape_pylib.getColorBySide(self.startJoint), 
                                lockAndHide=["t","s","v"],
                                rotationOrder="zxy",
                                matrix=self.ballJoint, 
                                parent=self.end_fk.name
        )

        self.registerControl(self.ball_fk)

        cmds.orientConstraint(self.ball_fk.name, self.ballJoint)

        
        self.tagAsFKIKLimb(self.ball_fk.name)
        self.addSwitchDataFK(self.ball_fk.name)
        self.addSwitchDataFKLeg(self.ball_fk.name)
        
        # Roll
        # Create IKs
        (ball_ik, ball_effector) = cmds.ikHandle( startJoint=self.endJoint, endEffector=self.ballJoint, solver="ikSCsolver" )
        (toe_ik, toe_effector) = cmds.ikHandle( startJoint=self.ballJoint, endEffector=self.toeJoint, solver="ikSCsolver" )
        
        
        # hook up visibility to rig attribute
        cmds.connectAttr(self.rig_attr, ball_ik+".visibility")
        cmds.connectAttr(self.rig_attr, ball_effector+".visibility")
        
        cmds.connectAttr(self.rig_attr, toe_ik+".visibility")
        cmds.connectAttr(self.rig_attr, toe_effector+".visibility")
        
        cmds.parent(ball_ik, self.rig_dag)
        cmds.parent(toe_ik, self.rig_dag)

        # rename the ball ikhandle and effector
        ik_name = MayaName(self.name)
        ik_name.category = "Ikhandle"
        ik_name.descriptor = ik_name.descriptor + "Ball"
        ball_ik = cmds.rename(ball_ik, str(ik_name))
        ik_name.category = "Effector"
        ball_effector = cmds.rename(ball_effector, str(ik_name))
        
        # rename the toe ikhandle and effector
        ik_name = MayaName(self.name)
        ik_name.category = "Ikhandle"
        ik_name.descriptor = ik_name.descriptor + "Toe"
        toe_ik = cmds.rename(toe_ik, str(ik_name))
        ik_name.category = "Effector"
        toe_effector = cmds.rename(toe_effector, str(ik_name))

        cmds.connectAttr(self.ik_attr, ball_ik+".ikBlend")
        cmds.connectAttr(self.ik_attr, toe_ik+".ikBlend")
        
        
        ik_pivot_name = MayaName(self.name)
        ik_pivot_name.category = "Ctrl"
        description = ik_pivot_name.descriptor
        
        # Make pivots
        ik_pivot_name.descriptor = description+"BankOut"
        self.bank_out_pivot = Control( name=ik_pivot_name, 
                                       size=3,
                                       shapeRotation=[90, 0, 90], 
                                       color=shape_pylib.getColorBySide(self.startJoint), 
                                       shapeType="circle", 
                                       lockAndHide=["t","s","v"], 
                                       matrix=self.bankOutJoint, 
                                       depth=1, 
                                       rotationOrder="xyz",
                                       parent=self.end_ik_controls[-1].name
        )
        
        self.registerControl(self.bank_out_pivot)

        ik_pivot_name.descriptor = description+"BankIn"
        self.bank_in_pivot = Control( name=ik_pivot_name, 
                                      size=3,
                                      shapeRotation=[90, 0, 90], 
                                      color=shape_pylib.getColorBySide(self.startJoint), 
                                      shapeType="circle", 
                                      lockAndHide=["t","s","v"], 
                                      matrix=self.bankInJoint, 
                                      depth=1, 
                                      rotationOrder="xyz",
                                      parent=self.bank_out_pivot.name
        )
        self.registerControl(self.bank_in_pivot)
        
        ik_pivot_name.descriptor = description+"ToePivot"
        self.toe_pivot = Control( name=ik_pivot_name, 
                                  size=3,
                                  shapeRotation=[0, 0, 90], 
                                  color=shape_pylib.getColorBySide(self.startJoint), 
                                  shapeType="circle", 
                                  lockAndHide=["t","s","v"], 
                                  matrix=self.toeJoint, 
                                  depth=1, 
                                  rotationOrder="zxy",
                                  parent=self.bank_in_pivot.name
        )
        
        self.registerControl(self.toe_pivot)
                                 
        ik_pivot_name.descriptor = description+"HeelPivot"
        self.heel_pivot = Control( name=ik_pivot_name, 
                                   size=3,
                                   shapeRotation=[0, 0, 90], 
                                   color=shape_pylib.getColorBySide(self.startJoint), 
                                   shapeType="circle", 
                                   lockAndHide=["t","s","v"], 
                                   matrix=self.heelJoint, 
                                   depth=1, 
                                   rotationOrder="zxy",
                                   parent=self.toe_pivot.name
        )
        self.registerControl(self.heel_pivot)

        ik_pivot_name.descriptor = description+"BallPivot"
        self.ball_pivot = Control( name=ik_pivot_name, 
                                   size=5,
                                   shapeRotation=[0, 0, 90], 
                                   color=shape_pylib.getColorBySide(self.startJoint), 
                                   shapeType="circle", 
                                   lockAndHide=["t","s","v"], 
                                   matrix=self.ballJoint, 
                                   depth=1, 
                                   rotationOrder="zxy",
                                   parent=self.heel_pivot.name
        )
        self.registerControl(self.ball_pivot)

        ik_pivot_name.descriptor = description+"ToeIk"
        self.toe_ik = Control( name=ik_pivot_name, 
                               size=3,
                               shapeRotation=[0, 0, 90],
                               color=shape_pylib.getColorBySide(self.startJoint), 
                               shapeType="turtle", 
                               lockAndHide=["t","s","v"], 
                               matrix=self.ballJoint,
                               depth=1, 
                               rotationOrder="zxy",
                               parent=self.heel_pivot.name
        )
        self.registerControl(self.toe_ik)

        # parent ik handles
        cmds.parent(ball_ik, self.ball_pivot.name)
        cmds.parent(toe_ik, self.toe_ik.name)
        cmds.parent(self.ikhandle, self.ball_pivot.name)

        self.tagAsFKIKLimb(self.bank_out_pivot.name)
        self.tagAsFKIKLimb(self.bank_in_pivot.name)
        self.tagAsFKIKLimb(self.toe_pivot.name)
        self.tagAsFKIKLimb(self.heel_pivot.name)
        self.tagAsFKIKLimb(self.ball_pivot.name)
        self.tagAsFKIKLimb(self.toe_ik.name)
        
        self.addSwitchDataIK(self.bank_out_pivot.name)
        self.addSwitchDataIK(self.bank_in_pivot.name)        
        self.addSwitchDataIK(self.toe_pivot.name)
        self.addSwitchDataIK(self.heel_pivot.name)
        self.addSwitchDataIK(self.ball_pivot.name)
        self.addSwitchDataIK(self.toe_ik.name)

        self.addSwitchDataIKLeg(self.toe_pivot.name)
        self.addSwitchDataIKLeg(self.heel_pivot.name)
        self.addSwitchDataIKLeg(self.ball_pivot.name)
        self.addSwitchDataIKLeg(self.toe_ik.name)
        
        ## Add Leg data to limb ctrls
        ## IK ##
        self.addSwitchDataIKLeg(self.ik.name)
        self.addSwitchDataIKLeg(self.pivot_ik.name)
        
        ## FK ##
        self.addSwitchDataFKLeg(self.start_fk.name)
        self.addSwitchDataFKLeg(self.mid_fk.name)
        self.addSwitchDataFKLeg(self.end_fk.name)
        
        # constrain the stretch to the ik handle for the leg, so that the leg stretch ignores the foot pivots
        cmds.parentConstraint(self.ikhandle, self.end_stretch_transform)        
       
        # Add mirror data
        ctrls = cmds.listRelatives(self.controls_dag, allDescendents=True)
        
    def postbuild(self):
        super().postbuild()
        
        self.bind_joints.append(self.ballJoint)
        
        # export joint dictionary
        self.export_joints_end = [self.ballJoint]
        self.export_joints[self.ballJoint] = self.endJoint
        

    def addSwitchDataFKLeg (self, fkctrl):
        ''' Create message attributes to hold limb data '''
        cmds.connectAttr(self.ball_fk.name+".message", attribute.add(fkctrl+".toeFK", type="message"))
        cmds.connectAttr(self.ballJoint+".message", attribute.add(fkctrl+".ballJoint", type="message"))
        
    def addSwitchDataIKLeg (self, ikctrl):
        ''' Create message attributes to hold limb data '''

        cmds.connectAttr(self.toe_pivot.name+".message", attribute.add(ikctrl+".toePivot", type="message"))
        cmds.connectAttr(self.heel_pivot.name+".message", attribute.add(ikctrl+".heelPivot", type="message"))
        cmds.connectAttr(self.bank_in_pivot.name+".message", attribute.add(ikctrl+".bankInPivot", type="message"))
        cmds.connectAttr(self.bank_out_pivot.name+".message", attribute.add(ikctrl+".bankOutPivot", type="message"))
        cmds.connectAttr(self.ball_pivot.name+".message", attribute.add(ikctrl+".ballPivot", type="message"))
        
        cmds.connectAttr(self.ballJoint+".message", attribute.add(ikctrl+".ballJoint", type="message"))
        cmds.connectAttr(self.toe_ik.name+".message", attribute.add(ikctrl+".toe_ik", type="message"))