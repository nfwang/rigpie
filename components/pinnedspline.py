 
import maya.cmds as cmds

from rigpie.components.splinecurve import SplineCurve
from rigpie.pylib.rmath import Vector, Transform

from rigpie.pylib.control import Control
from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.component import Component

import rigpie.pylib.curve as curve_pylib
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.coordspace as coordspace_pylib

class PinnedSpline(Component):
    ''' A spline curve component with a head and tail.  Joints are procedurally generated with a rail and a curve.
        Setup that came from AltarTableTentacle.
    '''
    
    def __init__(self,  **kwargs):
        
        super().__init__(**kwargs)
        
        # Required arguments
        self.name = kwargs.get('name', 'CnPinnedSplineComponent')
        self.curve = kwargs.get('curve', 'CnSplineCurve')
        self.rail = kwargs.get('rail', None)
        self.numberOfJoints = kwargs.get('numberOfJoints', 41)
        self.controlDivisions = kwargs.get('controlDivisions', 4)
        self.tweakDivision = kwargs.get('tweakDivision', 2)
        self.jointsParent = kwargs.get('jointsParent', None)
        self.controlAttrLocks = kwargs.get('controlAttrLocks', ['s', 'v'])
        self.retractAttr = kwargs.get('retractAttr', False)
        self.alignToNextMainControl = kwargs.get('alignToNextMainControl', False)
        
        self.aimVector = kwargs.get('aimVector', [0, 0, -1])
        self.upVector = kwargs.get('upVector', [0, 1, 0])
        self.mainCurveSkinweights = kwargs.get('mainCurveSkinweights', None)
        self.railOffsetVector = kwargs.get('railOffsetVector', None)
        self.mainControlSpace = kwargs.get('mainControlSpace', 'hammock')
        
        self.shapeType = kwargs.get('shapeType', 'circle')
        self.shapeRotation = kwargs.get('shapeRotation', [90,0,0])
        self.size = kwargs.get('size', 5)
        self.thickness = kwargs.get('thickness', 1)
        self.rotationOrder = kwargs.get('rotationOrder', "xyz")
        self.controlColor = kwargs.get('controlColor', None)


        # protected members
        self.controls = []
        self.main_controls = []
        self.tweak_controls = []
        
        self.hammock_transforms = None
        
        self.validHammockDivisionValues = [2, 4, 8, 16, 32, 64, 128, 256]
        
    def mirror(self):
        original_side  = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side  = "Rt"
            mirrored_side = "Lf"
            
        
        newself = PinnedSpline(name=self.name.replace(original_side, mirrored_side))

        newself.curve = self.curve.replace(original_side, mirrored_side)
        newself.numberOfJoints = self.numberOfJoints
        
        newself.controlDivisions = self.controlDivisions
        newself.tweakDivision = self.tweakDivision
        newself.jointsParent = self.jointsParent
        newself.controlAttrLocks = self.controlAttrLocks
        newself.retractAttr = self.retractAttr
        newself.alignToNextMainControl = self.alignToNextMainControl

        newself.aimVector = self.aimVector
        newself.upVector = self.upVector

        newself.mainCurveSkinweights = self.mainCurveSkinweights
        newself.railOffsetVector = self.railOffsetVector
        newself.mainControlSpace = self.mainControlSpace

        # Control shape
        newself.shapeType = self.shapeType
        newself.shapeRotation = self.shapeRotation
        newself.size = self.size
        newself.thickness = self.thickness
        newself.rotationOrder = self.rotationOrder
        newself.controlColor = self.controlColor
        
        newself.mirrored = 1
        
        return newself

    def prebuild(self):
    
        super().prebuild()

        if self.jointsParent == None:
            self.jointsParent = self.rig_dag
            
        # Create Rail
        if not self.rail:
            rail_name = MayaName(self.curve)
            rail_name.descriptor += "Rail"
            self.rail = cmds.duplicate(self.curve, name=rail_name)[0]
        
            length = cmds.arclen(self.curve)
            
            if self.railOffsetVector == None:
                self.railOffsetVector = [0.0, length/2.0, 0.0]
                
            cmds.setAttr(self.rail+'.translateX', cmds.getAttr(self.rail+'.translateX') + self.railOffsetVector[0] )
            cmds.setAttr(self.rail+'.translateY', cmds.getAttr(self.rail+'.translateY') + self.railOffsetVector[1] )
            cmds.setAttr(self.rail+'.translateZ', cmds.getAttr(self.rail+'.translateZ') + self.railOffsetVector[2] )
        
        aim_coefficient = 1
        aimVector = Vector([0,0,1])
        aimVector *= aim_coefficient

        # Generate Joints
        joint_name = MayaName(self.name)
        joint_name.category = 'Jnt'
        
        self.joints = curve_pylib.createNodesAlongCurve( self.curve, 
                                                         self.rail, 
                                                         self.numberOfJoints, 
                                                         name=str(joint_name), 
                                                         aimVector=self.aimVector, 
                                                         upVector=self.upVector, 
                                                         parameterizeCurve=False
        )
       
        for joint in self.joints:
            cmds.setAttr(joint+".segmentScaleCompensate", 0)
        


    def build(self):
        
        super().build()

        force_head_tail_flip = False
        
        # Head Control
        
        # swap the head and tail --super hacky
        pos = cmds.pointOnCurve(self.curve, parameter=1)
        if force_head_tail_flip:
            pos = cmds.pointOnCurve(self.curve, parameter=0)
        
        head_control_name = MayaName(self.name)
        head_control_name.descriptor += "Head"
        head_control_name.category = "Ctrl"
        
        transform = Transform(self.joints[0])
        transform.setTranslation(pos)
        
        self.head_control = Control( name=head_control_name, 
                                     size=self.size, 
                                     shapeRotation=self.shapeRotation,
                                     color=self.controlColor, 
                                     shapeType="cube", 
                                     thickness=self.thickness,
                                     lockAndHide=self.controlAttrLocks, 
                                     matrix=transform, 
                                     rotationOrder=self.rotationOrder,
                                     parent=self.controls_dag
        )
        self.registerControl(self.head_control)
        
        # Rebuild the curve based on the number of control divisions
        degree = cmds.getAttr(self.curve + '.degree')
        spans = cmds.getAttr(self.curve + '.spans')
        
        # Setup Spline Ik
        (self.ikhandle, self.effector, self.ikspline_curve) = cmds.ikHandle( startJoint=self.joints[0], 
                                                                             endEffector=self.joints[len(self.joints)-1], 
                                                                             solver="ikSplineSolver", 
                                                                             simplifyCurve=True, 
                                                                             numSpans=spans 
        )
        
        cmds.rebuildCurve ( self.curve, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=self.controlDivisions+1, d=degree, tol=0.001 )
        cmds.rebuildCurve ( self.rail, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=self.controlDivisions+1, d=degree, tol=0.001 )
        
        # Rename and organize
        self.ikhandle = cmds.rename( self.ikhandle, self.name+"IKHandle" )
        self.ikspline_curve = cmds.rename( self.ikspline_curve, self.name+"IkSplineCurve" )
        
        tweak_count = ((self.controlDivisions) * self.tweakDivision) + 1
        
        degree = cmds.getAttr(self.ikspline_curve + '.degree')
        spans = tweak_count
    
        cmds.rebuildCurve ( self.ikspline_curve, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=spans, d=degree, tol=0.001 )
        
        cmds.parent( self.ikhandle, self.worldspace_dag )
        cmds.parent( self.ikspline_curve, self.worldspace_dag )
        
        previous_control = None
        
        # Main Controls
        for control_id in range(self.controlDivisions + 1):
        
            control_name = MayaName(self.name)
            
            if control_id != 0:
                control_name.iterator = control_id
                
            control_name.category = "Ctrl"

            pos = cmds.pointOnCurve(self.ikspline_curve, parameter=float(control_id)/float(self.controlDivisions))
            
            transform = Transform(self.joints[0])
            transform.setTranslation(pos)
        
            control = Control( name=control_name, 
                               type="joint",
                               size=self.size, 
                               shapeRotation=self.shapeRotation,
                               color=self.controlColor, 
                               shapeType="circle", 
                               thickness=self.thickness,
                               lockAndHide=self.controlAttrLocks, 
                               matrix=transform, 
                               rotationOrder=self.rotationOrder,
                               parent=self.controls_dag
            )
            
            self.registerControl(control)
            self.main_controls.append(control)

            if self.alignToNextMainControl:
                # Aim the previous control to the current control
                if previous_control:
                    up_pos = cmds.pointOnCurve(self.rail, parameter=float(control_id)/float(self.controlDivisions))
                    
                    temp_up_transform_name = MayaName(control.name)
                    temp_up_transform_name.descriptor += "TempUp"
                    temp_up_transform_name.category += "Null"
                    
                    temp_up_transform = cmds.createNode("transform", name=temp_up_transform_name)
                    cmds.xform(temp_up_transform, translation=up_pos, worldSpace=True)
                    
                    cmds.delete(cmds.aimConstraint( previous_control.zero, 
                                                    control.name, 
                                                    aimVector=self.aimVector, 
                                                    upVector=self.upVector, 
                                                    worldUpType="object", 
                                                    worldUpObject=temp_up_transform
                                )
                    )
                    
                    cmds.delete(temp_up_transform)
                    
            previous_control = control
            
        # Place the cvs at the location of controls
        for cv in range(2, self.controlDivisions + degree - 2):
            
            control = self.main_controls[cv-1].name
            
            translation = cmds.xform(control, worldSpace=True, translation=True, query=True)
            cmds.xform("{}.cv[{}]".format(self.curve, cv), translation=translation, worldSpace=True)
            

        # Tweak Controls
        tweak_dag_name = MayaName(self.name)
        tweak_dag_name.descriptor = "Tweaks"
        tweak_dag_name.category = "Null"
        
        self.tweak_dag = cmds.createNode("transform", n=tweak_dag_name, parent=self.controls_dag)
        
        for tweak_id in range(tweak_count):
        
            tweak_name = MayaName(self.name)
            tweak_name.descriptor += "Tweak"
            tweak_name.iterator = tweak_id
            tweak_name.category = "Ctrl"

            position = cmds.pointOnCurve(self.ikspline_curve, parameter=float(tweak_id)/float(tweak_count - 1))
            
            transform = Transform(self.joints[0])
            transform.setTranslation(position)
        
            tweak = Control( name=tweak_name, 
                             type="joint",
                             size=self.size / 2.0,
                             shapeRotation=self.shapeRotation,
                             color="green", 
                             shapeType="circle", 
                             thickness=self.thickness,
                             lockAndHide=self.controlAttrLocks, 
                             matrix=transform, 
                             rotationOrder=self.rotationOrder,
                             parent=self.tweak_dag,
            )
            self.registerControl(tweak)
            self.tweak_controls.append(tweak)
            
            (motion_path, param, flipped_transform) = curve_pylib.attachNodeToCurve( self.curve, 
                                                                                     tweak.zero, 
                                                                                     worldUpType="vector", 
                                                                                     worldUpVector=self.upVector, 
                                                                                     aimVector=self.aimVector, 
                                                                                     upVector=self.upVector
            )
            
            if flipped_transform:
                cmds.parent(flipped_transform, self.worldspace_dag)
            
        # Tail Control
        position = cmds.pointOnCurve(self.curve, parameter=0)
        if force_head_tail_flip:
            position = cmds.pointOnCurve(self.curve, parameter=1)
        
        tail_control_name = MayaName(self.name)
        tail_control_name.descriptor += "Tail"
        tail_control_name.category = "Ctrl"
        
        transform = Transform(self.joints[0])
        transform.setTranslation(position)        
        
        self.tail_control = Control( name=tail_control_name, 
                                     size=self.size, 
                                     shapeRotation=self.shapeRotation,
                                     color=self.controlColor, 
                                     shapeType="cube", 
                                     thickness=self.thickness,
                                     lockAndHide=self.controlAttrLocks, 
                                     matrix=transform, 
                                     rotationOrder=self.rotationOrder,
                                     parent=self.controls_dag 
        )
        self.registerControl(self.tail_control)


        # Skin the tweak ctrls to the ik spline curve
        tweak_names = ["%s" % tweak.name for tweak in self.tweak_controls]
        cmds.skinCluster(self.ikspline_curve, tweak_names)

        ## Turn off inherit transform to remove double xform
        cmds.setAttr(self.tweak_dag+".inheritsTransform", 0)
        cmds.setAttr(self.curve+".inheritsTransform", 0)        

        
        # Tweaks visibility attr
        tweakattr = attribute_pylib.add("%s.tweaks" % self.component_options, value=0, type="long")
        attribute_pylib.connectAttr(tweakattr, self.tweak_dag+".visibility")
        
        
        # Setup Stretchy joints
        curve_pylib.enableStretchyComponentJoints( self.ikspline_curve, 
                                                   self.head_control.name, 
                                                   self.tail_control.name, 
                                                   self.joints, 
                                                   self.main_controls, self, 
                                                   aimVector=self.aimVector, 
                                                   stretch_attr=True
        )

        # Skin curve to main controls
        main_control_names = ["%s" % ctrl.name for ctrl in self.main_controls]
        self.curve_skincluster = cmds.skinCluster(self.curve, main_control_names)[0]
        
        # Setup twist
        cmds.connectAttr(self.main_controls[0].name+".worldMatrix[0]", self.ikhandle+".dWorldUpMatrix", force=True)
        cmds.connectAttr(self.main_controls[-1].name+".worldMatrix[0]", self.ikhandle+".dWorldUpMatrixEnd", force=True)
        
        aim_vector_vector = Vector(self.aimVector)
        up_vector_vector = Vector(self.upVector)
        
        cmds.setAttr(self.ikhandle + ".dWorldUpAxis", up_vector_vector.getMayaEnumInt(include_closest=True))
        cmds.setAttr(self.ikhandle + ".dForwardAxis", aim_vector_vector.getMayaEnumInt())
        cmds.setAttr(self.ikhandle + ".dTwistControlEnable", 1)
        cmds.setAttr(self.ikhandle + ".dWorldUpType", 4)
        
        
        if self.retractAttr:
            retract_attr = self.component_options + ".retract"
            curve_pylib.enableSlideJoints(retract_attr, self.joints, self.aimVector)


    def postbuild(self):
        super().postbuild()
        
        cmds.parent(self.joints[0], self.jointsParent)
       
        # The default is to have 5 main controls, if it's correct we can set the skinning correctly as well as 
        # make spaces for the hammock rig.
        if self.mainCurveSkinweights == None:
            self.mainCurveSkinweights = self.getMajorCurveSkinInfluenceTupleList()
        
        if self.mainCurveSkinweights:
            for cv in range(len(self.mainCurveSkinweights)):
                weight_tuples = self.mainCurveSkinweights[cv]
                cmds.skinPercent (self.curve_skincluster, "{}.cv[{}]".format(self.curve, cv), transformValue=weight_tuples)
        
        if self.mainControlSpace == "tailToHead":
            self.createTailToHeadSpaceSwitching()
        elif self.mainControlSpace == "headToTail":
            self.createHeadToTailSpaceSwitching()
        else:
            # Create spaces
            if isBitMultipleInteger(self.controlDivisions):
                self.createHammockSpacing()
            
        # Delete the rail
        cmds.delete(self.rail)


    def getMajorCurveSkinInfluenceTupleList(self):
        ''' get a list of influence and weights for the major spline driving tweaks '''
        
        skinning_tuple_list = []
        
        cv_count = cmds.getAttr(self.curve+".spans") + cmds.getAttr(self.curve+".degree")
        
        for ii in range(cv_count):
            if ii == 0:
                skinning_tuple_list.append( [ (self.main_controls[0].name, 1.0) ] )
            elif ii == 1:
                skinning_tuple_list.append( [ (self.main_controls[0].name, 0.7), (self.main_controls[1].name, 0.3) ] ),
            elif ii == cv_count - 2 :
                skinning_tuple_list.append( [ (self.main_controls[-2].name, 0.7), (self.main_controls[-1].name, 0.3) ] ),
            elif ii == cv_count - 1:
                skinning_tuple_list.append( [ (self.main_controls[-1].name, 1.0) ] )
            else:
                skinning_tuple_list.append( [ (self.main_controls[ii-1].name, 1.0) ] )
                
        return skinning_tuple_list


    def createHammockSpacing(self):
        self.hammock_transforms = [None] + coordspace_pylib.constrain_halfway_transforms(self.main_controls, []) + [None]
        cmds.parent(self.hammock_transforms, self.worldspace_dag)
        
        for ii, control in enumerate(self.main_controls):
            if ii == 0:
                coordspace_pylib.createSpaceSwitch( control.name,
                                                    ['rig', self.head_control.name, self.tail_control.name], 
                                                    nicenames='world:head:tail',
                                                    type='parent', 
                                                    default=2
                )
            elif (ii == len(self.main_controls)-1):
                coordspace_pylib.createSpaceSwitch( control.name,
                                                    ['rig', self.head_control.name, self.tail_control.name], 
                                                    nicenames='world:head:tail',
                                                    type='parent', 
                                                    default=1
                )
            else:
                hammock_transform_name = MayaName(control.name)
                hammock_transform_name.descriptor += "HammockSpace"
                hammock_transform_name.category = "Null"

                coordspace_pylib.createSpaceSwitch( control.name,
                                                    ['rig', self.head_control.name, self.tail_control.name, hammock_transform_name], 
                                                    nicenames='world:head:tail:hammock',
                                                    type='parent', 
                                                    default=3
                )

            
    def createHeadToTailSpaceSwitching(self):
        
        # space switching
        next_control = None
        
        for jj, control in enumerate(self.main_controls):
        
            if (jj + 1) == len(self.main_controls):
                next_control = None
            else:
                next_control = self.main_controls[jj+1]
            
            
            if next_control:
                coordspace_pylib.createSpaceSwitch( control.name,
                                                    ['rig', self.head_control.name, self.tail_control.name, next_control.name], 
                                                    nicenames='world:head:tail:next',
                                                    type='parent', 
                                                    default=2
                )
            else:
                coordspace_pylib.createSpaceSwitch( control.name,
                                                    ['rig', self.head_control.name, self.tail_control.name],
                                                    nicenames='world:head:tail',
                                                    type='parent',
                                                    default=1
                )
                
    def createTailToHeadSpaceSwitching(self):
        
        # space switching
        previous_control = None
        
        for jj, control in enumerate(self.main_controls):
            
            if previous_control:
                coordspace_pylib.createSpaceSwitch( control.name,
                                                    ['rig', self.head_control.name, self.tail_control.name, previous_control.name], 
                                                    nicenames='world:head:tail:previous',
                                                    type='parent', 
                                                    default=1
                )
            else:
                coordspace_pylib.createSpaceSwitch( control.name,
                                                    ['rig', self.head_control.name, self.tail_control.name], 
                                                    nicenames='world:head:tail',
                                                    type='parent',
                                                    default=2
                )
            previous_control = control    
            
