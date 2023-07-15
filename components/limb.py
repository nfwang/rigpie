 
import maya.cmds as cmds
import maya.mel as mel

from rigpie.pylib.component import Component

from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.control import Control
from rigpie.pylib.rmath import Transform, Vector

import rigpie.pylib.shape as shape_pylib
import rigpie.pylib.constraints as constraints_pylib
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.rig as rig_pylib
import rigpie.pylib.joint as joint_pylib
import rigpie.pylib.curve as curve_pylib
import rigpie.pylib.mayatransform as mayatransform_pylib

class Limb(Component):
    ''' FK/IK rig setup used for legs and arms '''
    
    def __init__(self, **kwargs):
        
        self.name = kwargs['name'] if 'name' in kwargs and kwargs['name'] is not None else "component"
        
        super().__init__(**kwargs)
        
        self.startJoint = kwargs.get('startJoint', "CnStartJnt")
        
        self.midJoint = kwargs.get('midJoint', 'CnMidJnt')
        self.hockJoint = kwargs.get('hockJoint', 'CnHockJnt')
        self.ankleJoint = kwargs.get('ankleJoint', 'CnAnkleJnt')
        self.endJoint = kwargs.get('endJoint', 'CnEndJnt')
        
        self.poleVectorMove = kwargs.get('poleVectorMove', [0,0,-20] )
        self.poleVectorTranslation = kwargs.get('poleVectorTranslation', [0,0,0])
        self.defaultIk = kwargs.get('defaultIk', 0)
        self.zeroPoseRot = kwargs.get('zeroPoseRot', [0, 0, 0])
        
        self.upAxis = kwargs.get('upAxis', 'Y')
        self.hingeControl = kwargs.get('hingeControl', False)
        self.benderControls = kwargs.get('benderControls', False)
        self.benderUpVector = kwargs.get('benderUpVector', [0, 0, 1])
        self.alignIkToWorld = kwargs.get('alignIkToWorld', True)
        self.startFkOffset = kwargs.get('startFkOffset', True)
        self.startGimbal = kwargs.get('startGimbal', True)
        self.endGimbal = kwargs.get('endGimbal', True)
        self.ikRotationOrder = kwargs.get('ikRotationOrder', "zxy")
        
        # protected members
        self.ik = ""
        self.toe_ik_handle = ""
        self.pivot_ik = ""
        self.pivot_ikShape = "sphere"
        self.spring_ikhandle = ""
        self.ikhandle = ""
        self.effector = ""
        self.fk_snap = ""
        
        self.fk_controls_dag = None
        self.ik_controls_dag = None
        
        self.bind_joints = []
        
        self.pins = {}
        self.sockets = {"end":None}

    def prebuild(self):
        super().prebuild()
    
    def build(self):
        
        super().build()
        
        self.aimAxis = joint_pylib.getLongAxis(self.endJoint)
        
        self.upVector = Vector([1,0,0])
        if self.upAxis == "Y":
            self.upVector = Vector([0, 1, 0])
        elif self.upAxis == "Z":
            self.upVector = Vector([0, 0, 1])
            
        self.aim_translate_value = cmds.getAttr("{}.translate{}".format(self.endJoint, self.aimAxis))
        self.aim_coefficient = self.aim_translate_value / abs (self.aim_translate_value)
        
        self.aimVector = Vector([1,0,0])
        if self.aimAxis == "Y":
            self.aimVector = Vector([0, 1, 0])
        elif self.aimAxis == "Z":
            self.aimVector = Vector([0, 0, 1])

        self.aimVector = self.aimVector * self.aim_coefficient
        
        
        # start pin
        start_pin_name = MayaName(self.name)
        start_pin_name.category = "Null"
        start_pin_name.descriptor = start_pin_name.descriptor + "StartPin"
        
        pin_start = cmds.createNode("transform", name=str(start_pin_name), parent=self.worldspace_dag)
        
        self.pins["start"] = pin_start
        xform_pylib.align(pin_start, self.startJoint)
        
        # fk dag
        fk_dag_name = MayaName(self.name)
        fk_dag_name.category = "Dag"
        fk_dag_name.descriptor = fk_dag_name.descriptor + "Fk"
        self.fk_controls_dag = cmds.createNode("transform", parent=self.controls_dag, n=str(fk_dag_name))
    
        # ik dag
        ik_dag_name = MayaName(self.name)
        ik_dag_name.category = "Dag"
        ik_dag_name.descriptor = ik_dag_name.descriptor + "Ik"
        self.ik_controls_dag = cmds.createNode("transform", parent=self.controls_dag, n=str(ik_dag_name))


        # add attribute and attach to visibility attrs
        self.ik_attr = attribute_pylib.add( self.component_options+".ik", 
                                            type="float", 
                                            max=1.0, 
                                            min=0.0, 
                                            value=1.0, 
                                            dv=self.defaultIk 
        )
        cmds.connectAttr(self.ik_attr, self.ik_controls_dag+".visibility")

        invert_ik_name = MayaName(self.name)
        invert_ik_name.category = "Plusminusaverage"
        invert_ik_name.descriptor = invert_ik_name.descriptor + "InvertIkAttr"
        
        # flip the ik value to control the fk visibility
        fk_visibility_plumin = cmds.createNode("plusMinusAverage", n=invert_ik_name)
        cmds.setAttr(fk_visibility_plumin+".input1D[0]", 1)
        cmds.connectAttr(self.ik_attr, fk_visibility_plumin+".input1D[1]")
        cmds.setAttr(fk_visibility_plumin+".operation", 2)
        
        self.fk_attr = fk_visibility_plumin+".output1D"
        cmds.connectAttr(self.fk_attr, self.fk_controls_dag+".visibility")

        # end socket
        socket_end_name = MayaName(self.name)
        socket_end_name.category = "Null"
        socket_end_name.descriptor = socket_end_name.descriptor + "EndSocket"
        
        socket_end = cmds.createNode("transform", name=str(socket_end_name), parent=self.worldspace_dag)
        cmds.connectAttr(self.endJoint+".worldMatrix", socket_end+".offsetParentMatrix")
        
        self.sockets["end"] = socket_end


    def postbuild(self):
        
        super().postbuild()
    
        attribute_pylib.lock(self.ikhandle, ['t','r','s'])
        
        
        # fill out the export joint dictionary to generate an export rig.
        self.getExportJointDict()

    
    def tagAsFKIKLimb(self, ctrl):
        ''' This is used for the marking menu IK/FK switching '''
        if not(cmds.objExists(ctrl+".isFKIKLimb")):
            cmds.addAttr(ctrl, ln="isFKIKLimb", k=False, dv=1)
            return True
        else:
            return False
    
    def addSwitchDataFK (self, fkctrl):
        ''' Create message attributes to hold limb data '''
        cmds.connectAttr( self.startJoint+".message", attribute_pylib.add( fkctrl+".startIK", type="message" ) )
        cmds.connectAttr( self.midJoint+".message",   attribute_pylib.add( fkctrl+".midIK",   type="message" ) )
        cmds.connectAttr( self.endJoint+".message",   attribute_pylib.add( fkctrl+".endIK",   type="message" ) )
        cmds.connectAttr( self.start_fk.name+".message",  attribute_pylib.add( fkctrl+".start_fk", type="message" ) )
        cmds.connectAttr( self.mid_fk.name+".message",    attribute_pylib.add( fkctrl+".midFK",   type="message" ) )
        cmds.connectAttr( self.end_fk.name+".message",    attribute_pylib.add( fkctrl+".endFK",   type="message" ) )
        cmds.connectAttr( self.ik.name+".message",       attribute_pylib.add( fkctrl+".IK",      type="message" ) )
        
    def addSwitchDataIK (self, ikctrl):
        ''' Create message attributes to hold limb data '''
        cmds.connectAttr( self.start_fk.name+".message",  attribute_pylib.add( ikctrl+".start_fk", type="message" ) )
        cmds.connectAttr( self.mid_fk.name+".message",    attribute_pylib.add( ikctrl+".midFK",   type="message" ) )
        cmds.connectAttr( self.iksnap+".message",   attribute_pylib.add( ikctrl+".endFK",   type="message" ) )
        cmds.connectAttr( self.pivot_ik.name+".message",  attribute_pylib.add( ikctrl+".pv",      type="message" ) )
        cmds.connectAttr( self.start_fk.name+".message",  attribute_pylib.add( ikctrl+".FK",      type="message" ) )
        
    def makeAutoPV (self, end=None, twistFollow=False):
        
        if not end:
            end = self.endJoint
            
        start_joint = cmds.duplicate( self.startJoint, parentOnly=True, name=self.startJoint.replace("Jnt", "PVJnt") )[0]
        end_joint = cmds.duplicate( end, po=True, n=self.endJoint.replace("Jnt", "PVJnt") )[0]
        
        cmds.delete( cmds.aimConstraint(end_joint, start_joint, upVector=[0,1,0], worldUpType="object", worldUpObject=self.pivot_ik.name ) )
        
        cmds.parent( start_joint, self.rig_dag )
        cmds.parent( end_joint, start_joint )
        
        (ikhandle, effector) = cmds.ikHandle(startJoint=start_joint, endEffector=end_joint, solver="ikSCsolver")
        ikhandle = cmds.rename(ikhandle, self.name+"_pvikHandle")
        cmds.parent(ikhandle, self.rig_dag)

        auto_pv_name = MayaName(self.pivot_ik.name)
        auto_pv_name.category = "Null"
        auto_pv_name.descriptor = auto_pv_name.descriptor+"Auto"
        
        self.auto_pv = cmds.createNode( "transform", n=auto_pv_name, parent=self.rig_dag )
        xform_pylib.align( self.auto_pv, self.pivot_ik.name )
        
        cmds.pointConstraint( self.ik.name, ikhandle )

        if twistFollow:
            twist_zero = cmds.createNode("transform", name=ikhandle+"_twistzero", parent=self.rig_dag)
            xform_pylib.align(twist_zero, self.ik.name)
            twistfol = cmds.duplicate(twist_zero, n=ikhandle+"_twist")[0]
            cmds.pointConstraint(self.ik.name, twist_zero)
            cmds.parent(twistfol, twist_zero)
            
            cmds.connectAttr( self.ik.name+".ry", twistfol+".ry" )
            cmds.orientConstraint(twistfol, ikhandle)
            
        cmds.parent( self.auto_pv, start_joint )
        cmds.pointConstraint( self.pins["start"], start_joint )

    def createBenderJoints(self, startJoint, endJoint):
        ''' bender joints are intermediate joints that are created for an arm or a leg that allows bowing '''

        curve_name = MayaName(startJoint)
        curve_name.category = "Curve"

        # use splineIK to make the curve
        (ikhandle, effector, curve) = cmds.ikHandle(startJoint=startJoint, endEffector=endJoint, solver="ikSplineSolver", ns=4)
        cmds.delete(ikhandle)
        
        bender_joint_name = MayaName(startJoint)
        bender_joint_name.descriptor = bender_joint_name.descriptor + "Bender"

        bender_joints = curve_pylib.createNodesAlongCurve(curve, startJoint, 4, name=bender_joint_name)
        
        cmds.delete(curve)
        
        return bender_joints

    def createHingeJoints(self, startJoint, endJoint):
        ''' Hinge Joints are the intermediate joints that are created for an arm or a leg that allows pivoting and stretching from the hinge area, ie, knee or elbow. '''

        hinge_joints = []

        a_joint = cmds.createNode("joint", name=startJoint.replace("Jnt", "HingeJnt"))
        
        xform_pylib.align(a_joint, startJoint)
        cmds.setAttr( a_joint + ".radius", cmds.getAttr(startJoint + ".radius") / 2)
        hinge_joints.append(a_joint)
        cmds.makeIdentity(a_joint, apply=True, t=1, r=1, s=1, n=0)

        b_joint = cmds.createNode("joint", name=startJoint.replace("Jnt", "Hinge1Jnt"), parent=a_joint)
        xform_pylib.align(b_joint, endJoint)
        cmds.setAttr(b_joint + ".radius", cmds.getAttr(startJoint + ".radius") / 2)
        hinge_joints.append(b_joint)
        
        xform_pylib.alignRotation(b_joint, a_joint)

        cmds.makeIdentity(b_joint, apply=True, translate=1, rotate=1, scale=1, normal=0)
        
        return hinge_joints

    def createBenderControls(self, startJoint, endJoint, benderJoints, count, descriptor, upVectorUnits=50, upVector=None, upVectorShape="square"):
        ''' Bender controls for each segment of a arm or leg. '''
        
        bender_name = MayaName(startJoint)
        bender_name.descriptor = descriptor + "Bender"
        bender_name.category = "Null"
        
        bender_controls = []

        # Bender ik
        (ikhandle, effector, curve) = cmds.ikHandle(startJoint=benderJoints[0], endEffector=benderJoints[-1], solver="ikSplineSolver", ns=4)
        
        ikhandle_name = MayaName(startJoint)
        ikhandle_name.descriptor = descriptor + "Bender"
        ikhandle_name.category = "Ikhandle"
        ikhandle = cmds.rename(ikhandle, ikhandle_name)
        
        ikhandle_name.category = "Curve"
        curve = cmds.rename(curve, ikhandle_name)

        cmds.parent(ikhandle, self.worldspace_dag)
        cmds.parent(curve, self.worldspace_dag)

        # Controls
        start_joint_transform = Transform(startJoint)
        
        # up vectors
        up_vector_name = MayaName(bender_name)
        up_vector_name.descriptor += "StartUp"
        up_vector_name.category = "Ctrl"
        
        if upVector == None:
            upVector = self.benderUpVector
        
        start_up_vector_transform = Transform()
        bender_up_vector = Vector(upVector)
        
        start_up_vector_transform.translate(bender_up_vector * upVectorUnits)
        start_up_vector_transform = start_up_vector_transform * start_joint_transform
        
        rgb = shape_pylib.getRgbBySide(self.startJoint, alternate=True)
        start_up_vector = Control( name=up_vector_name, 
                                   size=2, 
                                   shapeRotation=[90, 0, 0],
                                   color=rgb, 
                                   shapeType=upVectorShape, 
                                   depth=4,
                                   lockAndHide=["r","s"], 
                                   rotationOrder="xyz",
                                   matrix=start_up_vector_transform,
                                   parent=self.controls_dag
        )
        self.registerControl(start_up_vector)
        
        # align the second to last transform to the source so that we can have a twist attribute
        twist_transform = start_up_vector.offset_transforms[-2]
        xform_pylib.align(twist_transform, startJoint, ignoreChildren=True)
        twist_attr = "{}.bender{}A_twist".format(self.component_options, descriptor)
        attribute_pylib.add(twist_attr, min=None, max=None, type="float")
        cmds.connectAttr(twist_attr, "{}.rotate{}".format(twist_transform, self.aimAxis))
        
        end_joint_transform = Transform(endJoint)
        
        up_vector_name = MayaName(bender_name)
        up_vector_name.descriptor += "EndUp"
        up_vector_name.category = "Ctrl"

        end_up_vector_transform = Transform()
        end_up_vector_transform.translate(bender_up_vector * upVectorUnits)
        end_up_vector_transform = end_up_vector_transform * end_joint_transform

        end_up_vector = Control( name=up_vector_name, 
                                 size=2, 
                                 shapeRotation=[90, 0, 0],
                                 color=rgb, 
                                 shapeType=upVectorShape, 
                                 depth=4,
                                 lockAndHide=["r","s"], 
                                 rotationOrder="xyz",
                                 matrix=end_up_vector_transform,
                                 parent=self.controls_dag
        )
        self.registerControl(end_up_vector)
        
        # align the second to last transform to the source so that we can have a twist attribute
        twist_transform = end_up_vector.offset_transforms[-2]
        xform_pylib.align(twist_transform, endJoint, ignoreChildren=True)
        twist_attr = "{}.bender{}B_twist".format(self.component_options, descriptor)
        attribute_pylib.add(twist_attr, min=None, max=None, type="float")
        cmds.connectAttr(twist_attr, "{}.rotate{}".format(twist_transform, self.aimAxis))
        
        # Spline IK options
        cmds.setAttr(ikhandle + ".dTwistControlEnable", 1)
        cmds.setAttr(ikhandle + ".dWorldUpType", 2)
        cmds.setAttr(ikhandle + ".dForwardAxis", self.aimVector.getMayaEnumInt())
        cmds.setAttr(ikhandle + ".dWorldUpAxis", bender_up_vector.getMayaEnumInt(include_closest=True))
        
        cmds.connectAttr(start_up_vector.name+".worldMatrix[0]", ikhandle+".dWorldUpMatrix", force=True)
        cmds.connectAttr(end_up_vector.name+".worldMatrix[0]", ikhandle+".dWorldUpMatrixEnd", force=True)
        
        transforms = curve_pylib.createNodesAlongCurve(curve, startJoint, 3, name=bender_name, type="transform", parameterizeCurve=True)
        
        # auto determine the shape rotation
        if self.aimAxis == "X":
            shapeRotation = Vector([0, 0, -90]) * self.aim_coefficient
        elif self.aimAxis == "Z":
            shapeRotation = Vector([90, 0, 0]) * self.aim_coefficient
        else:
            if self.aim_coefficient == 1:
                shapeRotation = Vector([0, 0, 0])
            else:
                shapeRotation = Vector([0, 0, 180])
                
        for ii, transform in enumerate(transforms):

            control_name = MayaName(bender_name)
            control_name.iterator = ii
            control_name.category = "Ctrl"

            control = Control( name=control_name, 
                               type="joint",
                               size=8, 
                               color=rgb, 
                               shapeRotation=list(shapeRotation),
                               shapeType="shell", 
                               depth=1,
                               lockAndHide=["s"], 
                               rotationOrder="xyz",
                               matrix=transform,
                               parent=self.controls_dag
            )
            self.registerControl(control)
            
            bender_controls.append(control)
        
        # up vectors
        cmds.parentConstraint(startJoint, start_up_vector.zero, maintainOffset=True)
        cmds.parentConstraint(startJoint, end_up_vector.zero, maintainOffset=True)
        
        # start
        cmds.parentConstraint(startJoint, bender_controls[0].zero)
        
        # middle
        cmds.pointConstraint(startJoint, bender_controls[1].zero)
        cmds.pointConstraint(endJoint, bender_controls[1].zero)
        cmds.orientConstraint(startJoint, bender_controls[1].zero)
        
        # end
        cmds.pointConstraint(endJoint, bender_controls[2].zero)
        cmds.orientConstraint(startJoint, bender_controls[2].zero)
        
        curve_pylib.enableStretchyComponentJoints(curve, startJoint, endJoint, benderJoints, bender_controls, self, aimVector=list(self.aimVector))
        
        # Skin the spline
        curve_skincluster = cmds.skinCluster(curve, [ bender_control.name for bender_control in bender_controls ])[0]
        
        cmds.delete(transforms)
        
        return [bender_controls, [start_up_vector, end_up_vector], curve]



