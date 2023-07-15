import maya.cmds as cmds
import maya.mel as mel

from rigpie.components.spine import Spine
from rigpie.components.head import Head
from rigpie.components.arm import Arm
from rigpie.components.leg import Leg       
from rigpie.components.hand import Hand
from rigpie.components.basic import Basic

from rigpie.components.limb import TwoSegmentLimb

from rigpie.pylib.rig import Rig
from rigpie.pylib.control import Control
from rigpie.pylib.rmath import Transform
from rigpie.pylib.mayaname import MayaName

import rigpie.pylib.shape as shape_pylib
import rigpie.pylib.constraints as constraints_pylib
import rigpie.pylib.coordspace as coordspace_pylib
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.rig as rig_pylib
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.hik as hik_pylib
import rigpie.pylib.mayatransform as mayatransform_pylib


class Biped(Rig):
    ''' Rig template for bipeds. '''
    
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)

        hip_joint_name = MayaName()
        hip_joint_name.side = 'Cn'
        hip_joint_name.descriptor = 'Hip'
        hip_joint_name.category = 'Jnt'
        
        self.hipJoint = str(hip_joint_name)
        
        # protected members
        self.hip  = ''
        self.root = ''
        self.cogA = ''
        self.cogB = ''

    def registerComponents(self):
        ''' Register biped components '''
        
        hip_joint_name = MayaName()
        hip_joint_name.side = 'Cn'
        hip_joint_name.descriptor = 'Hip'
        hip_joint_name.category = 'Jnt'
        
        self.rootJoint = str(hip_joint_name)

        # Root
        root_component_name = MayaName()
        root_component_name.side = 'Cn'
        root_component_name.descriptor = 'Root'
        root_component_name.category = 'Component'

        self.root_component = Basic( name=str(root_component_name),
                                     controlOffsets=2,
                                     matrix=self.hipJoint,
                                     rotationOrder='zxy',
                                     lockAndHide=['s'],
                                     componentMatrix=self.hipJoint
        )

        self.registerComponent(self.root_component)

        # Hips
        hips_component_name = MayaName()
        hips_component_name.side = 'Cn'
        hips_component_name.descriptor = 'Hip'
        hips_component_name.category = 'Component'

        self.hips_component = Basic( name='CnHipComponent',
                                     joint=self.hipJoint,
                                     lockAndHide=['s'],
                                     componentMatrix=self.hipJoint,
                                     offsetDescriptors=['Gimbal']
        )
        
        self.registerComponent(self.hips_component)

        # Head
        self.head_component = Head()
        self.head_component = self.registerComponent(self.head_component)
        
        # Neck
        neck_joints = []
        for ii in range(1, 5):
            neck_joint_name = MayaName()
            neck_joint_name.side = 'Cn'
            neck_joint_name.descriptor = 'Neck'
            neck_joint_name.iterator = str(ii)
            neck_joint_name.category = 'Jnt'
            
            neck_joints.append(str(neck_joint_name))
            
        neck_component_name = MayaName()
        neck_component_name.side = 'Cn'
        neck_component_name.descriptor = 'Neck'
        neck_component_name.category = 'Component'

        neck_bot_joint_name = MayaName()
        neck_bot_joint_name.side = 'Cn'
        neck_bot_joint_name.descriptor = 'NeckBot'
        neck_bot_joint_name.category = 'Jnt'

        neck_mid_joint_name = MayaName()
        neck_mid_joint_name.side = 'Cn'
        neck_mid_joint_name.descriptor = 'NeckMid'
        neck_mid_joint_name.category = 'Jnt'
        
        self.neck_component = Spine( name=str(neck_component_name),
                                     joints=neck_joints, 
                                     topanchor=self.head_component.headJoint,
                                     controlJoints=[str(neck_bot_joint_name), str(neck_mid_joint_name)],
                                     root=str(neck_bot_joint_name),
                                     chainStart=str(neck_bot_joint_name),
                                     componentMatrix=str(neck_bot_joint_name),
                                     spans=1
        )
        
        self.registerComponent(self.neck_component)

        # Chest Offset
        chest_component_name = MayaName()
        chest_component_name.side = 'Cn'
        chest_component_name.descriptor = 'Chest'
        chest_component_name.category = 'Component'      
        
        chest_joint_name = MayaName(chest_component_name)
        chest_joint_name.category = 'Jnt'
        
        self.chest_component = Basic( name=str(chest_component_name),
                                      joint=str(chest_joint_name),
                                      shapeType='square',
                                      lockAndHide=['s'],
                                      size=[20,20,17]
        )
        
        self.registerComponent(self.chest_component)


        # Spine
        spine_component_name = MayaName()
        spine_component_name.side = 'Cn'
        spine_component_name.descriptor = 'Spine'
        spine_component_name.iterator = '3'
        spine_component_name.category = 'Jnt'
        
        self.spine_component = Spine( lastControlGimbal = True,
                                      shaperJoint = str(spine_component_name),
                                      spans=1
        )
        self.registerComponent(self.spine_component)

        # Arms
        self.leftarm_component = Arm( startFkOffset = False,
                                      upAxis='Y',
                                      benderUpVector = [0, 0, 1],
                                      hingeControl = True, 
                                      benderControls = True
        )
        self.registerComponent(self.leftarm_component)

        self.lefthand_component = Hand()
        self.registerComponent(self.lefthand_component)

        # Legs
        self.leftleg_component = Leg ( startFkOffset = False,
                                       upAxis='Z',
                                       hingeControl = True, 
                                       benderControls = True
                                       
        )
        self.registerComponent(self.leftleg_component)
        
        self.rightleg_component = self.leftleg_component.mirror()
        self.registerComponent(self.rightleg_component)
        
        self.rightarm_component = self.leftarm_component.mirror()
        self.registerComponent(self.rightarm_component)
        
        self.righthand_component = self.lefthand_component.mirror()
        self.registerComponent(self.righthand_component)
        
        jaw_component_name = MayaName()
        jaw_component_name.side = 'Cn'
        jaw_component_name.descriptor = 'Jaw'
        jaw_component_name.category = 'Component'       

        jaw_joint_name = MayaName(jaw_component_name)
        jaw_joint_name.category = 'Jnt'
        
        self.jaw_component = Basic( name=str(jaw_component_name), 
                                    shapeType = 'circle', 
                                    joint = str(jaw_joint_name), 
                                    lockAndHide = ['v', 's'],
                                    componentMatrix=str(jaw_joint_name))
        
        self.registerComponent(self.jaw_component)

        prop_component_name = MayaName()
        prop_component_name.side = 'Lf'
        prop_component_name.descriptor = 'Prop'
        prop_component_name.category = 'Component'       

        prop_joint_name = MayaName(prop_component_name)
        prop_joint_name.category = 'Jnt'
        
        self.leftprop_component = Basic( name=str(prop_component_name), 
                                         shapeType = 'sphere', 
                                         joint = 'LfPropJnt', 
                                         lockAndHide = ['v', 's'],
                                         componentMatrix=str(prop_joint_name),
                                         transformOffsets=1
        )
        
        self.registerComponent(self.leftprop_component)
        
        self.rightprop_component = self.leftprop_component.mirror()
        self.registerComponent(self.rightprop_component)
        

    def build(self):
        ''' The method to build all of the limbs '''
        
        super().build()

        attr = attribute_pylib.add(self.hips_component.control.name+'.gimbal', max=1, min=0, value=0)
        attribute_pylib.connectAttr(attr, self.hips_component.offset_controls[0].shape+'.visibility')

        self.lefthand_component.component_options = self.leftarm_component.component_options
        self.righthand_component.component_options = self.rightarm_component.component_options

        # parent all the components together
        cmds.parent(self.root_component.name, self.masterC.name)
        cmds.parent(self.hips_component.name, self.root_component.offset_controls[1].name)
        cmds.parent(self.neck_component.name, self.chest_component.control.name)
        cmds.parent(self.head_component.name, self.neck_component.controls[1].name)
        cmds.parent(self.jaw_component.name, self.head_component.head_gimbal_control.name)
        cmds.parent(self.leftleg_component.name, self.masterC.name)
        cmds.parent(self.rightleg_component.name, self.masterC.name)
        cmds.parent(self.chest_component.name, self.spine_component.top_spine_control.name)
        cmds.parent(self.spine_component.name, self.root_component.offset_controls[1].name)
        cmds.parent(self.leftarm_component.name, self.chest_component.control.name)
        cmds.parent(self.lefthand_component.name, self.chest_component.control.name)
        cmds.parent(self.rightarm_component.name, self.chest_component.control.name)
        cmds.parent(self.righthand_component.name, self.chest_component.control.name)
        
        cmds.parent(self.leftprop_component.name, self.leftarm_component.clavicle_control.name)
        cmds.parent(self.rightprop_component.name, self.rightarm_component.clavicle_control.name)

        # connect neck
        cmds.parentConstraint(self.head_component.head_gimbal_control.name, self.neck_component.pins['end'], maintainOffset=True)
        cmds.parent(self.neck_component.pins['start'], 'CnNeckBotCtrl')

        # connect spine
        cmds.parentConstraint(self.spine_component.top_spine_control.name, self.spine_component.pins['end'], maintainOffset=True)
        cmds.parent(self.spine_component.pins['start'], 'CnHipGimbalCtrl')

        # connect hands
        constraints_pylib.offsetParentMatrixConstraint(self.leftarm_component.sockets['end'], self.lefthand_component.components_dag, alignTo='parent')
        constraints_pylib.offsetParentMatrixConstraint(self.rightarm_component.sockets['end'], self.righthand_component.components_dag, alignTo='parent')

        # connect legs
        cmds.parent(self.leftleg_component.pins['start'], self.hips_component.control.name)
        cmds.parent(self.rightleg_component.pins['start'], self.hips_component.control.name)

        c = Control('CnSpineShaperCtrl')
        c.addTransformOffset()

        cmds.select (cl = 1)

        chest_null = cmds.group (name='CnSpineShaperDriverChestNull', empty=True)
        hip_null = cmds.group (name='CnSpineShaperDriverHipNull', empty=True)
        
        cmds.delete(cmds.parentConstraint ('CnSpineShaperCtrl', chest_null))
        cmds.delete(cmds.parentConstraint ('CnSpineShaperCtrl', hip_null))
        
        cmds.parent (chest_null, self.spine_component.top_spine_control.name)
        cmds.parent (hip_null, 'CnHipGimbalCtrl')
        hip_null_constraint = cmds.pointConstraint (chest_null, hip_null, 'CnSpineShaperAuto', maintainOffset=True)[0]
         
        cmds.addAttr ('CnSpineShaperCtrl', attributeType='float', longName='toChest', minValue=0, maxValue=1, defaultValue=.5, keyable=True)
        chest_reverse = cmds.createNode ('reverse', name='CnSpineShaperDriverReverse')
        
        cmds.connectAttr ('CnSpineShaperCtrl.toChest', '{}.inputX'.format(chest_reverse))
        cmds.connectAttr ('{}.outputX'.format(chest_reverse), '{}.{}W0'.format(hip_null_constraint, chest_null))
        cmds.connectAttr ('CnSpineShaperCtrl.toChest', '{}.{}W1'.format(hip_null_constraint, hip_null))

        # This should be in the hand component at some point
        for controls in self.leftarm_component.controls:
            controls.goToZeroPose()

        for controls in self.rightarm_component.controls:
            controls.goToZeroPose()
        
        # Create finger zero Pose
        for component in [self.lefthand_component, self.righthand_component]:
            for finger in component.finger_controls.keys():
                fingerList = component.finger_controls[finger]
                for control in fingerList:
                    key = 'finger'
                    if finger == 'Thumb':
                        key = 'thumb'
                    
                    # store rotation values for bind pose
                    xform_pylib.alignRotation(control.zero, component.zeroPoseRot[key], ignoreChildren=True)
                    for offset in control.offset_transforms:
                        xform_pylib.alignRotation(offset, component.zeroPoseRot[key], ignoreChildren=True)
                    
                    rot = cmds.getAttr(control.name+'.rotate')[0]
                    attribute_pylib.add(control.name+'.bindRotX', type='float', keyable=False, lock=0, max=None, min=None, value=rot[0])
                    attribute_pylib.add(control.name+'.bindRotY', type='float', keyable=False, lock=0, max=None, min=None, value=rot[1])
                    attribute_pylib.add(control.name+'.bindRotZ', type='float', keyable=False, lock=0, max=None, min=None, value=rot[2])
                    
                    cmds.setAttr(control.name+'.rotate', 0, 0, 0, type='float3')
            
            for control in component.controls:
                control.goToBindPose()
                
        # This should be in the hand component at some point
        for controls in self.leftarm_component.controls:
            controls.goToBindPose()

        for controls in self.rightarm_component.controls:
            controls.goToBindPose()
        

        
    def postbuild(self):
        ''' The method to connect all of the limbs together '''
        
        # import shapes, load skinweights, and zero out all the controls
        super().postbuild()

        self.leftarm_component.postbuild()
        self.rightarm_component.postbuild()
        self.leftleg_component.postbuild()
        self.rightleg_component.postbuild()

        # root offset visibility switch
        for ii, offset in enumerate(self.root_component.offset_controls):
            attr = self.master.name+'.root'+str(ii+1)
            attribute_pylib.add(attr, value=0)
            cmds.connectAttr(attr, offset.shape+'.visibility')


        ## Spaces ##
        # Head
        coordspace_pylib.createSpaceSwitch( 'CnHeadCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl'], 
                                            nicenames='world:master:masterC:root',
                                            type='orient', 
                                            addLocal=True,
                                            default=1
        )
        
        # Head Tilt Eye Follow
        # This makes the eyes tilt with the head on the z axis
        look_control = 'CnEyeLookatCtrl'
        head_joint = 'CnHeadJnt'
        
        tilt_follow_name = MayaName(look_control)
        tilt_follow_name.descriptor = tilt_follow_name.descriptor + 'TiltFollow'
        tilt_follow_name.category = 'Null'
        
        tilt_follow = mayatransform_pylib.createLocator(name=str(tilt_follow_name), parent=look_control, matrix=look_control)
        cmds.connectAttr('CnHeadComponent.Rig', tilt_follow+'Shape.visibility')
        
        tilt_follow_name.category = 'Multiplydivide'
        tilt_follow_md = cmds.createNode('multiplyDivide', n=tilt_follow_name)
        switch_attribute = attribute_pylib.add('CnHeadComponent_Options.eyeLookatTilt', value=1)
        
        cmds.connectAttr( switch_attribute, tilt_follow_md+'.input1X' )
        
        # add the rotation of the main head and gimbal together to get the tilt value
        tilt_follow_name.category = 'Plusminusaverage'
        tilt_follow_pm = cmds.createNode('plusMinusAverage', n=tilt_follow_name)
        cmds.connectAttr(self.head_component.head_gimbal_control.name+'.rotateZ', tilt_follow_pm+'.input1D[0]')
        cmds.connectAttr('CnHeadCtrl.rotateZ', tilt_follow_pm+'.input1D[1]')
        
        cmds.connectAttr( tilt_follow_pm+'.output1D', tilt_follow_md+'.input2X' )
        
        # Parent each lookat control to the tilt transform
        attribute_pylib.unlock('LfEyeLookAtZero', ['t', 'r', 's'])
        cmds.parent('LfEyeLookAtZero', tilt_follow)
        attribute_pylib.lock('LfEyeLookAtZero', ['t', 'r', 's'])

        attribute_pylib.unlock('RtEyeLookAtZero', ['t', 'r', 's'])
        cmds.parent('RtEyeLookAtZero', tilt_follow)
        attribute_pylib.lock('RtEyeLookAtZero', ['t', 'r', 's'])

       
        # Lookat Space switch
        coordspace_pylib.createSpaceSwitch( 'CnEyeLookatCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnHeadJnt'], 
                                            nicenames='world:master:masterC:root:head',
                                            type='parent',
                                            default=4
        )

        # Turn off tilt follow if the space is set to the head
        tilt_follow_name.category = 'Condition'
        tilt_follow_condition = cmds.createNode('condition', n=tilt_follow_name)
        
        cmds.connectAttr('CnEyeLookatCtrl.space', tilt_follow_condition+'.secondTerm')
        cmds.connectAttr( tilt_follow_md+'.outputX', tilt_follow_condition+'.colorIfFalseR')
        cmds.connectAttr( tilt_follow_condition+'.outColorR', tilt_follow + '.rz' )   
        
        
        coordspace_pylib.createSpaceSwitch( 'LfElbowPvCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnChestJnt', self.leftarm_component.auto_pv], 
                                            nicenames='world:master:masterC:root:chest:auto',
                                            type='parent',
                                            default=5
        )
        
        coordspace_pylib.createSpaceSwitch( 'RtElbowPvCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnChestJnt', self.rightarm_component.auto_pv], 
                                            nicenames='world:master:masterC:root:chest:auto',
                                            type='parent',
                                            default=5
        )        
        
        coordspace_pylib.createSpaceSwitch( 'LfKneePvCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', self.leftleg_component.auto_pv], 
                                            nicenames='world:master:masterC:root:auto', 
                                            type='parent', 
                                            default=4
        )
                                      
        coordspace_pylib.createSpaceSwitch( 'RtKneePvCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', self.rightleg_component.auto_pv], 
                                            nicenames='world:master:masterC:root:auto',
                                            type='parent',
                                            default=4
        )
        

        coordspace_pylib.createSpaceSwitch( 'LfWristIkCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnChestJnt'], 
                                            nicenames='world:master:masterC:root:chest', 
                                            default=1
        )
        
        coordspace_pylib.createSpaceSwitch( 'RtWristIkCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnChestJnt'], 
                                            nicenames='world:master:masterC:root:chest', 
                                            default=1
        )        

        if self.leftarm_component.benderControls:
            # Shoulders bender up vector
            coordspace_pylib.createSpaceSwitch( self.leftarm_component.upper_bender_up_controls[0].name, 
                                                ['LfClavicleJnt', 'LfShoulderJnt', 'LfShoulderHingeJnt'], 
                                                nicenames='clavicle:shoulder:hinge',
                                                ctrlParent=self.leftarm_component.upper_bender_up_controls[0].offset_transforms[0],
                                                type='parent', 
                                                default=0
            )    
            
            # Forearm bender up vector
            coordspace_pylib.createSpaceSwitch( self.leftarm_component.lower_bender_up_controls[-1].name, 
                                                ['LfElbowJnt', 'LfElbowHingeJnt', 'LfWristJnt'], 
                                                nicenames='elbow:hinge:wrist',
                                                ctrlParent=self.leftarm_component.lower_bender_up_controls[-1].offset_transforms[0],
                                                type='parent', 
                                                default=2
            )                 

        if self.rightarm_component.benderControls:
            # Shoulders bender up vector
            coordspace_pylib.createSpaceSwitch( self.rightarm_component.upper_bender_up_controls[0].name, 
                                                ['RtClavicleJnt', 'RtShoulderJnt', 'RtShoulderHingeJnt'], 
                                                nicenames='clavicle:shoulder:hinge',
                                                ctrlParent=self.rightarm_component.upper_bender_up_controls[0].offset_transforms[0],
                                                type='parent', 
                                                default=0
            )        
            # Forearm bender up vector
            coordspace_pylib.createSpaceSwitch( self.rightarm_component.lower_bender_up_controls[-1].name, 
                                                ['RtElbowJnt', 'RtElbowHingeJnt', 'RtWristJnt'], 
                                                nicenames='elbow:hinge:wrist',
                                                ctrlParent=self.rightarm_component.lower_bender_up_controls[-1].offset_transforms[0],
                                                type='parent', 
                                                default=2
            )        

        
        # Fk Arms
        shoulder_control = Control('LfShoulderFkCtrl')
        shoulder_control.goToZeroPose()
        shoulder_control.addTransformOffset()
        
        coordspace_pylib.createSpaceSwitch( shoulder_control.name, 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnChestJnt'], 
                                            nicenames='world:master:masterC:root:chest',
                                            type='orient', 
                                            addLocal=True,
                                            default=4
        )
        shoulder_control.goToBindPose()
        
        shoulder_control = Control('RtShoulderFkCtrl')
        shoulder_control.goToZeroPose()
        shoulder_control.addTransformOffset()

        coordspace_pylib.createSpaceSwitch( shoulder_control.name, 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnChestJnt'], 
                                            nicenames='world:master:masterC:root:chest',
                                            type='orient', 
                                            addLocal=True,
                                            default=4
        )
        shoulder_control.goToBindPose()
        
        # Prop Ctrl
        coordspace_pylib.createSpaceSwitch( self.leftprop_component.control.name, 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'LfWristJnt'], 
                                            nicenames='world:master:masterC:root:wrist',
                                            type='parent', 
                                            addLocal=True,
                                            default=4
        )

        coordspace_pylib.createSpaceSwitch( self.rightprop_component.control.name, 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'RtWristJnt'], 
                                            nicenames='world:master:masterC:root:wrist',
                                            type='parent', 
                                            addLocal=True,
                                            default=4
        )
        
        # Ik Legs
        coordspace_pylib.createSpaceSwitch( 'LfAnkleIkCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnHipCtrl'],
                                            nicenames='world:master:masterC:root:hips',
                                            type='parent',
                                            default=1
                                      
        )
        
        coordspace_pylib.createSpaceSwitch( 'RtAnkleIkCtrl',
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl', 'CnHipCtrl'],
                                            nicenames='world:master:masterC:root:hips',
                                            type='parent',
                                            default=1
        )

        
        # Fk Legs
        thigh_control = Control('LfThighFkCtrl')
        thigh_control.goToZeroPose()
        thigh_control.addTransformOffset()
        
        coordspace_pylib.createSpaceSwitch( thigh_control.name, 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl'], 
                                            nicenames='root:master:masterC:root',
                                            type='orient', 
                                            addLocal=True,
                                            default=3
        )
        thigh_control.goToBindPose()

        thigh_control = Control('RtThighFkCtrl')
        thigh_control.goToZeroPose()
        thigh_control.addTransformOffset()
        
        coordspace_pylib.createSpaceSwitch( thigh_control.name,
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl'], 
                                            nicenames='root:master:masterC:root',
                                            type='orient', 
                                            addLocal=True,
                                            default=3
        )
        thigh_control.goToBindPose()
        
        
        if self.leftleg_component.benderControls:
            # Thighs bender up vector
            coordspace_pylib.createSpaceSwitch( self.leftleg_component.upper_bender_up_controls[0].name, 
                                                ['CnHipJnt', 'LfThighJnt', 'LfThighHingeJnt'], 
                                                ctrlParent=self.leftleg_component.upper_bender_up_controls[0].offset_transforms[0],
                                                nicenames='root:thigh:hinge',
                                                type='parent', 
                                                default=0
            )
            
            # Knee bender up vector
            coordspace_pylib.createSpaceSwitch( self.leftleg_component.lower_bender_up_controls[-1].name, 
                                                ['LfKneeJnt', 'LfKneeHingeJnt', 'LfAnkleJnt', ], 
                                                nicenames='knee:hinge:ankle',
                                                ctrlParent=self.leftleg_component.lower_bender_up_controls[-1].offset_transforms[0],
                                                type='parent', 
                                                default=1
            )                  
        
        if self.rightleg_component.benderControls:
            # Thighs bender up vector
            coordspace_pylib.createSpaceSwitch( self.rightleg_component.upper_bender_up_controls[0].name, 
                                                ['CnHipJnt', 'RtThighJnt', 'RtThighHingeJnt'], 
                                                ctrlParent=self.rightleg_component.upper_bender_up_controls[0].offset_transforms[0],
                                                nicenames='root:thigh:hinge',
                                                type='parent', 
                                                default=0
            )
            # Knee bender up vector
            coordspace_pylib.createSpaceSwitch( self.rightleg_component.lower_bender_up_controls[-1].name, 
                                                ['RtKneeJnt', 'RtKneeHingeJnt', 'RtAnkleJnt'], 
                                                nicenames='knee:hinge:ankle',
                                                ctrlParent=self.rightleg_component.lower_bender_up_controls[-1].offset_transforms[0],
                                                type='parent',
                                                default=1
            )
        
        # Top Chest Control
        coordspace_pylib.createSpaceSwitch( 'CnSpineTopCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl'], 
                                            nicenames='world:master:masterC:root',
                                            type='orient',
                                            default=4,
                                            addLocal=True
        )
        
        # Base neck
        coordspace_pylib.createSpaceSwitch( 'CnNeckBotCtrl', 
                                            [self.worldspace_dag, self.master.name, self.masterC.name, 'CnRootCtrl'], 
                                            nicenames='world:master:masterC:root',
                                            type='orient',
                                            addLocal=True,
                                            default=4
        )
        
        attribute_pylib.add(self.neck_component.component_options+'.shaper')
        cmds.connectAttr(self.neck_component.component_options+'.shaper', self.neck_component.shaper.shape + '.visibility')
        
        
        # Create a no flip transform for 180 degree freedom
        # neck start up vector
        neckStart_noflip_transform = coordspace_pylib.createNoFlipAutoTransform('CnNeckStartPv1Ctrl', 
                                                                                'CnNeckBotCtrl',
                                                                                referenceTransformParent='CnChestJnt',
                                                                                visibilityAttr=self.neck_component.rig_attr
        )
        coordspace_pylib.createSpaceSwitch( 'CnNeckStartPv1Ctrl', 
                                            ['CnChestJnt', 'CnNeckBotJnt', neckStart_noflip_transform], 
                                            nicenames='spine:neck:auto',
                                            type='parent',
                                            addLocal=True,
                                            default=2
        )

        # neck end up vector
        neckEnd_noflip_transform = coordspace_pylib.createNoFlipAutoTransform( self.neck_component.end_vector.name, 
                                                                               'CnHeadJnt', 
                                                                               visibilityAttr=self.neck_component.rig_attr
        )
        coordspace_pylib.createSpaceSwitch( self.neck_component.end_vector.name, 
                                            ['CnChestJnt', 'CnNeckBotJnt', 'CnHeadJnt', neckEnd_noflip_transform], 
                                            nicenames='auto:head:neck:spine',
                                            type='parent',
                                            addLocal=True,
                                            default=3
        )
        
        if self.leftarm_component.lowerTwistJnt:
            # wrist twist up vector
            leftWrist_noflip_transform = coordspace_pylib.createNoFlipAutoTransform('LfWristTwistPvCtrl', 
                                                                              'LfWristJnt', 
                                                                              upPlaneAxis='XZ',
                                                                              frontAxis=[1,0,0],
                                                                              backAxis=[-1,0,0],
                                                                              startAxis=[0,0,1],                        
                                                                              visibilityAttr=self.leftarm_component.rig_attr
            )
            
            elbow_joint = 'LfElbowJnt'
            if self.leftarm_component.hingeControl == True:
                elbow_joint = 'LfElbowHingeJnt'
            
            coordspace_pylib.createSpaceSwitch('LfWristTwistPvCtrl', 
                                         [elbow_joint, 'LfWristJnt', leftWrist_noflip_transform], 
                                         nicenames='elbow:wrist:auto',
                                         type='parent',
                                         default=2
            )

        # wrist twist up vector
        if self.leftarm_component.lowerTwistJnt:        
            rightWrist_noflip_transform = coordspace_pylib.createNoFlipAutoTransform('RtWristTwistPvCtrl', 
                                                                              'RtWristJnt', 
                                                                              upPlaneAxis='XZ',
                                                                              frontAxis=[1,0,0],
                                                                              backAxis=[-1,0,0],
                                                                              startAxis=[0,0,1],                        
                                                                              visibilityAttr=self.rightarm_component.rig_attr
            )
            
            elbow_joint = 'RtElbowJnt'
            if self.rightarm_component.hingeControl == True:
                elbow_joint = 'RtElbowHingeJnt'
            
            coordspace_pylib.createSpaceSwitch('RtWristTwistPvCtrl', 
                                         [elbow_joint, 'RtWristJnt', rightWrist_noflip_transform], 
                                         nicenames='elbow:wrist:auto',
                                         type='parent',
                                         default=2
            )

        self.characterizeHIK()
        
    def createExportRig(self):
        ''' Run createExportJoints() on all the biped components '''
        
        super().createExportRig()
        
        cmds.setAttr(self.hips_component.export_joints_end[0]+'.radius', 3)
        
        # parent biped template export joints
        # head to neck
        self.parentExportJoint(self.head_component.export_joints_start, self.neck_component.export_joints_end[0])

        # jaw to head
        self.parentExportJoint(self.jaw_component.export_joints_start, self.head_component.export_joints_start[0])

        # neck to spine
        self.parentExportJoint(self.neck_component.export_joints_start, self.chest_component.export_joints_end[0])

        # chest joint
        self.parentExportJoint(self.chest_component.export_joints_start, self.spine_component.export_joints_end[0])

        
        # spine to hips
        self.parentExportJoint(self.spine_component.export_joints_start, self.hips_component.export_joints_end[0])

        # arms to spine
        self.parentExportJoint(self.leftarm_component.export_joints_start, self.chest_component.export_joints_end[0])
        self.parentExportJoint(self.rightarm_component.export_joints_start, self.chest_component.export_joints_end[0])

        # hands to arms
        self.parentExportJoint(self.lefthand_component.export_joints_start, self.leftarm_component.export_joints_end[0])
        self.parentExportJoint(self.righthand_component.export_joints_start, self.rightarm_component.export_joints_end[0])

        # props to wrists
        self.parentExportJoint(self.leftprop_component.export_joints_start, self.leftarm_component.export_joints_end[0])
        self.parentExportJoint(self.rightprop_component.export_joints_start, self.rightarm_component.export_joints_end[0])
        
        # legs to hips
        self.parentExportJoint(self.leftleg_component.export_joints_start, self.hips_component.export_joints_end[0])
        self.parentExportJoint(self.rightleg_component.export_joints_start, self.hips_component.export_joints_end[0])
        
        
    def characterizeHIK(self, characterizeExportJoints=True):
        ''' tag controls and joints for maya hik for motion capture '''
        
        # Zero out rig
        for control in cmds.ls('*Ctrl'):
            c = Control(control)
            c.goToZeroPose()
        
        # Set legs to FK
        cmds.setAttr('LfAnkleIkCtrl.ik', False)
        cmds.setAttr('RtAnkleIkCtrl.ik', False)
        
        hik_pylib.characterizeHIK(characterizeExportJoints=characterizeExportJoints)
        
        cmds.setAttr('LfAnkleIkCtrl.ik', True)
        cmds.setAttr('RtAnkleIkCtrl.ik', True)

        # Back to bind pose
        for control in cmds.ls('*Ctrl'):
            c = Control(control)
            c.goToBindPose()    