def isBitMultipleInteger(number):
    output = number
    
    while output > 2.1:
        output = float(output) / 2.0
        
    if output == 2.0:
        return True
    else:
        return False

def constrain_halfway_point(transforms, others):
    def split_list(l, even, odd):
        def sub(index, l, odd, even):
            try:
                if index % 2 == 0:
                    even.append(l[index])
                else:
                    odd.append(l[index])
            except IndexError: # we've reached the end of the list
                return odd, even
    
            return sub(index+1, l, odd, even) # recursive call by advancing the index
        return sub(0, l, [], [])
        
    
    even, odd = split_list(transforms, [], [])
    
    if len(odd) == 3:
        cmds.parentConstraint(odd[0], odd[1])
        cmds.parentConstraint(odd[2], odd[1])

        cmds.parentConstraint(odd[0], even[0])
        cmds.parentConstraint(odd[1], even[0])
        
        cmds.parentConstraint(odd[1], even[1])
        cmds.parentConstraint(odd[2], even[1])
    else:
        half_index = int((len(transforms) + 1) / 2)
        
        # Constrain the middle and ends
        cmds.parentConstraint(transforms[0], transforms[half_index-1])
        cmds.parentConstraint(transforms[-1], transforms[half_index-1])

        others = [transforms[:half_index], transforms[half_index-1:]]
    
        if len(others[0]) == 2:
            return True
    
        constrain_halfway_point(others[0], [])
        constrain_halfway_point(others[1], [])
    
