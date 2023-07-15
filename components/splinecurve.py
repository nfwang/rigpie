 
import maya.cmds as cmds

from rigpie.pylib.component import Component
from rigpie.pylib.control import Control
from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.rmath import Transform, Vector

import rigpie.pylib.constraints as constraints_pylib
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.rig as rig_pylib
import rigpie.pylib.rmath as rmath_pylib
import rigpie.pylib.controlshape as controlshape_pylib
import rigpie.pylib.joint as joint_pylib
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.curve as curve_pylib
import rigpie.pylib.mayatransform as mayatransform_pylib

class SplineCurve(Component):
    ''' Simple FK chain with the option of ik spline tweak controls '''
    
    def __init__(self,  **kwargs):
        
        # Required arguments
        self.name = kwargs.get('name', 'CnSplineCurve1')
        self.joints = kwargs.get('joints', ['CnSplineCurve%sJnt' % ii for ii in range(1,6)])
        self.controlJoints = kwargs.get('controlJoints', ['CnSplineCurve%sJnt' % ii for ii in range(1,6)])
        self.tweakSpacing = kwargs.get('tweakSpacing', 0)
        self.controlAttrLocks = kwargs.get('controlAttrLocks', ['t', 'v', 's'])
        self.shapeType = kwargs.get('shapeType', 'circle')
        self.shapeRotation = kwargs.get('shapeRotation', [0,0,0])
        self.size = kwargs.get('size', 10)
        
        self.controlParenting = kwargs.get('controlParenting', 'hierarchy') # 'flat' or 'hierarchy'
        self.curveAttach = kwargs.get('curveAttach', None)
        self.curveAttachRail = kwargs.get('curveAttachRail', None)
        self.aimVector = kwargs.get('aimVector', None)
        self.upVector = kwargs.get('upVector', [0,1,0])
        self.spans = kwargs.get('spans', 7)
        self.mainCurveSkinweights = kwargs.get('mainCurveSkinweights', None) #[vertid0tuple, vertid1tuple] vertidtuple = [(influence1,weight1), (influence2:weight2)]
        self.mainCurveSpans = kwargs.get('mainCurveSpans', 7)
        self.controlColor = kwargs.get('controlColor', None)
        self.retractAttr = kwargs.get('retractAttr', False)
        self.matchMajorCvsToMainControls = kwargs.get('matchMajorCvsToMainControls', False)
        self.bindType = kwargs.get('bindType', 'spline')
        
        super().__init__(**kwargs)
        
        self.root = ""
        
        self.ctrlTwist = kwargs.get('ctrlTwist', False)
        self.dWorldUpAxis = 1  # [Y, -Y, ~Y, Z, -Z, ~Z, X, -X, ~X]
        self.dForwardAxis = 0  # [X, -X, Y, -Y, Z, -Z]
        
        self.motionPathInverseFront = False
        self.motionPathInverseUp = False
        
        # Protected members
        self.curve = ""
        self.tweak_curve = ""
        self.effector = ""
        self.ikhandle = ""
        self.controls = [] # all controls includes up vectors
        self.main_controls = [] # controls for the spline
        self.tweak_controls = [] # minor controls for the spline
        self.tweak_dag = ""
        self.start_vector = ""
        self.end_vector = ""

        self.pins = {"end":None, "start":None}

    def mirror(self):
        original_side  = "Lf"
        mirrored_side = "Rt"
        if self.name[0:2] == "Rt":
            original_side = "Rt"
            mirrored_side = "Lf"
            
        
        newself = SplineCurve(name=self.name.replace(original_side, mirrored_side))
        
        mirror_joints = []
        for joint in self.joints:
            mirror_joints.append(joint.replace(original_side, mirrored_side))
        newself.joints = mirror_joints

        mirror_joints = []
        for joint in self.controlJoints:
            mirror_joints.append(joint.replace(original_side, mirrored_side))
        newself.controlJoints = mirror_joints
        
        newself.tweakSpacing = self.tweakSpacing
        newself.controlAttrLocks = self.controlAttrLocks
        newself.shapeType = self.shapeType
        newself.controlParenting = self.controlParenting
        
        newself.mainCurveSkinweights = self.mainCurveSkinweights
        newself.matchMajorCvsToMainControls = self.matchMajorCvsToMainControls
        
        if self.curveAttach:
            newself.curveAttach = self.curveAttach.replace(original_side, mirrored_side)
            newself.curveAttachRail = self.curveAttachRail.replace(original_side, mirrored_side)
        
        newself.motionPathInverseFront = not self.motionPathInverseFront
        newself.motionPathInverseUp = not self.motionPathInverseUp
        newself.retractAttr = self.retractAttr
        
        newself.shapeRotation = self.shapeRotation
        newself.size = self.size
        
        newself.upVector = self.upVector
        newself.spans = self.spans
        newself.mainCurveSpans = self.mainCurveSpans
        
        if self.mainCurveSkinweights:
            mirror_skinweight_tuples = []
            for tuple_list in self.mainCurveSkinweights:
                newlist = []
                for tuple in tuple_list:
                    newlist.append((tuple[0].replace(original_side, mirrored_side), tuple[1]))
                    
                mirror_skinweight_tuples.append(newlist)

            newself.mainCurveSkinweights = mirror_skinweight_tuples
        
        newself.mirrored = 1
        
        return newself

    def prebuild(self):
        super().prebuild()

    def build(self):
        super().build()
        
        # Make Static anchors to measure distance based on rig scale.
        static_anchor_start_name = MayaName(self.name)
        static_anchor_start_name.descriptor += "StaticStart"
        static_anchor_start_name.category = "Null"
        
        static_anchor_start = cmds.createNode("transform", name=static_anchor_start_name, parent=self.rig_dag)
        xform_pylib.align(static_anchor_start, self.joints[0])
        
        static_anchor_end_name = MayaName(self.name)
        static_anchor_end_name.descriptor += "StaticEnd"
        static_anchor_end_name.category = "Null"
        
        static_anchor_end = cmds.createNode("transform", name=static_anchor_end_name, parent=self.rig_dag)
        xform_pylib.align(static_anchor_end, self.joints[-1])
       
        # Create the chain of controls
        head = ""
        tail = ""
        
        distArray = [0]
        thead = None
        
        if not self.aimVector:
            aim_axis = joint_pylib.getLongAxis(self.joints[1])
            self.aimVector = joint_pylib.getLongAxisVector(self.joints[1])
            
        else:
            aim_axis = "x"
            if self.aimVector[1]:
                aim_axis = "y"
            elif self.aimVector[2]:
                aim_axis = "z"
        
        up_axis = "x"
        if self.upVector[1]:
            up_axis = "y"
        elif self.upVector[2]:
            up_axis = "z"
            
        if not self.controlColor:
            self.controlColor = controlshape_pylib.getColorBySide(self.name)

        thickness = 1
        if self.tweakSpacing:
            thickness = 2
        
        # Build controls
        for jnt in self.controlJoints:

            # if there are tweak controls, do not constrain the joint to the ctrl
            if head == "":
                control_name = MayaName(jnt)
                control_name.category = "Ctrl"
                
                head = Control( name=control_name, 
                                color=self.controlColor, 
                                size=self.size, 
                                shapeType=self.shapeType, 
                                lockAndHide=self.controlAttrLocks, 
                                type="joint",
                                rotationOrder=jnt, 
                                parent=self.controls_dag, 
                                matrix=jnt,
                                thickness=thickness,
                                shapeRotation=self.shapeRotation
                                
                )
                self.registerControl(head)
                
                self.main_controls.append(head)
                
                head = head.name
                tail = head
                
                if self.root != "":
                    constraints_pylib.parentConstraintMaintainOffset(self.root, head.zero)
                
                if self.controlParenting == "flat":
                    attribute_pylib.unlockAndShow(head, ["t"])
                    
                # Save out the translation
                thead = rmath_pylib.Vector(cmds.xform(head, q=True, t=True, ws=True))
                
            else:
                control_name = MayaName(jnt)
                control_name.category = "Ctrl"
                
                ctrl = Control( name=control_name, 
                                color=self.controlColor,
                                size=self.size, 
                                shapeType=self.shapeType, 
                                lockAndHide=self.controlAttrLocks,
                                thickness=thickness,
                                type="joint",
                                rotationOrder=jnt,
                                matrix=jnt, 
                                shapeRotation=self.shapeRotation
                )
                self.registerControl(ctrl)
                self.main_controls.append(ctrl)
                                
                zero = ctrl.zero
                ctrl = ctrl.name
                
                if self.controlParenting != "flat":
                    attribute_pylib.unlockAndShow(zero, ["t","r","s"])
                    cmds.parent(zero, tail)
                    attribute_pylib.lockAndHide(zero, ["t","r","s"])
                else:
                    cmds.parent(zero, self.controls_dag)
                    attribute_pylib.unlockAndShow(ctrl, ["t"])
                    
                    if self.root != "":
                        constraints_pylib.parentConstraintMaintainOffset(self.root, zero)
                
                # Find Distance from head
                tctrl = rmath_pylib.Vector(cmds.xform(ctrl, q=True, t=True, ws=True))
                distArray.append((thead - tctrl).length()) 
                
                tail = ctrl
        
        main_control_names = ["%s" % ctrl.name for ctrl in self.main_controls]
        self.curve_skincluster = None
        # Use maya's spline ik to generate the curve
        if self.curveAttach:        
            self.curve = self.curveAttach
        else:
            # Create spline IK
            (self.ikhandle, self.effector, self.curve) = cmds.ikHandle(sj=self.joints[0], ee=self.joints[len(self.joints)-1], sol="ikSplineSolver", ns=4 )

            # Rename and organize
            self.ikhandle = cmds.rename( self.ikhandle, self.name+"IKHandle" )
            self.curve = cmds.rename( self.curve, self.name+"Curve" )
            cmds.rebuildCurve ( self.curve, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=self.spans, d=3, tol=0.001 )
            cmds.parent( self.ikhandle, self.worldspace_dag )
            cmds.parent( self.curve, self.worldspace_dag )
            
            # end pin
            end_pin_name = MayaName(self.name)
            end_pin_name.descriptor = end_pin_name.descriptor + "EndPin"
            end_pin_name.category = "Null"

            end_pin = cmds.createNode( "transform", name=str(end_pin_name))
            xform_pylib.align(end_pin, self.joints[-1])
            self.pins["end"] = end_pin
            
            # start pin
            start_pin_name = MayaName(self.name)
            start_pin_name.descriptor = start_pin_name.descriptor + "StartPin"
            start_pin_name.category = "Null"

            start_pin = cmds.createNode("transform", n= str(start_pin_name))
            xform_pylib.align(start_pin, self.joints[0])
            self.pins["start"] = start_pin                

            curve_pylib.enableStretchyComponentJoints(self.curve, self.pins["start"], self.pins["end"], self.joints, self.main_controls, self, aimVector=self.aimVector, stretch_attr=True)

            if self.ctrlTwist:

                start_joint = self.joints[0]
                end_joint   = self.joints[-1]
            
                start_vector_name = MayaName(start_joint)
                start_vector_name.descriptor = start_vector_name.descriptor + "StartPv"
                start_vector_name.category = "Ctrl"

                start_vector_transform = Transform(start_joint)
                move_vector = Vector(self.upVector)
                move_vector = move_vector * 25
                start_vector_transform.translate(move_vector)
                
                show_pv_attr = self.component_options+".showUpVectors"
                attribute_pylib.add(show_pv_attr)
                
                self.start_vector = Control( name=start_vector_name, 
                                             color=self.controlColor,
                                             size=self.size/5.0, 
                                             shapeType="turtle", 
                                             lockAndHide=['r','s'], 
                                             matrix=start_vector_transform
                )
                
                self.registerControl(self.start_vector)
                cmds.connectAttr(show_pv_attr, self.start_vector.name+".visibility")

                end_vector_name = MayaName(end_joint)
                end_vector_name.descriptor = end_vector_name.descriptor + "EndPv"
                end_vector_name.category = "Ctrl"

                end_vector_transform = Transform(end_joint)
                end_vector_transform.translate(move_vector)
                
                self.end_vector = Control( name=end_vector_name, 
                                           color=self.controlColor,
                                           size=self.size/5.0,
                                           shapeType="turtle", 
                                           lockAndHide=['r','s'], 
                                           matrix=end_vector_transform,
                                           shapeRotation=[0,0,180]
                )
                self.registerControl(self.end_vector)
                
                cmds.connectAttr(show_pv_attr, self.end_vector.name+".visibility")

                
                cmds.parent(self.start_vector.zero, self.main_controls[0].name)
                cmds.parent(self.end_vector.zero, self.main_controls[-1].name)

                # Assign upvector to spline twist
                cmds.setAttr (self.ikhandle+".dTwistControlEnable", 1)
                cmds.setAttr (self.ikhandle+".dWorldUpType", 2)
                cmds.setAttr (self.ikhandle+".dWorldUpAxis", self.dWorldUpAxis)
                cmds.setAttr (self.ikhandle+".dForwardAxis", self.dForwardAxis)
                
                cmds.connectAttr(self.start_vector.name+".worldMatrix[0]", self.ikhandle+".dWorldUpMatrix", f=True)
                cmds.connectAttr(self.end_vector.name+".worldMatrix[0]", self.ikhandle+".dWorldUpMatrixEnd", f=True)

        cmds.setAttr(self.curve+".inheritsTransform", 0)
        
        joints_curve = self.curve
        if self.tweakSpacing:
            #### TWEAK CONTROLS ####
            # Group
            self.tweak_dag = cmds.createNode("transform", n="Tweaks", parent=self.controls_dag)
            
            # Vis attr
            tweakattr = attribute_pylib.add("%s.tweaks" % self.component_options, value=0, type="long")
        
            # Create tweak controls
            frontFkId  = -1
            endFkId    = -1
            twistCnt   = 1
            
            self.tweak_controls = []

            for ii in range(0, len(self.joints)+self.tweakSpacing, self.tweakSpacing):
                # make a tweak on the last joint regardless of the spacing
                try:
                    jnt = self.joints[ii]
                except:
                    jnt = self.joints[-1]

                # current fkctrl corresponding to tweak
                if (jnt in self.controlJoints):
                    frontFkId = self.controlJoints.index(jnt)
                    endFkId   = self.controlJoints.index(jnt) + 1
                    
                    twistCnt  = 1
                
                # create ctrl
                tweak_control_name = MayaName(jnt)
                tweak_control_name.descriptor = tweak_control_name.descriptor + "Tweak"
                tweak_control_name.category = "Ctrl"

                # To cover when the spacing value matches the forced end tweak creation
                if cmds.objExists(tweak_control_name):
                    break
                
                # different control color shade
                tweak = Control( name=tweak_control_name, 
                                 color="green", 
                                 size=self.size/2.0, 
                                 shapeType="circle",
                                 lockAndHide=["s","v"], 
                                 type="joint",
                                 parent=self.tweak_dag, 
                                 matrix=jnt, 
                                 shapeRotation=self.shapeRotation
                )
                self.registerControl(tweak)
                self.tweak_controls.append( tweak.name )

                
                if self.bindType == "spline":
                    
                    if self.tweak_curve == "":
                        major_curve_name = MayaName(self.curve)
                        major_curve_name.descriptor = major_curve_name.descriptor + "Major"
                    
                        self.tweak_curve = cmds.duplicate(self.curve, n=major_curve_name)[0]
                        
                        cmds.setAttr(self.tweak_curve+".inheritsTransform", 0)
                        
                    degree = cmds.getAttr(self.tweak_curve + '.degree')
                    cmds.rebuildCurve(self.tweak_curve, keepRange=True, spans=self.mainCurveSpans, degree=degree)
                    
                    # This will only work if the cv count matches the main control count
                    # Align the cv with the main controls so that you get less floating ignore first and last controls
                    if self.matchMajorCvsToMainControls:
                        for cv in range(2, self.mainCurveSpans + degree - 2):
                            
                            control = self.main_controls[cv-1].name
                            
                            translation = cmds.xform(control, worldSpace=True, translation=True, query=True)
                            cmds.xform("{}.cv[{}]".format(self.tweak_curve, cv), translation=translation, worldSpace=True)

                    
                    # Unlock translates and rotations of the zero
                    attribute_pylib.unlockAndShow(tweak.zero, ["t","r"])
                    
                    if self.root != "":
                        curve_pylib.attachNodeToCurve( self.tweak_curve, tweak.zero, worldUpType="objectrotation", worldUpVector=self.upVector, worldUpObject=self.root)
                    else:
                        
                        (motion_path, param, flipped_transform) = curve_pylib.attachNodeToCurve( self.tweak_curve, tweak.zero, worldUpType="vector", worldUpVector=self.upVector, aimVector=self.aimVector, upVector=self.upVector)
                        cmds.parent(flipped_transform, self.worldspace_dag)
                    
                    
                elif self.bindType == "hierarchy":
                    
                    ttweak = rmath_pylib.Vector(cmds.xform(jnt, q=True, t=True, ws=True))
                    dist = (thead - ttweak).length()
                    
                    attribute_pylib.unlockAndShow(tweak.zero, ["t","r"])
                    
                    cfk = 0
                    for jj in range(len(distArray)):
                        if dist >= distArray[jj]:
                            cfk = jj

                    constraints_pylib.parentConstraintMaintainOffset(self.main_controls[cfk].name, tweak.zero)
                
                    # Relock
                    attribute_pylib.lockAndHide(tweak.zero, ["t","r"])

                twistCnt += 1
            
                
            # Skin the tweak ctrls to the ik spline curve
            cmds.skinCluster(self.curve, self.tweak_controls)
            
            # Connect vis attr to tweaks vis
            attribute_pylib.connectAttr(tweakattr, self.tweak_dag+".v")
            
            ## Turn off inherit transform to remove double xform
            cmds.setAttr(self.tweak_dag+".inheritsTransform", 0)
            cmds.setAttr(self.curve+".inheritsTransform", 0)
        else:
            self.curve_skincluster = cmds.skinCluster(self.curve, main_control_names)[0]
        
        if self.curveAttach:
            # group of motion pathed transform that joints will be constrained to
            attach_group_name = MayaName(self.name)
            attach_group_name.descriptor = attach_group_name.descriptor + "AttachGroup"
            attach_group_name.category = "Null"
            
            attach_group = cmds.createNode("transform", name=attach_group_name, parent=self.rig_dag)
                                    
            cmds.setAttr(attach_group+".inheritsTransform", 0)

            
            if self.curveAttachRail:
                # group of motion pathed transform that will be used as an up vector
                rail_group_name = MayaName(self.name)
                rail_group_name.descriptor = rail_group_name.descriptor + "RailGroup"
                rail_group_name.category = "Null"
                
                rail_group = cmds.createNode("transform", name=rail_group_name, parent=self.rig_dag)
                cmds.setAttr(rail_group+".inheritsTransform", 0)

            # Add stretch attr
            stretch_attr = self.component_options+".stretch"
            attribute_pylib.add(stretch_attr, max=1.0, min=0.0, type="float", value=1)

            reverse_joint_list = list(self.joints)
            reverse_joint_list.reverse()
            rail_motion_paths = []
            motion_paths = []
            
            for joint in reverse_joint_list:

                attach_name = MayaName(joint)
                attach_name.descriptor = attach_name.descriptor + "Attach"
                attach_name.category = "Null"
                
                attach = cmds.createNode("transform", name=attach_name, parent=attach_group)
                
                xform_pylib.align(attach, joint)
                
                motion_path = None
                if self.curveAttachRail:
                    rail_name = MayaName(joint)
                    rail_name.descriptor = rail_name.descriptor + "Rail"
                    rail_name.category = "Null"
                    
                    rail = cmds.createNode("transform", name=rail_name, parent=rail_group)
                    
                    # pin to curve with closest point
                    (motion_path, param, flipped_transform) = curve_pylib.attachNodeToCurve(self.curve, attach, worldUpType="object", worldUpObject=rail, aimVector=self.aimVector, upVector=self.upVector)
                    motion_paths.append(motion_path)
                    
                    # use the same param for the rail
                    (rail_motion_path, rail_param, flipped_transform) = curve_pylib.attachNodeToCurve(self.curveAttachRail, rail)
                    cmds.parent(flipped_transform, self.worldspace_dag)
                    rail_motion_paths.append(rail_motion_path)

                    cmds.setAttr(rail_motion_path+".uValue",  param)
                    
                    # inverse the front and up for mirrored joint chains
                    cmds.setAttr(motion_path+".inverseFront", self.motionPathInverseFront)
                    cmds.setAttr(motion_path+".inverseUp", self.motionPathInverseUp)
                    
                    cmds.setAttr(self.curveAttachRail+".inheritsTransform", 0)

                else:
                    (motion_path, param, flipped_transform) = curve_pylib.attachNodeToCurve(self.curve, attach, worldUpType="vector", worldUpVector=self.upVector, aimVector=self.aimVector, upVector=self.upVector)
                    cmds.parent(flipped_transform, self.worldspace_dag)
                    
                    motion_paths.append(motion_path)
                
                cmds.parentConstraint(attach, joint)
            

            if self.curveAttachRail:
                rail_skincluster = cmds.skinCluster(self.curveAttachRail, main_control_names)[0]
                curve_pylib.enableStretchyMotionPath(stretch_attr, self.curveAttachRail, rail_motion_paths)
            else:
                curve_pylib.enableStretchyMotionPath(stretch_attr, self.curveAttach, motion_paths)
                

        # Slide attr
        if self.retractAttr:
            retract_attr = self.component_options + ".retract"
            curve_pylib.enableSlideJoints(retract_attr, self.joints, self.aimVector)
        
        # export joint dictionary
        for ii in range(len(self.joints)):
            if ii == 0:
                self.export_joints[self.joints[0]] = None
            else:
                self.export_joints[self.joints[ii]] = self.joints[ii-1]
        
        

    def postbuild(self):
        super().postbuild()
        
        if self.tweak_curve and self.mainCurveSkinweights:
            main_control_names = ["%s" % ctrl.name for ctrl in self.main_controls]
            
            if (self.bindType == "spline") and (len(main_control_names) != 0):
                self.curve_skincluster = cmds.skinCluster(self.tweak_curve, main_control_names)[0]
                
                for cv in range(len(self.mainCurveSkinweights)):
                    weight_tuples = self.mainCurveSkinweights[cv]
                    cmds.skinPercent (self.curve_skincluster, "{}.cv[{}]".format(self.tweak_curve, cv), transformValue=weight_tuples)
                    
        self.export_joints_start = [self.joints[0]]
        self.export_joints_end = [self.joints[-1]]
