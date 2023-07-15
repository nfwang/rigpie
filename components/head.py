 


import maya.cmds as cmds

from rigpie.components.splinecurve import SplineCurve
from rigpie.pylib.component import Component

from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.control import Control
from rigpie.pylib.rmath import Transform

import rigpie.pylib.controlshape as controlshape_pylib
import rigpie.pylib.xform as xform
import rigpie.pylib.attribute as attribute

class Head(Component):
    ''' Head with eye controls '''
    
    def __init__(self, **kwargs):
    
        kwargs['name'] = kwargs.get('name', 'CnHeadComponent')
        kwargs['componentMatrix'] = kwargs.get('componentMatrix', 'CnHeadJnt')

        super().__init__(**kwargs)
        
        self.leftEyeJoint = 'LfEyeJnt'
        self.rightEyeJoint = 'RtEyeJnt'
        self.headJoint = 'CnHeadJnt'

        # members
        self.fkroot = ''
        self.head_control = ''

    def prebuild(self):
        super().prebuild()
        
    def build(self):

        head_control_name = MayaName(self.headJoint)
        head_control_name.category = 'Ctrl'
        
        self.head_control = Control( name=head_control_name, 
                                     size=6,
                                     color='yellow', 
                                     shapeType='cube', 
                                     thickness=3, 
                                     lockAndHide=['s','v'], 
                                     depth=2,
                                     matrix=self.headJoint, 
                                     rotationOrder=self.headJoint,
                                     parent=self.controls_dag
        )
        
        self.registerControl(self.head_control)
        
        head_gimbal_control_name = MayaName(self.headJoint)
        head_gimbal_control_name.descriptor = 'HeadGimbal'
        head_gimbal_control_name.category = 'Ctrl'
        
        self.head_gimbal_control = Control( name=head_gimbal_control_name,
                                    size=5, 
                                    color=controlshape_pylib.getColorBySide(self.headJoint), 
                                    shapeType='cube', 
                                    lockAndHide=['s','v'], 
                                    depth=0,
                                    matrix=self.headJoint, 
                                    rotationOrder=self.headJoint,
                                    inputJoint=self.headJoint,
                                    parent=self.head_control.name
        )
        self.registerControl(self.head_gimbal_control)
        
        attr = attribute.add(self.head_control.name+'.gimbal', max=1, min=0, value=0)
        attribute.connectAttr(attr, self.head_gimbal_control.shape+'.visibility')
        
        ## Eye Rig ##
        left_eye_transform = Transform(self.leftEyeJoint)
        left_eye_position = left_eye_transform.getTranslation()
        left_eye_transform.setTranslation([0, left_eye_position.y, left_eye_position.z+20])

        eye_lookat_control_name = MayaName()
        eye_lookat_control_name.side = 'Cn'
        eye_lookat_control_name.descriptor =  'EyeLookat'
        eye_lookat_control_name.category = 'Ctrl'
        
        eye_lookat_control = Control( name=eye_lookat_control_name, 
                        color='yellow', 
                        shapeRotation=[90,0,0],
                        shapeType='circle', 
                        lockAndHide=['s','v'],
                        depth=2,
                        matrix=left_eye_transform, 
                        parent=self.controls_dag
        )
        
        self.registerControl(eye_lookat_control)
        
        aim_vector = [0,0,1]
        
        for eye_joint in [self.leftEyeJoint, self.rightEyeJoint]:
            eye_fk_control_name = MayaName(eye_joint)
            eye_fk_control_name.category = 'Ctrl'
            
            # fk
            eye_fk_control = Control( name=eye_fk_control_name, 
                                      color=controlshape_pylib.getColorBySide(eye_joint), 
                                      shapeType='sphere', 
                                      lockAndHide=['s','v'], 
                                      shapeRotation=[0,0,90], 
                                      rotationOrder=eye_joint,
                                      inputJoint=eye_joint, 
                                      depth=2, 
                                      matrix=eye_joint, 
                                      parent=self.controls_dag
            )

            cmds.parent(eye_fk_control.zero, self.head_gimbal_control.name)
            
            self.registerControl(eye_fk_control)

            eye_joint_transform = Transform( eye_joint )
            eye_joint_transform.translate( [0, 0, 20] )

            eye_fk_control_name.descriptor = eye_fk_control_name.descriptor + 'LookAt'
            
            aim_control = Control( name=eye_fk_control_name, 
                                   size=.5, 
                                   color=controlshape_pylib.getColorBySide(eye_joint), 
                                   shapeType='circle', 
                                   lockAndHide=['r','s','v'], 
                                   shapeRotation=[90,0,0],
                                   matrix=eye_joint_transform, 
                                   parent=eye_lookat_control.name
            )
            
            self.registerControl(aim_control)
            
            cmds.aimConstraint( aim_control.name, 
                                eye_fk_control.offset_transforms[0], 
                                aimVector=aim_vector, 
                                upVector=[0, 1, 0], 
                                worldUpType='vector', 
                                worldUpVector=[0, 1, 0] 
            )
            
    def postbuild(self):
        super().postbuild()

        # export joints
        self.export_joints[self.headJoint] = None
        self.export_joints[self.leftEyeJoint] = self.headJoint
        self.export_joints[self.rightEyeJoint] = self.headJoint
        
        self.export_joints_start = [self.headJoint]
        self.export_joints_end = [self.leftEyeJoint, self.rightEyeJoint]
