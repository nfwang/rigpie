 

import maya.cmds as cmds

from rigpie.components.splinecurve import SplineCurve
from rigpie.pylib.control import Control
from rigpie.pylib.mayaname import MayaName

import rigpie.pylib.rig as rig
import rigpie.pylib.attribute as attribute
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.controlshape as controlshape_pylib
import rigpie.pylib.constraints as constraints_pylib
import rigpie.pylib.skincluster as skincluster_pylib

class Spine(SplineCurve):
    ''' Spine component used for upright characters 
        SplineCurve with a shaper control driven by a single chain ik.
    '''
    
    def __init__(self, **kwargs):

        kwargs['name'] = kwargs.get('name', 'CnSpineComponent')
        kwargs['componentMatrix'] = kwargs.get('componentMatrix', 'CnHipJnt')
        kwargs['joints'] = kwargs.get('joints', ["CnSpine%sJnt" % ii for ii in range(1,6)])
        kwargs['controlJoints'] = kwargs.get('controlJoints', ["CnSpineBotJnt", "CnSpineTopJnt"])
        kwargs['shape'] = kwargs.get('shape', 'circle')
        kwargs['upVector'] = kwargs.get('upVector', [1,0,0])
        kwargs['twistEnable'] = kwargs.get('twistEnable', False)
        kwargs['tweaks'] = kwargs.get('tweaks', False)
        kwargs['controlParenting'] = kwargs.get('controlParenting', True)
        kwargs['bindType'] = kwargs.get('bindType', 'hierarchy')
        
        self.lastControlGimbal = kwargs.get('lastControlGimbal', False)
        self.shaperJoint = kwargs.get('shaperJoint', None)
        
        super().__init__(**kwargs)

        self.upVector = [0,0,-1]
        self.ctrlTwist = True
        self.dWorldUpAxis = 4 # [Y, -Y, ~Y, Z, -Z, ~Z, X, -X, ~X]
        self.dForwardAxis = 2 # [X, -X, Y, -Y, Z, -Z]

        
        
    def build(self):
        super().build()

        # since this component is also used for the neck, if there is a top control joint 
        # then unlock the translation of it.
        
        self.top_spine_control = None
        if self.lastControlGimbal:
            top_spine_ctrl = self.controlJoints[-1].replace("Jnt", "Ctrl")
            attribute.unlockAndShow(top_spine_ctrl, ['t'])
            
            # Spine Top Gimbal
            ctrl_name = MayaName(top_spine_ctrl)
            ctrl_name.descriptor = ctrl_name.descriptor + "Gimbal"

            spine_top_gimbal = Control( name=ctrl_name,
                                        color=controlshape_pylib.getColorBySide(top_spine_ctrl), 
                                        size=5, 
                                        shapeType="cube",
                                        depth=0,
                                        lockAndHide=["s","v"], 
                                        rotationOrder=top_spine_ctrl,
                                        matrix=top_spine_ctrl, 
                                        parent=top_spine_ctrl
            )
            
            self.registerControl(spine_top_gimbal)
            
            constraints_pylib.offsetParentMatrixConstraint(spine_top_gimbal.name, self.controlJoints[-1])
            
            # Visiblity
            attr = attribute.add(top_spine_ctrl+".gimbal", max=1, min=0, value=0)
            attribute.connectAttr(attr, spine_top_gimbal.name+"Shape.visibility")
            
            self.top_spine_control = spine_top_gimbal
    
        # Constrain the floating joints that are used for control creation, just so the skeleton looks better.
        mid_spine = None
        for ii in range(len(self.controlJoints)):
            joint = self.controlJoints[ii]
            ctrl = joint.replace("Jnt", "Ctrl")
            
            cmds.parentConstraint(ctrl, joint)
            mid_spine = ctrl

        end_pin_name = MayaName(self.name)
        end_pin_name.category = "Zero"
        end_pin_zero = cmds.createNode( "transform", name=str(end_pin_name), parent=mid_spine)
        
        xform_pylib.align(end_pin_zero, self.pins["end"])
        
        cmds.parent(self.pins["end"], end_pin_zero)
        
        # Setup twist
        start_joint = self.joints[0]
        end_joint = self.joints[-1]
        
        if not self.shaperJoint:
            center = int(len(self.controlJoints) / 2)
            self.shaperJoint = self.controlJoints[center]

        # Shaper
        shaper_name = MayaName(self.name)
        shaper_name.category = "Ctrl"
        shaper_name.descriptor = shaper_name.descriptor+"Shaper"
        
        self.shaper = Control( name=shaper_name, 
                               color="dark orange", 
                               size=self.size, 
                               shapeType="circle", 
                               lockAndHide=["s","v"], 
                               rotationOrder=self.controlJoints[0],
                               matrix=self.shaperJoint, 
                               parent=self.controls_dag, 
                               type="joint"
        )
        self.registerControl(self.shaper)
        
        shaper = self.shaper.name
        shaperZero = self.shaper.zero
        
        # Joint to drive shaper
        shaper_jointa_name = MayaName(self.name)
        shaper_jointa_name.descriptor = shaper_jointa_name.descriptor + "ShaperA"
        shaper_jointa_name.category = "Jnt"
        
        shaper_joint_a = cmds.createNode("joint", name=shaper_jointa_name)

        shaper_jointb_name = MayaName(self.name)
        shaper_jointb_name.descriptor = shaper_jointb_name.descriptor + "ShaperB"
        shaper_jointb_name.category = "Jnt"

        shaperjntb = cmds.createNode("joint", name=shaper_jointb_name)
        
        cmds.delete(cmds.parentConstraint(start_joint, shaper_joint_a))
        cmds.delete(cmds.parentConstraint(end_joint, shaperjntb))

        cmds.delete(cmds.aimConstraint(shaperjntb, shaper_joint_a, aimVector=[0,1,0], upVector=[0,0,1], worldUpType="scene"))
        cmds.makeIdentity(shaper_joint_a, apply=1, t=1, r=1, s=1, n=0, pn=1)
        cmds.makeIdentity(shaperjntb, apply=1, t=1, r=1, s=1, n=0, pn=1)
        
        cmds.parent(shaperjntb, shaper_joint_a)
        cmds.parent(shaper_joint_a, self.rig_dag)
        
        (ikHandle, ee) = cmds.ikHandle(shaper_joint_a, endEffector=shaperjntb, solver="ikSCsolver")
        ikHandle = cmds.rename(ikHandle, "{}ShaperIKHandle".format(self.name))
        ee = cmds.rename(ee, "{}ShaperEFF".format(self.name))

        cmds.pointConstraint(self.pins["start"], shaper_joint_a)
        
        shaperIk_name = MayaName(self.name)
        shaperIk_name.descriptor = shaperIk_name.descriptor + "ShaperRef"
        shaperIk_name.category = "Zero"
        shaperikzero = cmds.createNode("transform", name=str(shaperIk_name), parent=self.controlJoints[0])
        
        shaperIk_name.category = "Null"
        shaperikref = cmds.createNode("transform", name=str(shaperIk_name), parent=shaperikzero)
        
        cmds.parentConstraint(shaperikref, ikHandle)
        
        cmds.delete(cmds.parentConstraint(self.pins["end"], shaperikzero))
        cmds.connectAttr(self.pins["end"]+".t", shaperikref+".t")
        
        constraints_pylib.parentConstraintMaintainOffset(shaper_joint_a, shaperZero)
        
        # Skin the spine
        cmds.parent(ikHandle, self.worldspace_dag)
        
        start_joint_name = MayaName(self.pins["start"])
        start_joint_name.descriptor = start_joint_name.descriptor + "Spline"
        start_joint = cmds.createNode("joint", n=start_joint_name, parent=self.worldspace_dag)
        cmds.connectAttr(self.pins["start"]+".worldMatrix", start_joint+".offsetParentMatrix")

        shaper_joint_name = MayaName(shaper)
        shaper_joint_name.category = "Jnt"
        shaper_joint = cmds.createNode("joint", n=shaper_joint_name, parent=self.worldspace_dag)
        cmds.connectAttr(shaper+".worldMatrix", shaper_joint+".offsetParentMatrix")
        
        end_pin_joint = MayaName(self.pins["end"])
        end_pin_joint.category = "Jnt"
        end_pin_joint = cmds.createNode("joint", n=end_pin_name, parent=self.worldspace_dag)
        cmds.connectAttr(self.pins["end"]+".worldMatrix", end_pin_joint+".offsetParentMatrix")
        
        skinJnts = [start_joint, shaper_joint, end_pin_joint]
        
        # delete the existing skincluster on the curve
        curve_skincluster = skincluster_pylib.findRelatedSkinCluster(self.curve)
        cmds.delete(curve_skincluster)
        
        cmds.select(skinJnts)
        sc = cmds.skinCluster(self.curve, skinJnts, tsb=1)[0]
        cmds.skinPercent( sc, '{}.cv[0]'.format(self.curve), transformValue=[(skinJnts[0], 1.0)])
        cmds.skinPercent( sc, '{}.cv[3]'.format(self.curve), transformValue=[(skinJnts[2], 1.0)])
        cmds.skinPercent( sc, '{}.cv[2]'.format(self.curve), transformValue=[(skinJnts[1], 1.0)])
        cmds.skinPercent( sc, '{}.cv[1]'.format(self.curve), transformValue=[(skinJnts[1], 1.0)])
        
        cmds.parent(self.start_vector.zero, self.pins["start"])
        cmds.parent(self.end_vector.zero, self.pins["end"])
    
    def postbuild(self):
        super().postbuild()
        
        # export joint dictionary
        self.export_joints.pop(self.joints[-1]) # remove the last joint
        
        if self.top_spine_control:
            self.export_joints_end = [self.controlJoints[-1]]
            self.export_joints[self.controlJoints[-1]] = self.joints[-2]
        else:
            self.export_joints_end = [self.joints[-2]]