class ThreeSegmentLimb(Limb):
    ''' Three segments limb used for animals and insect legs '''

    def __init__(self, **kwargs):

        self.name = kwargs['name'] if 'name' in kwargs and kwargs['name'] is not None else "component"

        super().__init__(**kwargs)
        
        self.startJoint = kwargs['startJoint'] if 'startJoint' in kwargs and kwargs['startJoint'] is not None else "CnStartJnt"
        self.midJoint = kwargs['midJoint'] if 'midJoint' in kwargs and kwargs['midJoint'] is not None else "CnMidJnt"
        self.hockJoint = kwargs['hockJoint'] if 'hockJoint' in kwargs and kwargs['hockJoint'] is not None else "CnHockJnt"
        self.ankleJoint = kwargs['ankleJoint'] if 'ankleJoint' in kwargs and kwargs['ankleJoint'] is not None else "CnAnkleJnt"
        self.endJoint = kwargs['endJoint'] if 'endJoint' in kwargs and kwargs['endJoint'] is not None else "CnEndJnt"
        self.poleVectorTranslation = kwargs['poleVectorTranslation'] if 'poleVectorTranslation' in kwargs and kwargs['poleVectorTranslation'] is not None else None
        self.defaultIk = kwargs['defaultIk'] if 'defaultIk' in kwargs and kwargs['defaultIk'] is not None else 0
        self.zeroPoseRot = kwargs['zeroPoseRot'] if 'zeroPoseRot' in kwargs and kwargs['zeroPoseRot'] is not None else [0, 0, 0]
        
        # not supported for threesegmentlimb
        self.hingeControl = False
        
        self.ikRotationOrder = "zxy"
        
        self.ik = ""
        self.toe_ik_handle = ""
        self.pivot_ik = ""
        self.pivot_ikShape = "sphere"
        self.spring_ikhandle = ""
        self.ikhandle = ""
        self.effector = ""
        self.fk_snap = ""
        
        self.fk_controls_dag = None
        self.ik_controls_dag = None
        
        self.pins = {}

    def prebuild(self):
        super().prebuild()


    def build(self):
        super().build()
        
        #### FK Rig ####
        fk_parent = self.fk_controls_dag

        if self.startFkOffset:
        
            ## Create start offset
            ctrl_name = MayaName(self.startJoint)
            ctrl_name.category = "Ctrl"
            ctrl_name.descriptor = ctrl_name.descriptor+"OffsetFk"
        
            self.fk_offset = Control( name=str(ctrl_name), 
                                      size=5, 
                                      color=shape_pylib.getColorBySide(self.startJoint), 
                                      shapeType="sphere", 
                                      lockAndHide=["t","s","v"], 
                                      depth=2,
                                      matrix=self.startJoint,
                                      rotationOrder="zxy",
                                      parent=self.fk_controls_dag
            )
            self.registerControl(self.fk_offset)
            
            fk_parent = self.fk_offset.name
            

        ctrl_name = MayaName(self.startJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Fk"
        ctrl_name.category = "Ctrl"
        self.start_fk = Control( name=str(ctrl_name), 
                                 size=5, 
                                 shapeRotation=[0,0,90], 
                                 color=shape_pylib.getColorBySide(self.startJoint),
                                 shapeType="cube", 
                                 lockAndHide=["t","s","v"], 
                                 matrix=self.startJoint, 
                                 rotationOrder=self.startJoint,
                                 parent=fk_parent
        )
        self.registerControl(self.start_fk)

        
        ctrl_name = MayaName(self.midJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Fk"
        ctrl_name.category = "Ctrl"
        self.mid_fk = Control( name=str(ctrl_name), 
                               size=5, 
                               shapeRotation=[0,0,90], 
                               color=shape_pylib.getColorBySide(self.midJoint), 
                               shapeType="cube", 
                               lockAndHide=["t","s","v"], 
                               matrix=self.midJoint, 
                               rotationOrder=self.midJoint,
                               parent=self.start_fk.name
        )
        self.registerControl(self.mid_fk)

        ctrl_name = MayaName(self.hockJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Fk"
        ctrl_name.category = "Ctrl"
        self.hockFK = Control( name=str(ctrl_name), 
                               size=5, 
                               shapeRotation=[0,0,90], 
                               color=shape_pylib.getColorBySide(self.hockJoint), 
                               shapeType="cube", 
                               lockAndHide=["t","s","v"], 
                               matrix=self.hockJoint, 
                               rotationOrder=self.hockJoint,
                               parent=self.mid_fk.name
        )
        self.registerControl(self.hockFK)

        ctrl_name = MayaName(self.ankleJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Fk"
        ctrl_name.category = "Ctrl"
        self.ankleFK = Control( name=str(ctrl_name), 
                                size=5, 
                                shapeRotation=[0,0,90], 
                                color=shape_pylib.getColorBySide(self.ankleJoint), 
                                shapeType="cube", 
                                lockAndHide=["t","s","v"], 
                                matrix=self.ankleJoint, 
                                rotationOrder=self.ankleJoint,
                                parent=self.hockFK.name
        )
        self.registerControl(self.ankleFK)

        
        # Orient Constrain ctrls to joints
        cmds.parentConstraint(self.start_fk.name, self.startJoint)
        cmds.orientConstraint(self.mid_fk.name, self.midJoint)
        cmds.orientConstraint(self.hockFK.name, self.hockJoint)
        cmds.orientConstraint(self.ankleFK.name, self.ankleJoint)
        
        self.tagAsFKIKLimb(self.start_fk.name)
        self.tagAsFKIKLimb(self.mid_fk.name)
        self.tagAsFKIKLimb(self.hockFK.name)
        self.tagAsFKIKLimb(self.ankleFK.name)

        # pin fk control
        constraints_pylib.parentConstraintMaintainOffset(self.pins["start"], self.fk_offset.zero)

        # Create Controls
        # start control
        ctrl_name = MayaName(self.startJoint)
        ctrl_name.category = "Ctrl"
        ctrl_name.descriptor = ctrl_name.descriptor+"OffsetIk"

        self.startIkOffset = Control( name=str(ctrl_name),
                                      size=5,
                                      color=shape_pylib.getColorBySide(self.startJoint),
                                      shapeType="sphere",
                                      lockAndHide=["s","v"],
                                      matrix=self.startJoint,
                                      rotationOrder="zxy",
                                      parent=self.ik_controls_dag
        )
        self.registerControl(self.startIkOffset)

        
        # ik control
        ik_transform = Transform()
        ik_transform.setTranslation(cmds.xform(self.ankleJoint, translation=True, worldSpace=True, query=True))
        
        ctrl_name = MayaName(self.ankleJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Ik"
        ctrl_name.category = "Ctrl"
        self.ik = Control( name=str(ctrl_name),
                           size=5, 
                           shapeRotation=[0,0,90],
                           color=shape_pylib.getColorBySide(self.ankleJoint),
                           thickness=3,
                           shapeType="cube",
                           lockAndHide=["s","v"],
                           matrix=ik_transform,
                           rotationOrder=self.ikRotationOrder,
                           parent=self.ik_controls_dag
        )
        self.registerControl(self.ik)

        ik_transform = Transform()
        ik_transform.setTranslation(cmds.xform(self.endJoint, translation=True, worldSpace=True, query=True))
        
        ctrl_name = MayaName(self.endJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Ik"
        ctrl_name.category = "Ctrl"
        self.ik_end = Control( name=str(ctrl_name),
                               size=3, 
                               shapeRotation=[0,0,90],
                               color=shape_pylib.getColorBySide(self.endJoint),
                               thickness=1,
                               shapeType="sphere",
                               lockAndHide=["s","v"],
                               matrix=ik_transform,
                               rotationOrder=self.ikRotationOrder,
                               parent=self.ik.name
        )
        self.registerControl(self.ik_end)

        # ik pv control
        pv_transform = Transform()
        
        # try to get the upVector position
        if self.poleVectorTranslation == None:
            position_transform = cmds.createNode("transform", name=self.name+"DeleteMeNull", p=self.startJoint)
            xform_pylib.align(position_transform, self.startJoint)
            
            cmds.setAttr("{}.translate{}".format(position_transform, self.aimAxis), self.aim_translate_value * 2.0)
            
            pv_transform.setTranslation(cmds.xform(position_transform, worldSpace=True, translation=True, query=True))
            cmds.delete(position_transform)
        else:
            pv_transform.setTranslation(self.poleVectorTranslation)
        
        
        
        if self.poleVectorMove:
            v = Vector(self.poleVectorMove)
            pv_transform.translate(v)

        ctrl_name = MayaName(self.midJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Pv"
        ctrl_name.category = "Ctrl"
        self.pivot_ik = Control( name=str(ctrl_name), 
                                size=1, 
                                shapeRotation=[0,0,0], 
                                color=shape_pylib.getColorBySide(self.midJoint), 
                                shapeType=self.pivot_ikShape, 
                                lockAndHide=["r","s","v"], 
                                matrix=pv_transform, 
                                depth=2,
                                parent=self.ik_controls_dag, 
        )
        self.registerControl(self.pivot_ik)
        
        
        if not self.alignIkToWorld:
            xform_pylib.align(self.ik.zero, self.ankleJoint)
            xform_pylib.align(self.pivot_ik.zero, self.midJoint)
        
        
        # duplicate the joint chain for the spring ik
        self.spring_start = joint_pylib.duplicate(self.startJoint, appendDescription="Spring", hierarchy=False)[0]
        spring_mid = joint_pylib.duplicate(self.midJoint, appendDescription="Spring", hierarchy=False)[0]
        spring_hock = joint_pylib.duplicate(self.hockJoint, appendDescription="Spring", hierarchy=False)[0]
        spring_ankle = joint_pylib.duplicate(self.ankleJoint, appendDescription="Spring", hierarchy=False)[0]
        
        # ik spring solver
        mel.eval("ikSpringSolver")
        ikhandle_name = MayaName(self.ankleJoint)
        ikhandle_name.category = "Ikhandle"
        ikhandle_name.descriptor = ikhandle_name.descriptor + "Spring"

        (ikhandle, effector) = cmds.ikHandle(startJoint=self.spring_start, endEffector=spring_ankle, solver="ikSpringSolver")
        self.spring_ikhandle = cmds.rename(ikhandle, ikhandle_name)
        cmds.connectAttr(self.rig_attr, self.spring_ikhandle+".visibility")
        
        # ankle ik solver
        ikhandle_name = MayaName(self.midJoint)
        ikhandle_name.category = "Ikhandle"
        ikhandle_name.descriptor = ikhandle_name.descriptor
        
        (ikhandle, effector) = cmds.ikHandle(startJoint=self.midJoint, endEffector=self.ankleJoint, solver="ikRPsolver")
        self.ikhandle = cmds.rename(ikhandle, ikhandle_name)
        cmds.connectAttr(self.rig_attr, self.ikhandle+".visibility")
        
        # toe ik solver
        ikhandle_name = MayaName(self.endJoint)
        ikhandle_name.category = "Ikhandle"
        ikhandle_name.descriptor = ikhandle_name.descriptor
        
        (ikhandle, effector) = cmds.ikHandle(startJoint=self.ankleJoint, endEffector=self.endJoint, solver="ikRPsolver")
        self.toe_ik_handle = cmds.rename(ikhandle, ikhandle_name)
        cmds.connectAttr(self.rig_attr, self.toe_ik_handle+".visibility")
        
        cmds.poleVectorConstraint (self.pivot_ik.name, self.ikhandle, weight=1)
        cmds.poleVectorConstraint (self.pivot_ik.name, self.spring_ikhandle, weight=1)
        
        # Connect ik handles
        cmds.parent(self.ikhandle, self.spring_ikhandle)
        cmds.parent(self.spring_ikhandle, self.ik_end.name)
        cmds.parent(self.toe_ik_handle, self.ik_end.name)
        
        cmds.setAttr(self.ik_attr, self.defaultIk)
        
        cmds.connectAttr(self.ik_attr, self.ikhandle+".ikBlend")
        cmds.connectAttr(self.ik_attr, self.toe_ik_handle+".ikBlend")

        cmds.parent(self.spring_start, self.rig_dag)
        cmds.parentConstraint(self.spring_start, self.startIkOffset.zero)

        # drive start joint with spring chain
        start_parent_constraint = cmds.parentConstraint(self.startIkOffset.name, self.startJoint)[0]
        cmds.connectAttr(self.fk_attr, "{}.{}W0".format(start_parent_constraint, self.start_fk.name))
        cmds.connectAttr(self.ik_attr, "{}.{}W1".format(start_parent_constraint, self.startIkOffset.name))

        constraints_pylib.parentConstraintMaintainOffset(self.pins["start"], self.spring_start)

        # spring ik angle bias
        attribute_pylib.add(self.component_options+".angleBias", min=1.0, max=0.0, type="float")
        
        reverse_angleBias_name = MayaName(self.spring_ikhandle)
        reverse_angleBias_name.descriptor = reverse_angleBias_name.descriptor+"AngleBias"
        reverse_angleBias_name.category = "Plusminusaverage"
        
        reverse_angleBias = cmds.createNode("plusMinusAverage", name=reverse_angleBias_name)
        cmds.setAttr(reverse_angleBias+".input1D[0]", 1)
        cmds.setAttr(reverse_angleBias+".operation", 2)
        cmds.connectAttr(self.component_options+".angleBias", reverse_angleBias+".input1D[1]")
        cmds.connectAttr(reverse_angleBias+".output1D", self.spring_ikhandle+".springAngleBias[1].springAngleBias_FloatValue")
        cmds.connectAttr(self.component_options+".angleBias", self.spring_ikhandle+".springAngleBias[0].springAngleBias_FloatValue")        
        
        self.makeAutoPV(end=self.ankleJoint)
        
        
    def postbuild(self):
        super().postbuild()
        
    def mirror(self):
        original_side = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side = "Rt"
            mirrored_side = "Lf"
            

        newself = ThreeSegmentLimb(name=self.name.replace(original_side, mirrored_side))
        
        newself.startJoint = self.startJoint.replace(original_side, mirrored_side)
        newself.midJoint = self.midJoint.replace(original_side, mirrored_side)
        newself.hockJoint = self.hockJoint.replace(original_side, mirrored_side)
        newself.ankleJoint = self.ankleJoint.replace(original_side, mirrored_side)
        newself.endJoint = self.endJoint.replace(original_side, mirrored_side)
        if self.poleVectorTranslation:
            newself.poleVectorTranslation = [self.poleVectorTranslation[0] * -1, self.poleVectorTranslation[1], self.poleVectorTranslation[2]]
        else:
            newself.poleVectorTranslation = None
        newself.defaultIk = self.defaultIk
        newself.poleVectorMove = self.poleVectorMove
        newself.alignIkToWorld = self.alignIkToWorld
        newself.hingeControl = self.hingeControl
        
        newself.mirrored     = 1
        
        return newself
        
    def getExportJointDict(self):
        
        if self.hingeControl:
            pass
            
        else:
            self.export_joints[self.startJoint] = None
            self.export_joints[self.midJoint] = self.startJoint
            self.export_joints[self.hockJoint] = self.midJoint
            self.export_joints[self.ankleJoint] = self.hockJoint
            
            self.export_joints_start = [self.startJoint]
        
        self.export_joints_end = [self.endJoint]
        


class TwoSegmentLimb(Limb):
    ''' Two segments limb used for bipedal arms and legs '''
    
    def __init__(self, **kwargs):

        self.name = kwargs['name'] if 'name' in kwargs and kwargs['name'] is not None else "component"
        
        super().__init__(**kwargs)
        
        self.startJoint = kwargs['startJoint'] if 'startJoint' in kwargs and kwargs['startJoint'] is not None else "CnStartJnt"
        self.midJoint = kwargs['midJoint'] if 'midJoint' in kwargs and kwargs['midJoint'] is not None else "CnMidJnt"
        self.endJoint = kwargs['endJoint'] if 'endJoint' in kwargs and kwargs['endJoint'] is not None else "CnEndJnt"
        
        self.defaultIk = kwargs['defaultIk'] if 'defaultIk' in kwargs and kwargs['defaultIk'] is not None else 0
        self.poleVectorTranslation = kwargs['poleVectorTranslation'] if 'poleVectorTranslation' in kwargs and kwargs['poleVectorTranslation'] is not None else [0,0,0]
        self.zeroPoseRot = kwargs['zeroPoseRot'] if 'zeroPoseRot' in kwargs and kwargs['zeroPoseRot'] is not None else [0, 0, 0]
        self.benderStartUpVector = kwargs['benderStartUpVector'] if 'benderStartUpVector' in kwargs and kwargs['benderStartUpVector'] is not None else None
        self.benderMidUpVector = kwargs['benderMidUpVector'] if 'benderMidUpVector' in kwargs and kwargs['benderMidUpVector'] is not None else None
        
        self.lowerTwistJnt = ""
        self.lowerTwistAimVector = []
        self.lowerTwistUpVector = []

        self.ikRotationOrder = ""
        
        self.tweaks          = True
        
        # members
        self.start_fk       = ""
        self.mid_fk         = ""
        self.end_fk         = ""
        self.fk_offset      = ""

        self.fk_controls_dag = None
        self.ik_controls_dag = None
        
        self.component_options = ""
        
        self.fkroot        = ""
        self.auto_pv        = ""
        self.iksnap        = ""
                
        self.hinge_joints  = []
        self.hinge         = ""

        self.mirrored      = 0  
        
        self.pins = {"start":None}

    def prebuild(self):
        super().prebuild()
        
        
    def build(self):
        super().build()
        
        if self.benderStartUpVector == None:
            self.benderStartUpVector = self.benderUpVector

        if self.benderMidUpVector == None:
            self.benderMidUpVector = self.benderUpVector
            

        #### FK Rig ####
        fk_parent = self.fk_controls_dag

        if self.startFkOffset:
        
            ## Create start offset
            ctrl_name = MayaName(self.startJoint)
            ctrl_name.category = "Ctrl"
            ctrl_name.descriptor = ctrl_name.descriptor+"OffsetFk"
        
            self.fk_offset = Control( name=str(ctrl_name), 
                                          color=shape_pylib.getColorBySide(self.startJoint), 
                                          size=5, 
                                          shapeType="sphere", 
                                          depth=2,
                                          lockAndHide=["t","s","v"], 
                                          rotationOrder="zxy",
                                          parent=self.fk_controls_dag, 
                                          matrix=self.startJoint)
            self.registerControl(self.fk_offset)
            
            fk_parent = self.fk_offset.name

        ctrl_name = MayaName(self.startJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Fk"
        ctrl_name.category = "Ctrl"
        self.start_fk = Control( name=str(ctrl_name), 
                                color=shape_pylib.getColorBySide(self.startJoint), 
                                size=5, 
                                shapeType="cube", 
                                lockAndHide=["t","s","v"], 
                                parent=fk_parent, 
                                matrix=self.startJoint, 
                                shapeRotation=[0,0,90], 
                                rotationOrder=self.startJoint )
        self.registerControl(self.start_fk)

        self.start_fk_controls = []
        self.start_fk_controls.append(self.start_fk)

        if self.startGimbal:
            ctrl_name = MayaName(self.startJoint)
            ctrl_name.descriptor = ctrl_name.descriptor + "FkGimbal"
            ctrl_name.category = "Ctrl"
            self.start_fk_gimbal = Control( name=str(ctrl_name), 
                                          color=shape_pylib.getColorBySide(self.startJoint), 
                                          size=5, 
                                          shapeType="sphere", 
                                          lockAndHide=["t","s","v"], 
                                          parent=self.start_fk.name, 
                                          matrix=self.startJoint, 
                                          shapeRotation=[0,0,90], 
                                          rotationOrder=self.startJoint 
            )
            self.registerControl(self.start_fk_gimbal)
            self.start_fk_controls.append(self.start_fk_gimbal)
            
            attribute_pylib.add(self.start_fk.name+".gimbal")
            cmds.connectAttr(self.start_fk.name+".gimbal", self.start_fk_gimbal.shape+".visibility")

        ctrl_name = MayaName(self.midJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Fk"
        ctrl_name.category = "Ctrl"
        self.mid_fk = Control( name=str(ctrl_name), 
                              color=shape_pylib.getColorBySide(self.midJoint), 
                              size=5, 
                              shapeType="cube", 
                              lockAndHide=["t","s","v"], 
                              parent=self.start_fk_controls[-1].name, 
                              matrix=self.midJoint, 
                              shapeRotation=[0,0,90], 
                              rotationOrder=self.midJoint)
        self.registerControl(self.mid_fk)
        
        ctrl_name = MayaName(self.endJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Fk"
        ctrl_name.category = "Ctrl"
        self.end_fk = Control( name=str(ctrl_name), 
                              color=shape_pylib.getColorBySide(self.endJoint), 
                              size=5, shapeType="cube", 
                              lockAndHide=["t","s","v"], 
                              parent=self.mid_fk.name, 
                              matrix=self.endJoint, 
                              shapeRotation=[0,0,90], 
                              rotationOrder=self.endJoint)
        self.registerControl(self.end_fk)
        
        self.end_fk_controls = []
        self.end_fk_controls.append(self.end_fk)

        if self.endGimbal:
            ctrl_name = MayaName(self.endJoint)
            ctrl_name.descriptor = ctrl_name.descriptor + "FkGimbal"
            ctrl_name.category = "Ctrl"
            self.end_fk_gimbal = Control( name=str(ctrl_name), 
                                        color=shape_pylib.getColorBySide(self.endJoint), 
                                        size=5, 
                                        shapeType="sphere", 
                                        lockAndHide=["t","s","v"], 
                                        parent=self.end_fk.name, 
                                        matrix=self.endJoint, 
                                        shapeRotation=[0,0,90], 
                                        rotationOrder=self.endJoint 
            )
            self.registerControl(self.end_fk_gimbal)
            self.end_fk_controls.append(self.end_fk_gimbal)
            
            attribute_pylib.add(self.end_fk.name+".gimbal")
            cmds.connectAttr(self.end_fk.name+".gimbal", self.end_fk_gimbal.shape+".visibility")

        # Orient Constrain ctrls to joints
        cmds.orientConstraint(self.start_fk_controls[-1].name, self.startJoint)
        cmds.orientConstraint(self.mid_fk.name, self.midJoint)
        
        con, fk_end_hook = constraints_pylib.orientConstraintMaintainOffset(self.end_fk_controls[-1].name, self.endJoint)

        self.tagAsFKIKLimb(self.start_fk.name)
        self.tagAsFKIKLimb(self.mid_fk.name)
        self.tagAsFKIKLimb(self.end_fk.name)
        
        ## Bind Pose##
        if self.zeroPoseRot:
            if self.startFkOffset:
                self.start_fk_controls.insert(0, self.fk_offset)
                
            xform_pylib.alignRotation(self.start_fk_controls[0].zero, self.zeroPoseRot, ignoreChildren=True)
            for offset in self.start_fk_controls[0].offset_transforms:
                xform_pylib.alignRotation(offset, self.zeroPoseRot, ignoreChildren=True)
            
            rot = cmds.getAttr(self.start_fk_controls[0].name+".rotate")[0]
            attribute_pylib.add(self.start_fk_controls[0].name+".bindRotX", type="float", keyable=False, lock=0, max=None, min=None, value=rot[0])
            attribute_pylib.add(self.start_fk_controls[0].name+".bindRotY", type="float", keyable=False, lock=0, max=None, min=None, value=rot[1])
            attribute_pylib.add(self.start_fk_controls[0].name+".bindRotZ", type="float", keyable=False, lock=0, max=None, min=None, value=rot[2])

            # zero out the control to get world rotation of the subsequent controls
            cmds.setAttr(self.start_fk_controls[0].name+".rotate", 0, 0, 0, type="float3")
            
            # store rotation values for bind pose
            xform_pylib.alignRotation(self.mid_fk.zero, self.zeroPoseRot, ignoreChildren=True)
            for offset in self.mid_fk.offset_transforms:
                xform_pylib.alignRotation(offset, self.zeroPoseRot[1], ignoreChildren=True)
            
            rot = cmds.getAttr(self.mid_fk.name+".rotate")[0]
            attribute_pylib.add(self.mid_fk.name+".bindRotX", type="float", keyable=False, lock=0, max=None, min=None, value=rot[0])
            attribute_pylib.add(self.mid_fk.name+".bindRotY", type="float", keyable=False, lock=0, max=None, min=None, value=rot[1])
            attribute_pylib.add(self.mid_fk.name+".bindRotZ", type="float", keyable=False, lock=0, max=None, min=None, value=rot[2])

            # zero out the control to get world rotation of the subsequent controls
            cmds.setAttr(self.mid_fk.name+".rotate", 0, 0, 0, type="float3")

            # store rotation values for bind pose
            xform_pylib.alignRotation(self.end_fk.zero, self.zeroPoseRot, ignoreChildren=True)
            for offset in self.end_fk.offset_transforms:
                xform_pylib.alignRotation(offset, self.zeroPoseRot[2], ignoreChildren=True)
            
            
            rot = cmds.getAttr(self.end_fk.name+".rotate")[0]
            attribute_pylib.add(self.end_fk.name+".bindRotX", type="float", keyable=False, lock=0, max=None, min=None, value=rot[0])
            attribute_pylib.add(self.end_fk.name+".bindRotY", type="float", keyable=False, lock=0, max=None, min=None, value=rot[1])
            attribute_pylib.add(self.end_fk.name+".bindRotZ", type="float", keyable=False, lock=0, max=None, min=None, value=rot[2])
            
            cmds.setAttr(self.end_fk.name+".rotate", 0, 0, 0, type="float3")


        #### IK Rig #####
        ik_transform = Transform()
        ik_transform.setTranslation(cmds.xform(self.endJoint, translation=True, worldSpace=True, query=True))
        
        # ik pv control
        pv_transform = Transform()
        pv_transform.setTranslation(cmds.xform(self.midJoint, translation=True, query=True, worldSpace=True))
        
        if self.poleVectorTranslation and self.poleVectorTranslation != [0,0,0]:
            pv_transform = Transform()
            pv_transform.translate(self.poleVectorTranslation)

        if self.poleVectorMove:
            v = Vector(self.poleVectorMove)
            pv_transform.translate(v)

        # ik control
        ctrl_name = MayaName(self.endJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Ik"
        ctrl_name.category = "Ctrl"
        
        self.ik = Control( name=str(ctrl_name), 
                           color=shape_pylib.getColorBySide(self.startJoint), 
                           size=5, 
                           shapeType="cube", 
                           lockAndHide=["s","v"],
                           parent=self.ik_controls_dag,
                           depth=2,
                           matrix=ik_transform,
                           shapeRotation=[0,0,90],
                           rotationOrder=self.ikRotationOrder,
                           thickness=3
        )
        self.registerControl(self.ik)
        
        self.end_ik_controls = []
        self.end_ik_controls.append(self.ik)

        if self.endGimbal:
            ctrl_name = MayaName(self.endJoint)
            ctrl_name.descriptor = ctrl_name.descriptor + "IkGimbal"
            ctrl_name.category = "Ctrl"
            self.end_ik_gimbal = Control( name=str(ctrl_name), 
                                        color=shape_pylib.getColorBySide(self.endJoint), 
                                        size=5, 
                                        shapeType="sphere", 
                                        lockAndHide=["s","v"], 
                                        parent=self.ik.name,
                                        matrix=self.endJoint, 
                                        shapeRotation=[0,0,90], 
                                        rotationOrder=self.ikRotationOrder
            )
            self.registerControl(self.end_ik_gimbal)
            
            # align with ik control
            cmds.setAttr(self.end_ik_gimbal.zero+".t", 0, 0, 0)
            cmds.setAttr(self.end_ik_gimbal.zero+".r", 0, 0, 0)
            
            self.end_ik_controls.append(self.end_ik_gimbal)
            
            attribute_pylib.add(self.ik.name+".gimbal")
            cmds.connectAttr(self.ik.name+".gimbal", self.end_ik_gimbal.shape+".visibility")        
        
        
        ctrl_name = MayaName(self.midJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Pv"
        ctrl_name.category = "Ctrl"
        
        self.pivot_ik = Control( name=str(ctrl_name), 
                                color=shape_pylib.getColorBySide(self.midJoint),
                                size=1, 
                                shapeType="turtle", 
                                lockAndHide=["r","s","v"], 
                                parent=self.ik_controls_dag, 
                                matrix=pv_transform,
                                shapeRotation=[0,0,0], 
                                depth=2
        )
        self.registerControl(self.pivot_ik)
        
        # hack for transform bug for now
        if ("Rt" in self.name) and (self.poleVectorTranslation != [0,0,0]):
            cmds.setAttr(self.pivot_ik.zero+".translate", self.poleVectorTranslation[0], self.poleVectorTranslation[1], self.poleVectorTranslation[2], type="float3")
            
        # Make IK snap parent for ik/fk switching
        snap_name = MayaName(self.endJoint)
        snap_name.descriptor = snap_name.descriptor + "IKSnap"
        snap_name.category = "Null"
        
        self.iksnap = cmds.createNode("transform", n=snap_name, parent=self.end_fk.name)
        cmds.setAttr(self.iksnap+".visibility", False)
        xform_pylib.align(self.iksnap, self.ik.name)
    
        # Lower twist joint
        if self.lowerTwistJnt and cmds.objExists(self.lowerTwistJnt):

            twist_null_name = MayaName(self.lowerTwistJnt)
            twist_null_name.category = "Null"
            twist_null = mayatransform_pylib.createLocator(name=twist_null_name, parent=self.midJoint, matrix=self.lowerTwistJnt)
            cmds.connectAttr(self.rig_attr, twist_null+".visibility")
            
            # up vector
            uptwist_transform = Transform(self.endJoint)
            twist_translation = Vector(self.lowerTwistUpVector) * cmds.getAttr(self.midJoint+".translate"+self.aimAxis)
            uptwist_transform.translate(twist_translation)
            
            up_vector_name = MayaName(self.lowerTwistJnt)
            up_vector_name.descriptor = up_vector_name.descriptor + "Pv"
            up_vector_name.category = "Ctrl"
            
            self.upVector_twist = Control( name=str(up_vector_name), 
                                           color=shape_pylib.getColorBySide(self.lowerTwistJnt), 
                                           size=1, 
                                           shapeType="turtle", 
                                           lockAndHide=["r","s"], 
                                           parent=self.controls_dag, 
                                           matrix=uptwist_transform, 
                                           shapeRotation=[-90,0,0], 
                                           depth=2
            )
            self.registerControl(self.upVector_twist)

            cmds.parentConstraint(self.endJoint, self.upVector_twist.zero, maintainOffset=True)
            
            upVector_visibility_attr = self.component_options + ".showUpVectors" 
            attribute_pylib.add(upVector_visibility_attr)
            
            cmds.connectAttr(upVector_visibility_attr, self.upVector_twist.name+".visibility")
            
            cmds.aimConstraint(self.endJoint, twist_null, aimVector=self.lowerTwistAimVector, upVector=self.lowerTwistUpVector, worldUpType="object", worldUpObject=self.upVector_twist.name)
            
            # 50% of the wrist twist
            twist_null_name.category = "MultipyDivide"
            percentage_md = cmds.createNode("multiplyDivide", name=twist_null_name)
            
            axis = "x"
            if self.lowerTwistAimVector[1]:
                axis = "y"
            if self.lowerTwistAimVector[2]:
                axis = "z"
                
            cmds.connectAttr(twist_null+".r"+axis, percentage_md+".input1X")
            cmds.connectAttr(percentage_md+".outputX", self.lowerTwistJnt+".r"+axis)

        # Pin start fk_offset
        constraints_pylib.parentConstraintMaintainOffset(self.pins["start"], self.start_fk_controls[0].zero)
        # constraints_pylib.offsetParentMatrixConstraint(self.pins["start"], self.start_fk_controls[0].zero, alignTo="child")
        
        # track the start, mid, and end for ikstretch and hinge controls to account for rig scale
        # Create transforms for static measurement 
        static_start_name = MayaName(self.startJoint)
        static_start_name.descriptor = static_start_name.descriptor + "StaticStart"
        static_start_name.category = "Null"
        static_start = cmds.createNode("transform", name=static_start_name, parent=self.rig_dag)
        xform_pylib.align(static_start, self.startJoint)

        static_start_name.category = "DecomposeMatrix"
        self.static_start_dm = cmds.createNode("decomposeMatrix",  n=static_start_name)
        cmds.connectAttr(static_start + ".worldMatrix", self.static_start_dm+".inputMatrix")

        static_mid_name = MayaName(self.midJoint)
        static_mid_name.descriptor = static_mid_name.descriptor + "StaticMid"
        static_mid_name.category = "Null"
        static_mid = cmds.createNode("transform", name=static_mid_name, parent=self.rig_dag)
        xform_pylib.align(static_mid, self.midJoint)

        static_mid_name.category = "DecomposeMatrix"
        self.static_mid_dm = cmds.createNode("decomposeMatrix",  n=static_mid_name)
        cmds.connectAttr(static_mid+".worldMatrix", self.static_mid_dm+".inputMatrix")

        static_end_name = MayaName(self.endJoint)
        static_end_name.descriptor = static_end_name.descriptor + "StaticEnd"
        static_end_name.category = "Null"
        static_end = cmds.createNode("transform", name=static_end_name, parent=self.rig_dag)
        xform_pylib.align(static_end, self.endJoint)

        static_end_name.category = "DecomposeMatrix"
        self.static_end_dm = cmds.createNode("decomposeMatrix",  n=static_end_name)
        cmds.connectAttr(static_end+".worldMatrix", self.static_end_dm+".inputMatrix")
        
        # set up ik stretch in T pose
        self.addStretch()
        
        # Go to bind pose
        self.start_fk_controls[0].goToBindPose()
        self.mid_fk.goToBindPose()
        self.end_fk.goToBindPose()
        
        # ik zero pose
        xform_pylib.align(self.ik.name, self.iksnap)
        
        if self.zeroPoseRot:
            # Create Zero Pose for the IK target
            pos = cmds.getAttr(self.ik.name+".translate")[0]
            rot = cmds.getAttr(self.ik.name+".rotate")[0]

            attribute_pylib.add(self.ik.name+".bindPosX", type="float", keyable=False, lock=0, max=None, min=None, value=pos[0])
            attribute_pylib.add(self.ik.name+".bindPosY", type="float", keyable=False, lock=0, max=None, min=None, value=pos[1])
            attribute_pylib.add(self.ik.name+".bindPosZ", type="float", keyable=False, lock=0, max=None, min=None, value=pos[2])
            attribute_pylib.add(self.ik.name+".bindRotX", type="float", keyable=False, lock=0, max=None, min=None, value=rot[0])
            attribute_pylib.add(self.ik.name+".bindRotY", type="float", keyable=False, lock=0, max=None, min=None, value=rot[1])
            attribute_pylib.add(self.ik.name+".bindRotZ", type="float", keyable=False, lock=0, max=None, min=None, value=rot[2])
        
            # ik pv control
            pv_transform = Transform()
            pv_transform.setTranslation(cmds.xform(self.midJoint, translation=True, query=True, worldSpace=True))
            
            if self.poleVectorTranslation and self.poleVectorTranslation != [0,0,0]:
                pv_transform = Transform()
                pv_transform.setTranslation(self.poleVectorTranslation)

            if self.poleVectorMove:
                v = Vector(self.poleVectorMove)
                pv_transform.translate(v)
            

            xform_pylib.alignPosition(self.pivot_ik.name, pv_transform.getTranslation(), ignoreChildren=True)
        
            # Create Zero Pose for the IK target
            pos = cmds.getAttr(self.pivot_ik.name+".translate")[0]
            rot = cmds.getAttr(self.pivot_ik.name+".rotate")[0]

            attribute_pylib.add(self.pivot_ik.name+".bindPosX", type="float", keyable=False, lock=0, max=None, min=None, value=pos[0])
            attribute_pylib.add(self.pivot_ik.name+".bindPosY", type="float", keyable=False, lock=0, max=None, min=None, value=pos[1])
            attribute_pylib.add(self.pivot_ik.name+".bindPosZ", type="float", keyable=False, lock=0, max=None, min=None, value=pos[2])
            attribute_pylib.add(self.pivot_ik.name+".bindRotX", type="float", keyable=False, lock=0, max=None, min=None, value=rot[0])
            attribute_pylib.add(self.pivot_ik.name+".bindRotY", type="float", keyable=False, lock=0, max=None, min=None, value=rot[1])
            attribute_pylib.add(self.pivot_ik.name+".bindRotZ", type="float", keyable=False, lock=0, max=None, min=None, value=rot[2])

        # Make FK snap parent for fk/ik switching
        snap_name = MayaName(self.endJoint)
        snap_name.descriptor = snap_name.descriptor + "FKSnap"
        snap_name.category = "Null"
        
        self.fk_snap = cmds.createNode("transform", n=snap_name, parent=self.ik.name)
        cmds.setAttr(self.fk_snap+".visibility", False)
        xform_pylib.align(self.fk_snap, self.end_fk.name)
        
        self.tagAsFKIKLimb(self.ik.name)
        self.tagAsFKIKLimb(self.pivot_ik.name)
        
        # Create the IK
        (self.ikhandle, self.effector) = cmds.ikHandle(startJoint=self.startJoint, endEffector=self.endJoint, solver="ikRPsolver")
        ik_name = MayaName(self.name)
        ik_name.category = "Ikhandle"
        
        self.ikhandle = cmds.rename(self.ikhandle, str(ik_name))
        ik_name.category = "Effector"
        self.effector = cmds.rename(self.effector, str(ik_name))
        
        cmds.connectAttr(self.rig_attr, self.ikhandle+".visibility")
        cmds.connectAttr(self.rig_attr,  self.effector+".visibility")

        ## IK ##
        self.addSwitchDataIK(self.ik.name)
        self.addSwitchDataIK(self.pivot_ik.name)
        
        ## FK ##
        self.addSwitchDataFK(self.start_fk.name)
        self.addSwitchDataFK(self.mid_fk.name)
        self.addSwitchDataFK(self.end_fk.name)
        
        cmds.setAttr(self.ik_attr, self.defaultIk)
        cmds.connectAttr(self.ik_attr, self.ikhandle+".ikBlend")
        
        # snap the IK to the FK
        if not self.alignIkToWorld:
            xform_pylib.align(self.ik.zero, self.endJoint)
            xform_pylib.align(self.fk_snap, self.endJoint)
            xform_pylib.align(self.pivot_ik.zero, self.midJoint)

        # Constrain Pole Vector, IKHandle, orientation
        cmds.poleVectorConstraint (self.pivot_ik.name, self.ikhandle, weight=1)
        
        # use MO constraint 
        endJoint_constraint, ik_end_hook = constraints_pylib.orientConstraintMaintainOffset(self.end_ik_controls[-1].name, self.endJoint)
        cmds.setAttr(endJoint_constraint+".interpType", 2)
        
        # hook up fk/ik switch to rotation of end joint.
        cmds.connectAttr(self.fk_attr, endJoint_constraint+"."+fk_end_hook+"W0")
        cmds.connectAttr(self.ik_attr, endJoint_constraint+"."+ik_end_hook+"W1")

        cmds.parent(self.ikhandle, self.end_ik_controls[-1].name)
        
        # Add an IK control at hinge
        if self.hingeControl:
            self.createHingeControl()
            
        if self.benderControls:
        
            self.upper_bender_joints = self.createBenderJoints(self.startJoint, self.midJoint)
            self.lower_bender_joints = self.createBenderJoints(self.midJoint, self.endJoint)

            bender_start_joint = self.startJoint
            bender_mid_joint = self.midJoint
            
            start_descriptor = (MayaName(self.startJoint)).descriptor
            mid_descriptor = (MayaName(self.midJoint)).descriptor
            
            if self.hingeControl:
                bender_start_joint = self.hinge_joints[0]
                bender_mid_joint = self.hinge_joints[2]
            
            cmds.parent(self.upper_bender_joints[0], bender_start_joint)
            cmds.parent(self.lower_bender_joints[0], bender_mid_joint)
                
            controls, ups, curve = self.createBenderControls( bender_start_joint, 
                                                              bender_mid_joint, 
                                                              self.upper_bender_joints, 
                                                              3, 
                                                              start_descriptor, 
                                                              upVector=self.benderStartUpVector
            )
            self.upper_bender_controls = controls
            self.upper_bender_up_controls = ups
            self.upper_bender_curve = curve
            
            controls, ups, curve = self.createBenderControls( bender_mid_joint, 
                                                              self.endJoint, 
                                                              self.lower_bender_joints, 
                                                              3, 
                                                              mid_descriptor,
                                                              upVector=self.benderMidUpVector,
                                                              upVectorShape="circle"
            )
            
            self.lower_bender_controls = controls
            self.lower_bender_up_controls = ups
            self.lower_bender_curve = curve
            
            # Make one bendy for the middle

            # auto determine the shape rotation
            if self.aimAxis == "X":
                shapeRotation = Vector([0, 0, -90]) * self.aim_coefficient
            elif self.aimAxis == "Z":
                shapeRotation = Vector([90, 0, 0]) * self.aim_coefficient
            else:
                if self.aim_coefficient == 1:
                    shapeRotation = Vector([0, 0, 0])
                else:
                    shapeRotation = Vector([0, 0, 180])            
            
            control_name = MayaName(self.midJoint)
            control_name.descriptor += "Bender"
            control_name.category = "Ctrl"

            self.middle_bender_control = Control( name=control_name, 
                                                  color=shape_pylib.getRgbBySide(self.startJoint, alternate=True), 
                                                  size=8, 
                                                  shapeType="shell", 
                                                  lockAndHide=["s"], 
                                                  rotationOrder="xyz",
                                                  shapeRotation=list(shapeRotation),
                                                  depth=1,
                                                  type="transform",
                                                  parent=self.controls_dag,
                                                  matrix=self.midJoint
            )
            self.registerControl(self.middle_bender_control)

            cmds.parentConstraint(bender_mid_joint, self.middle_bender_control.zero, maintainOffset=True)
            
            # add an offset and constrain the end and start benders
            transform = self.upper_bender_controls[-1].addTransformOffset()
            cmds.setAttr(transform+".visibility", False, lock=True)
            cmds.pointConstraint(self.middle_bender_control.name, transform)

            transform = self.lower_bender_controls[0].addTransformOffset()
            cmds.setAttr(transform+".visibility", False, lock=True)
            cmds.parentConstraint(self.middle_bender_control.name, transform, maintainOffset=True)
            
            # visibility attrs
            attribute_pylib.add(self.component_options+".benders")
            for control in (self.upper_bender_controls + self.lower_bender_controls):
                cmds.connectAttr(self.component_options+".benders", control.name + ".visibility")
                
            cmds.connectAttr(self.component_options+".benders", self.middle_bender_control.name+".visibility")
            
            attribute_pylib.add(self.component_options+".bendersStartUp")
            for control in (self.upper_bender_up_controls):
                cmds.connectAttr(self.component_options+".bendersStartUp", control.name + ".visibility")

            attribute_pylib.add(self.component_options+".bendersMidUp")
            for control in (self.lower_bender_up_controls):
                cmds.connectAttr(self.component_options+".bendersMidUp", control.name + ".visibility")

        # auto pole vector
        self.makeAutoPV()
        

    def postbuild(self):
        super().postbuild()        
        
        # bind joints are used for making bind sets.  If a bind joint doesnt exist, the system uses the export_joints dict
        self.bind_joints = []
        if self.benderControls:
            self.bind_joints.append(self.upper_bender_joints[0]) 
            self.bind_joints.append(self.upper_bender_joints[1]) 
            self.bind_joints.append(self.upper_bender_joints[2]) 
            
            self.bind_joints.append(self.lower_bender_joints[0]) 
            self.bind_joints.append(self.lower_bender_joints[1]) 
            self.bind_joints.append(self.lower_bender_joints[2]) 

            self.bind_joints.append(self.endJoint)
            
        elif self.hingeControl:
            self.bind_joints = [self.hinge_joints[0], self.hinge_joints[2]]
            self.bind_joints.append(self.endJoint)
            
        else:
            self.bind_joints = [self.startJoint, self.midJoint, self.endJoint]

    
    def addStretch(self):
        ''' Add measurements and scale joints according to the default length. '''
        
        # attributes
        ik_stretch_attr = attribute_pylib.add(self.component_options+".ikstretch")
        ikstretch_point_attr = attribute_pylib.add(self.component_options+".ikstretchPoint", type="float", min=0.0, max=None, value=1.0)
        
        # Measure the distance of a straight limb with the end to account for rig scale
        static_distance_name = MayaName(self.ik.name)
        static_distance_name.descriptor = static_distance_name.descriptor + "Static"
        static_distance_name.category = "DistanceDimension"
        static_distance = cmds.createNode("distanceDimShape", n=str(static_distance_name)+"Shape")
        cmds.rename(cmds.listRelatives(static_distance, parent=True)[0], static_distance_name)

        cmds.connectAttr(self.static_start_dm+".outputTranslate", static_distance+".startPoint")
        cmds.connectAttr(self.static_end_dm+".outputTranslate", static_distance+".endPoint" )
        
        cmds.parent( cmds.listRelatives(static_distance, parent=True)[0], self.rig_dag )

        # Measure distance of a straight limb with the end driven by the IK ctrl
        distance_name = MayaName(self.ik.name)
        distance_name.category = "DistanceDimension"
        distance = cmds.createNode("distanceDimShape", n=str(distance_name)+"Shape")
        cmds.rename(cmds.listRelatives(distance, parent=True)[0], distance_name)
        
        decompose_start_name = MayaName(self.pins["start"])
        decompose_start_name.descriptor = decompose_start_name.descriptor + "StartStretch"
        decompose_start_name.category = "DecomposeMatrix"
        decompose_start = cmds.createNode("decomposeMatrix",  n=decompose_start_name)
        
        # ikhandle hasnt been created yet, so make a transform to constrain later.
        end_stretch_name = MayaName(self.ik.name)
        end_stretch_name.descriptor = end_stretch_name.descriptor + "EndStretch"
        end_stretch_name.category = "Null"
        self.end_stretch_transform = mayatransform_pylib.createLocator(name=end_stretch_name, parent=self.rig_dag, matrix=self.ik.name)
        
        decompose_end_name = MayaName(self.ik.name)
        decompose_end_name.descriptor = decompose_end_name.descriptor + "EndStretch"
        decompose_end_name.category = "DecomposeMatrix"
        
        decompose_end = cmds.createNode("decomposeMatrix",  n=decompose_end_name)
        
        cmds.parent( cmds.listRelatives(distance, parent=True)[0], self.rig_dag )
        
        cmds.connectAttr(self.pins["start"] + ".worldMatrix", decompose_start+".inputMatrix")
        cmds.connectAttr(self.end_stretch_transform+".worldMatrix", decompose_end+".inputMatrix" )
        
        cmds.connectAttr(decompose_start+".outputTranslate", distance+".startPoint")
        cmds.connectAttr(decompose_end+".outputTranslate", distance+".endPoint" )
        
        # Stretch Point Multiplier
        stretch_point_md_name = MayaName(self.ik.name)
        stretch_point_md_name.descriptor += "StretchPoint"
        stretch_point_md_name.category = "MultiplyDivide"
        stretch_point_md = cmds.createNode("multiplyDivide", n=stretch_point_md_name)

        # Divide the distance with its current value
        # Stretch
        stretch_ratio_md_name = MayaName(self.ik.name)
        stretch_ratio_md_name.descriptor += "StretchRatio"
        stretch_ratio_md_name.category = "MultiplyDivide"

        stretch_ratio_md = cmds.createNode("multiplyDivide", n=stretch_ratio_md_name)
        cmds.setAttr(stretch_ratio_md+".operation", 2)

        cmds.connectAttr(stretch_point_md+".outputX", stretch_ratio_md+".input1X")
        cmds.connectAttr(static_distance+".distance", stretch_ratio_md+".input2X")

        # Compress
        compress_ratio_md_name = MayaName(self.ik.name)
        compress_ratio_md_name.descriptor += "CompressRatio"
        compress_ratio_md_name.category = "MultiplyDivide"

        compress_ratio_md = cmds.createNode("multiplyDivide", n=compress_ratio_md_name)
        cmds.setAttr(compress_ratio_md+".operation", 2)

        cmds.connectAttr(stretch_point_md+".outputX", compress_ratio_md+".input1X")
        cmds.connectAttr(distance+".distance", compress_ratio_md+".input2X")
        
        # compress condition
        compress_condition_name = MayaName(self.ik.name)
        compress_condition_name.descriptor = compress_condition_name.descriptor + "Compress"
        compress_condition_name.category = "Condition"
        compress_condition = cmds.createNode("condition", n=compress_condition_name)
        cmds.setAttr(compress_condition+".operation", 4) # Less than

        cmds.connectAttr(distance+".distance", compress_condition+".firstTerm")
        cmds.setAttr(compress_condition+".secondTerm", cmds.getAttr(distance+".distance"))
        cmds.connectAttr(stretch_ratio_md+".outputX", compress_condition+".colorIfFalseR")
        cmds.connectAttr(compress_ratio_md+".outputX", compress_condition+".colorIfTrueR")
        
        cmds.connectAttr(ikstretch_point_attr, stretch_point_md+".input1X")
        cmds.connectAttr(distance+".distance", stretch_point_md+".input2X")
        
        # Switch for turning on and off IKStretch
        stretchswitch_condition_name = MayaName(self.ik.name)
        stretchswitch_condition_name.descriptor += "StretchSwitch"
        stretchswitch_condition_name.category = "Condition"
        stretchswitch_condition = cmds.createNode("condition", n=stretchswitch_condition_name)
        cmds.connectAttr(compress_condition+".outColorR",  stretchswitch_condition+".colorIfTrueR")
        cmds.setAttr(stretchswitch_condition+".secondTerm", 1)

        fkswitch_condition_name = MayaName(self.ik.name)
        fkswitch_condition_name.descriptor += "FkSwitchStretch"
        fkswitch_condition_name.category = "Condition"
        fkswitch_condition = cmds.createNode("condition", n=fkswitch_condition_name)
        cmds.setAttr(fkswitch_condition+".secondTerm", 1)
        
        # Hook up stretch switch
        cmds.connectAttr( ik_stretch_attr, stretchswitch_condition+".ft")        

        # Hook up fk/ik switch
        cmds.connectAttr( self.ik_attr, fkswitch_condition+".ft")
        cmds.connectAttr( stretchswitch_condition+".outColorR", fkswitch_condition+".colorIfTrueR" )
        
        upper_distance_md_name = MayaName(self.ik.name)
        upper_distance_md_name.descriptor += "UpperDistance"
        upper_distance_md_name.category = "Multiplydivide"
        upper_distance_md = cmds.createNode("multiplyDivide", name=upper_distance_md_name)
        
        # Add a stretch attr
        attribute_pylib.add(self.component_options+".midStretch", max=None, min=None, type="float")
        
        # Connect attr to fk translation
        fk_offset = self.mid_fk.addTransformOffset()
        cmds.connectAttr(self.component_options+".midStretch", "{}.translate{}".format(fk_offset, self.aimAxis))
        
        mid_stretch_pm_name = MayaName(self.midJoint)
        mid_stretch_pm_name.descriptor += "AttrStretch"
        mid_stretch_pm_name.category = "Plusminusaverage"
        
        mid_stretch_pm = cmds.createNode("plusMinusAverage", name=mid_stretch_pm_name)
        
        cmds.connectAttr(upper_distance_md+".outputX", mid_stretch_pm+".input1D[0]")
        cmds.connectAttr(self.component_options+".midStretch", mid_stretch_pm+".input1D[1]")        
        
        cmds.connectAttr(fkswitch_condition+".outColorR", upper_distance_md+".input1X")
        cmds.setAttr(upper_distance_md+".input2X", cmds.getAttr(self.midJoint+".translate"+self.aimAxis))
        cmds.connectAttr(mid_stretch_pm+".output1D", self.midJoint+".translate"+self.aimAxis)

        lower_distance_md_name = MayaName(self.ik.name)
        lower_distance_md_name.descriptor += "LowerDistance"
        lower_distance_md_name.category = "Multiplydivide"
        lower_distance_md = cmds.createNode("multiplyDivide", name=lower_distance_md_name)


        # Add a stretch attr
        attribute_pylib.add(self.component_options+".endStretch", max=None, min=None, type="float")
        
        # Connect attr to fk translation
        fk_offset = self.end_fk.addTransformOffset()
        cmds.connectAttr(self.component_options+".endStretch", "{}.translate{}".format(fk_offset, self.aimAxis))        
        
        end_stretch_pm_name = MayaName(self.endJoint)
        end_stretch_pm_name.descriptor += "AttrStretch"
        end_stretch_pm_name.category = "Plusminusaverage"
        
        end_stretch_pm = cmds.createNode("plusMinusAverage", name=end_stretch_pm_name)
        
        cmds.connectAttr(lower_distance_md+".outputX", end_stretch_pm+".input1D[0]")
        cmds.connectAttr(self.component_options+".endStretch", end_stretch_pm+".input1D[1]")
        
        cmds.connectAttr(fkswitch_condition+".outColorR", lower_distance_md+".input1X")
        cmds.setAttr(lower_distance_md+".input2X", cmds.getAttr(self.endJoint+".translate"+self.aimAxis))
        cmds.connectAttr(end_stretch_pm+".output1D", self.endJoint+".translate"+self.aimAxis)

        
    def createHingeControl(self):
        ''' This will add a ctrl to the limb that will stretch the limb from the middle.  Used for fixing knee pops. '''

        rig_grp_name = MayaName(self.rig_dag)
        rig_grp_name.descriptor = rig_grp_name.descriptor + "Hinge"
        riggrp = cmds.createNode("transform", n=rig_grp_name, parent=self.rig_dag)

        midTransform = Transform(self.midJoint)

        # Add vis attr
        visibility_attr = self.component_options + ".hinge"

        if not cmds.objExists(visibility_attr):
            cmds.addAttr(self.component_options, ln="hinge", at="long", min=0, max=1, dv=0, s=True, k=True)

        # Create mid ctrl
        ctrl_name = MayaName(self.midJoint)
        ctrl_name.descriptor = ctrl_name.descriptor + "Hinge"
        ctrl_name.category = "Ctrl"
        
        self.hinge = Control( name=str(ctrl_name), 
                              color=shape_pylib.getColorBySide(self.startJoint), 
                              size=5, 
                              shapeType="circle", 
                              lockAndHide=["r","s"], 
                              parent=self.controls_dag, 
                              matrix=self.midJoint, 
                              shapeRotation=[0,0,90], 
                              thickness=2.0
        )
        self.registerControl(self.hinge)

        cmds.connectAttr(visibility_attr, self.hinge.name + ".visibility")
        cmds.pointConstraint(self.midJoint, cmds.listRelatives(self.hinge.name, parent=True))
        cmds.orientConstraint(self.startJoint, cmds.listRelatives(self.hinge.name, parent=True))
        ocon = cmds.orientConstraint(self.midJoint, cmds.listRelatives(self.hinge.name, parent=True))[0]
        cmds.setAttr(ocon+".interpType", 2)
        
        # # Joint creation and setup ##
        # 0 is the upper joint and 1 is the lower jnt
        aim_targets = []
        startdms = []
        enddms = []

        joint_chain = [self.startJoint, self.midJoint, self.endJoint]
        decompose_chain = [self.static_start_dm, self.static_mid_dm, self.static_end_dm]
        
        for ii in range(2):
            start_joint = None
            end_joint = None
            
            # Create Joints
            if len(self.hinge_joints) <= 2:
                hingeJoints = self.createHingeJoints(joint_chain[ii], joint_chain[ii+1])
                
                hinge_start_joint = hingeJoints[0]
                hinge_end_joint = hingeJoints[1]
                
                start_dm = decompose_chain[ii]
                end_dm = decompose_chain[ii+1]
                
                cmds.parent(hinge_start_joint, joint_chain[ii])

                self.hinge_joints += hingeJoints
            else:
                hinge_start_joint = self.hinge_joints[0 + 2 * ii]
                hinge_end_joint = self.hinge_joints[1 + 2 * ii]

                start_dm = decompose_chain[0 + 2 * ii]
                end_dm = decompose_chain[1 + 2 * ii]
            
            length = cmds.getAttr(hinge_end_joint + ".translate" + self.aimAxis)
            
            # create measurements for length in order to account for scale
            static_distance_name = MayaName(hinge_start_joint)
            static_distance_name.descriptor = static_distance_name.descriptor + "Static"
            static_distance_name.category = "DistanceDimension"
            
            static_distance = cmds.createNode("distanceDimShape", n=str(static_distance_name)+"Shape")
            cmds.rename(cmds.listRelatives(static_distance, parent=True)[0], static_distance_name)
            
            cmds.connectAttr(start_dm+".outputTranslate", static_distance+".startPoint")
            cmds.connectAttr(end_dm+".outputTranslate", static_distance+".endPoint" )
            
            cmds.parent(cmds.listRelatives(static_distance, parent=True)[0], self.rig_dag)
            
            # using an aim constraint because I cant figure out which vector the poleVectorConstraint chooses.
            aim_target_name = MayaName(hinge_start_joint)
            aim_target_name.descriptor = aim_target_name.descriptor + "Aim"
            aim_target_name.category = "Null"

            aim_target = mayatransform_pylib.createLocator(name=aim_target_name, parent=joint_chain[ii+1], matrix=joint_chain[ii+1])
            cmds.connectAttr(self.rig_attr, aim_target+".visibility")
            
            aim_targets.append(aim_target)
        
            # up vector
            up_target_name = MayaName(hinge_start_joint)
            up_target_name.descriptor = up_target_name.descriptor + "Up"
            up_target_name.category = "Null"

            up_target = mayatransform_pylib.createLocator(name=up_target_name)
            cmds.connectAttr(self.rig_attr, up_target + ".visibility")

            # Place the pv
            cmds.parent(up_target, hinge_start_joint)
            cmds.setAttr(up_target+".translate", 0, 0, 0, type="float3")
            cmds.setAttr(up_target+".translate" + self.upAxis, length * self.aim_coefficient)
            cmds.setAttr(up_target+".rotate", 0, 0, 0, type="float3")

            cmds.parent(up_target, joint_chain[ii])
            
            cmds.aimConstraint(aim_target, hinge_start_joint, aimVector=list(self.aimVector), upVector=list(self.upVector), worldUpType="object", worldUpObject=up_target)
            
            ## Measure the length and put it into the x of the end joint ##
            # Get world space
            math_name = MayaName(joint_chain[ii])
            math_name.descriptor = math_name.descriptor + "Start"
            math_name.category = "DecomposeMatrix"
            startdm = cmds.createNode("decomposeMatrix", n=math_name)
            startdms.append(startdm)
            
            math_name = MayaName(joint_chain[ii])
            math_name.descriptor = math_name.descriptor + "End"
            math_name.category = "DecomposeMatrix"
            enddm = cmds.createNode("decomposeMatrix", n=math_name)
            enddms.append(enddm)

            measure_name = aim_target_name
            measure_name.category = "DistanceDimension"
            measure = cmds.createNode("distanceDimShape", n=str(measure_name)+"Shape")
            mnode = cmds.rename(cmds.listRelatives(measure, parent=True)[0], measure_name)
            cmds.setAttr(mnode + ".v", l=False)
            cmds.parent(mnode, riggrp)

            # Measure distance
            cmds.connectAttr(startdm + ".outputTranslate", measure + ".startPoint")
            cmds.connectAttr(enddm + ".outputTranslate", measure + ".endPoint")
            
            # divide the changing by its current length.
            ratio_md_name = aim_target_name
            ratio_md_name.descriptor = ratio_md_name.descriptor + "Ratio"
            ratio_md_name.category = "MuliplyDivide"
            
            ratio_md = cmds.createNode("multiplyDivide", n=ratio_md_name)
            cmds.setAttr(ratio_md+".operation", 2)
            cmds.connectAttr(static_distance+".distance", ratio_md+".input2X")
            cmds.connectAttr(measure + ".distance", ratio_md + ".input1X")
            
            # Zero out hinge_end_joint non-aim translation to avoid upvector issues
            if self.aimVector.x == 0:
                cmds.setAttr(hinge_end_joint + ".translateX", 0)

            if self.aimVector.y == 0:
                cmds.setAttr(hinge_end_joint + ".translateY", 0)

            if self.aimVector.z == 0:
                cmds.setAttr(hinge_end_joint + ".translateZ", 0)
            
            # Plug into the joints scale
            cmds.connectAttr(ratio_md + ".outputX", hinge_start_joint + ".scale" + self.aimAxis)

        
        # Hook up measuring for stretch
        cmds.connectAttr(self.startJoint + ".worldMatrix", startdms[0] + ".inputMatrix")
        cmds.connectAttr(self.hinge.name + ".worldMatrix", enddms[0] + ".inputMatrix")

        cmds.connectAttr(self.hinge.name + ".worldMatrix", startdms[1] + ".inputMatrix")
        cmds.connectAttr(self.endJoint + ".worldMatrix", enddms[1] + ".inputMatrix")

        # Constrain newly created joints
        cmds.pointConstraint(self.startJoint, self.hinge_joints[0])
        cmds.parentConstraint(self.hinge.name, aim_targets[0], mo=True)

        cmds.pointConstraint(self.hinge.name, self.hinge_joints[2])
        cmds.pointConstraint(self.endJoint, aim_targets[1], mo=True)
        cmds.orientConstraint(self.midJoint, aim_targets[1], mo=True)

        # Hide the visibility of the second joint of each chain
        cmds.setAttr(self.hinge_joints[1] + ".drawStyle", 2)
        cmds.setAttr(self.hinge_joints[3] + ".drawStyle", 2)

        # parent the lower twist joint to the second half hinge if it exists.
        if self.lowerTwistJnt:
            cmds.parent(self.lowerTwistJnt, self.hinge_joints[2])
    
        return True
        
    def mirror(self):

        original_side = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side = "Rt"
            mirrored_side = "Lf"
            
        
        newself = TwoSegmentLimb(name=self.name.replace(original_side, mirrored_side))
        
        newself.startJoint = self.startJoint.replace(original_side, mirrored_side)
        newself.midJoint = self.midJoint.replace(original_side,  mirrored_side)
        newself.endJoint = self.endJoint.replace(original_side, mirrored_side)
        
        newself.poleVectorTranslation = [self.poleVectorTranslation[0] * -1, self.poleVectorTranslation[1], self.poleVectorTranslation[2]]
        newself.startFkOffset = self.startFkOffset
        
        newself.startGimbal = self.startGimbal
        newself.endGimbal = self.endGimbal
        
        newself.defaultIk = self.defaultIk
        newself.mirrored = 1
        newself.alignIkToWorld = self.alignIkToWorld
        newself.zeroPoseRot = self.zeroPoseRot
        
        newself.hingeControl = self.hingeControl
        newself.benderControls = self.benderControls
        
        newself.upAxis = self.upAxis
        
        return newself


    def getExportJointDict(self):
        
        if self.hingeControl:
            self.export_joints[self.hinge_joints[0]] = self.startJoint
            self.export_joints[self.hinge_joints[2]] = self.midJoint
            
        if self.benderControls:
            for ii in range(len(self.upper_bender_joints)-2, 0, -1):
                self.export_joints[self.upper_bender_joints[ii]] = self.upper_bender_joints[ii-1]

            for ii in range(len(self.lower_bender_joints)-2, 0, -1):
                self.export_joints[self.lower_bender_joints[ii]] = self.lower_bender_joints[ii-1]

            if self.hingeControl:
                self.export_joints[self.upper_bender_joints[0]] = self.hinge_joints[0]
                self.export_joints[self.lower_bender_joints[0]] = self.hinge_joints[2]
            else:
                self.export_joints[self.upper_bender_joints[0]] = self.startJoint
                self.export_joints[self.lower_bender_joints[0]] = self.midJoint
                
        self.export_joints[self.startJoint] = None
        self.export_joints[self.midJoint] = self.startJoint
        self.export_joints[self.endJoint] = self.midJoint
        
        self.export_joints_start = [self.startJoint]
    
        if self.lowerTwistJnt and cmds.objExists(self.lowerTwistJnt):
            self.export_joints[self.lowerTwistJnt] = self.midJoint

        self.export_joints_end = [self.endJoint]