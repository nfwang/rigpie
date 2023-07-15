
from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.control import Control

import maya.cmds as cmds
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.constraints as constraints_pylib
import rigpie.pylib.control as control_pylib
import rigpie.pylib.xform as xform_pylib

class Component(object):
    ''' Components are system of controls '''
    
    def __init__(self, *args, **kwargs):

        if args:
            self.createFromString(args[0])
            return

        self.name = kwargs.get('name', "CnDefaultComponent") 

        # maya object or matrix to align the component transform to
        self.componentMatrix = kwargs.get('componentMatrix', None)
        
        # members
        self.controls_dag = None
        self.rig_dag = None
        self.worldspace_dag = None
        
        self.control_attr = ""
        self.rig_attr = ""
        self.worldspace_attr = ""
        
        self.component_options = None
        self.controls = []

        self.components_dag = cmds.createNode("transform", name=self.name)
        
        cmds.addAttr(self.components_dag, ln="registeredControls", dt="string")
        self.controls_attr = self.components_dag + ".registeredControls"

        self.export_joints = {} # joint and parent
        self.export_joints_start = []
        self.export_joints_end = []
        
    def createFromString(self, component):
        if cmds.objExists(component):
            self.controls_dag = component+"|Controls"
            self.rig_dag = component+"|Rig"
            self.components_dag = component
            
            for shape in cmds.listRelatives(component, shapes=True):
                if "_options" in shape:
                    self.component_options = shape
            
            control_string = cmds.getAttr(component+".registeredControls")
            self.controls = cmds.getAttr(component+".controls")

    
    def registerControl(self, control):
        # string attr on rig node that keeps track of all components for querying
        current_controls = cmds.getAttr(self.controls_attr)
        
        if not current_controls:
            current_controls = control.name
        else:
            if control.name not in current_controls:
                current_controls = current_controls + ", " + control.name
        
        cmds.setAttr(self.controls_attr, current_controls, type="string")
        self.controls.append(control)


    def addComponentOptions(self, ctrl):
        ''' Add maya shape that is instanced to all controls for component options. '''
        
        if isinstance(ctrl, Control):
            ctrl = ctrl.name
        
        # already exists
        try:
            cmds.parent(self.component_options, ctrl, s=True, add=True)
            
        except (RuntimeError, ValueError):
            limbNode = cmds.createNode("mesh", n=self.name+"_Options")
            
            control_pylib.tagAsComponentOptions(limbNode)
            tform = cmds.listRelatives(limbNode, parent=True)
            cmds.parent(limbNode, ctrl, shape=True, add=True)
            cmds.delete(tform)
            
            self.component_options = "%s|%s" % (ctrl, self.name+"_Options")
            
            # hide this so the focus on the viewport doesnt get crazy.
            try:
                cmds.setAttr(self.component_options+".visibility", False, lock=True)
                cmds.setAttr(self.component_options+".lodVisibility", False, lock=True)
            except RuntimeError:
                pass
            

    def prebuild(self):
        ''' pre build groups '''
        
        dag_group_name = MayaName(self.name)
        dag_group_name.category = "Dag"
        dag_group_name.descriptor = dag_group_name.descriptor+"Controls"
        self.controls_dag = cmds.createNode("transform", n=str(dag_group_name), parent=self.components_dag)

        dag_group_name = MayaName(self.name)
        dag_group_name.category = "Dag"
        dag_group_name.descriptor = dag_group_name.descriptor+"Rig"
        self.rig_dag = cmds.createNode("transform", n=str(dag_group_name), parent=self.components_dag)
        
        dag_group_name = MayaName(self.name)
        dag_group_name.category = "Dag"
        dag_group_name.descriptor = dag_group_name.descriptor+"Worldspace"
        self.worldspace_dag = cmds.createNode("transform", n=str(dag_group_name), parent=self.components_dag)
        cmds.setAttr(self.worldspace_dag+".inheritsTransform", 0)
        
        # create visibility attrs
        self.control_attr = attribute_pylib.add(self.components_dag+".Controls", value=1)
        self.rig_attr = attribute_pylib.add(self.components_dag+".Rig", value=1)
        self.worldspace_attr = attribute_pylib.add(self.components_dag+".WorldSpace", value=1)
        
        # connect attrs
        cmds.connectAttr(self.control_attr, self.controls_dag+".v")
        cmds.connectAttr(self.rig_attr, self.rig_dag+".v")
        cmds.connectAttr(self.worldspace_attr, self.worldspace_dag+".v")

        self.addComponentOptions(self.components_dag)


    def build(self):
        ''' component build '''

        # align the components dag with the component_matrix
        if self.componentMatrix:
            if isinstance(self.componentMatrix, str):
                xform_pylib.align(self.components_dag, self.componentMatrix)
            else:
                cmds.xform(self.components_dag, matrix=self.componentMatrix, worldSpace=True)
        
        pass

    def postbuild(self):
        ''' component postbuild '''
        
        pass
    
    def createExportJoints(self):
        ''' create separate joints for fbx export '''
        
        # Create Joints
        for joint in self.export_joints.keys():
            export_joint_name = MayaName(joint)
            export_joint_name.category = ""
            
            export_joint = cmds.createNode("joint", name=export_joint_name)
            cmds.setAttr(export_joint+".radius", cmds.getAttr(joint+".radius"))
            cmds.setAttr(export_joint+".segmentScaleCompensate", 0)
            
            xform_pylib.align(export_joint, joint)
            
            # add a attribute for reading to export joint
            cmds.addAttr(export_joint, longName="joint", dt="string")
            cmds.setAttr(export_joint+".joint", joint, type="string")

            # add a attribute for reading to rig joint
            cmds.addAttr(joint, longName="joint", dt="string")
            cmds.setAttr(joint+".joint", export_joint, type="string")

        # Parent Joints
        for joint in self.export_joints.keys():
            export_joint = joint.replace("Jnt", "")
            
            if self.export_joints[joint]:
                cmds.parent(export_joint, self.export_joints[joint].replace("Jnt",""))
                
        

        