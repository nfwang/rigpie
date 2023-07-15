 

import maya.cmds as cmds
import os
import os.path 

from rigpie.pylib.rmath import Transform
from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.control import Control

import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.control as control_pylib
import rigpie.pylib.mayafile as mayafile_pylib
import rigpie.pylib.skincluster as skincluster_pylib
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.joint as joint_pylib
import rigpie.pylib.constraints as constraints_pylib



class Rig(object):
    
    def __init__(self, *args, **kwargs):
        ## Global variables
        self.rig_dag = "rig"

        ## protected members
        self.components_dag = "rig|components"
        self.geo_dag = "rig|geo"
        self.utility_dag = "rig|utility"
        self.skeleton_dag = "rig|skel"
        self.worldspace_dag = "rig|worldspace"
        self.components = []
        
        self.master = "CnMasterCtrl"
        self.masterA = "CnWorldACtrl"
        self.masterB = "CnWorldBCtrl"
        self.masterC = "CnWorldCCtrl"
        
        ## Asset specific variables
        self.geometry_path = ""
        self.utility_path = ""
        self.skinweights_path = ""
        self.skeleton_path = ""
        self.controlshape_path = ""

        # create an export rig for the game engine
        self.exportRig = False
        self.loadSkinWeights = True

        
    def setup(self):
        ''' Setup dag nodes and import in mesh.'''

        # New Scene
        cmds.file(new=True, f=True)

        rig = cmds.createNode("transform", name=self.rig_dag)
        attribute_pylib.lockAndHide(rig, ["t","r","s","v"])
   
        cmds.addAttr(self.rig_dag, ln="registeredComponents", dt="string")
        self.component_attr = self.rig_dag + ".registeredComponents"

        ## List of components
        self.geo_dag = cmds.createNode("transform", name="geo", parent=self.rig_dag)
        self.utility_dag = cmds.createNode("transform", name="utility",  parent=self.rig_dag)
        self.skeleton_dag = cmds.createNode("transform", name="skel",  parent=self.rig_dag)
        self.worldspace_dag = cmds.createNode("transform", name="worldspace", parent=self.rig_dag)
        
        cmds.setAttr(self.worldspace_dag+".inheritsTransform", False)
        
        ## Setup visibility attrs for organization groups
        # geo
        plumin  = cmds.createNode("plusMinusAverage", name=self.geo_dag+"Vis_plumin")
        geoattr = self.rig_dag + "." + self.geo_dag

        cmds.addAttr( self.rig_dag, ln=self.geo_dag, at="enum", en="off:on:template:reference:seg", k=True )
        cmds.setAttr( self.geo_dag+".overrideEnabled", 1 )
        cmds.connectAttr( geoattr, self.geo_dag+".overrideVisibility" )
        cmds.setAttr( plumin+".operation", 2 )
        cmds.setAttr( plumin+".input1D[1]", 1 )
        cmds.connectAttr( geoattr, plumin+".input1D[0]" )
        cmds.connectAttr( plumin+".output1D", self.geo_dag+".overrideDisplayType" )
        cmds.setAttr( geoattr, 1 )
        
        # utility
        utilityattr = self.rig_dag + "." + self.utility_dag
        cmds.addAttr(self.rig_dag, ln="utility", at="long", max=1, min=0, k=True)
        cmds.setAttr(self.utility_dag+".overrideEnabled", 1)
        cmds.setAttr(utilityattr, 0)
        cmds.connectAttr(utilityattr, self.utility_dag+".overrideVisibility")

        # skel
        rig_skeleton_attr = self.rig_dag + ".rig_skeleton"
        attribute_pylib.add(rig_skeleton_attr, value=1)
        cmds.setAttr(self.skeleton_dag+".overrideEnabled", 1)
        cmds.connectAttr(rig_skeleton_attr, self.skeleton_dag+".overrideVisibility")
        
        if self.exportRig:
            self.export_skeleton_attr = self.rig_dag + ".export_skeleton"
            attribute_pylib.add(self.export_skeleton_attr, value=1)

        # world
        worldattr = self.rig_dag + "." + self.worldspace_dag
        cmds.addAttr(self.rig_dag, ln="worldspace", at="long", max=1, min=0, k=True)
        cmds.setAttr(self.worldspace_dag + ".overrideEnabled", 1)
        cmds.connectAttr(worldattr, self.worldspace_dag+".overrideVisibility")
        
        #### Import Utility ####
        self.importUtility()

        #### Import Geo ####
        self.importGeo()


    def prebuild(self):
        ''' import skeleton and run prebuild on all components '''
        
        print("rig.prebuild()...")
        
        #### Import Skeletons ####
        if self.skeleton_path != "":
            self.importSkeleton()
        
        
        # build all components
        for component in self.components:
            component.prebuild()
    
    def registerComponents(self):
        return
        
    def build (self):
        
        #### World Controls ####
        self.master = Control( name="CnMasterCtrl", 
                               size=30, 
                               shapeType="diamond2d", 
                               lockAndHide=["v"], 
                               depth=1,
                               rotationOrder="zxy",
                               parent=self.rig_dag
        )
        
        self.masterA = Control( name="CnMasterACtrl", 
                                size=25, 
                                shapeType="diamond2d", 
                                lockAndHide=["v", "s"], 
                                depth=1, 
                                rotationOrder="zxy",
                                parent=self.master.name 
        )
                               
        self.masterB = Control( name="CnMasterBCtrl", 
                                size=20, 
                                shapeType="diamond2d", 
                                lockAndHide=["v", "s"], 
                                depth=0, 
                                rotationOrder="zxy",
                                parent=self.masterA.name 
        )
                               
        self.masterC = Control( name="CnMasterCCtrl", 
                                size=15, 
                                shapeType="diamond2d", 
                                lockAndHide=["v", "s"], 
                                depth=0, 
                                rotationOrder="zxy",
                                parent=self.masterB.name 
        )

        component_options = cmds.createNode("mesh", name="World_Options")
        delete_me = cmds.listRelatives(component_options, parent=True)[0]
        
        control_pylib.tagAsComponentOptions(component_options)
        tform = cmds.listRelatives(component_options, parent=True)
        cmds.parent(component_options, self.masterA.name, s=True, add=True)
        cmds.parent(component_options, self.masterB.name, s=True, add=True)
        cmds.parent(component_options, self.masterC.name, s=True, add=True)
        cmds.parent(component_options, self.master.name, s=True, add=True)
        
        cmds.delete(delete_me)
        
        self.controls_attr = attribute_pylib.add(self.rig_dag+".controls", value=1)
        cmds.connectAttr(self.controls_attr, self.masterA.zero+".visibility")
        
        for component in self.components:
            print ("rig.build(): {}".format(component.name))
            component.build()
        
    def postbuild (self):
        # build all components
        for component in self.components:
            print ("rig.postbuild(): {}".format(component.name))
            component.postbuild()
        
        # export rig
        if self.exportRig:
            self.createExportRig()
            self.constrainExportJoints()
        
        # create skinclusters and load weights
        if self.skinweights_path != "" and self.loadSkinWeights:
            skincluster_geo = self.importSkinWeights()
        
        # reset bind poses
        cmds.delete(cmds.ls(type="dagPose"))
        
        for root_joint in cmds.listRelatives(self.skeleton_dag, children=True):
            root_joint_name = MayaName(root_joint)
            if self.exportRig:
                root_joint_name.category = ""
                
            print ("rig.postbuild(): Resetting {} Bind Pose".format(root_joint_name))
            cmds.select(root_joint_name)
            cmds.dagPose(root_joint_name, bindPose=True, save=True, selection=True)
        
        cmds.select(clear=True)

        shape_visibility_connections = {}

        # lock rig transforms
        attribute_pylib.lock(self.geo_dag, ['t', 'r', 's', 'v'])
        attribute_pylib.lock(self.utility_dag, ['t', 'r', 's', 'v'])
        attribute_pylib.lock(self.skeleton_dag, ['t', 'r', 's', 'v'])
        attribute_pylib.lock(self.worldspace_dag, ['t', 'r', 's', 'v'])
        

        # create a set for deformer binding
        cmds.select(clear=True)
        self.bind_set = cmds.sets(name="rig_bind_set")

        for component in self.components:
            # hide all how the sausage is made
            cmds.setAttr(component.rig_attr, 0)
            cmds.setAttr(component.worldspace_attr, 0)
        
            # Add all the component options now so we dont get viewport focus issues.
            for ctrl in component.controls:
                visibility_connection = cmds.listConnections(ctrl.shape + ".visibility", plugs=True, source=True)
                if visibility_connection:
                    shape_visibility_connections[ctrl.shape] = visibility_connection[0]
            

            # add the export_joint keys to the bind set for the component
            component_bind_set = cmds.sets(name=component.name + "_rig_bind_set")
            
            # if a bind_joints dict exists, use that, if not, use the export_joints
            try:
                cmds.sets(list(component.bind_joints), add=component_bind_set)
            except:
                cmds.sets(list(component.export_joints.keys()), add=component_bind_set)
                
            cmds.sets(component_bind_set, add=self.bind_set)


        # create a set for export deformer binding
        cmds.select (clear = True)
        export_bind_set = cmds.sets (name = "export_bind_set")

        if self.exportRig:
            # create component sets for export deformer building
            component_sets = cmds.sets ("rig_bind_set", q = True)
            for component_set in component_sets:

                rig_jnts = cmds.sets (component_set, q = True)

                export_jnts = []
                if rig_jnts:
                    for rig_jnt in rig_jnts:
                        export_jnt = joint_pylib.getExportFromRigJointName (rig_jnt)
                        export_jnts.append (export_jnt)
                    
                    cmds.select (export_jnts)
                else:
                    cmds.select (clear = True)

                new_set = cmds.sets (name = component_set.replace ("_rig_bind_set", "_export_bind_set"))
                cmds.sets (new_set, add = export_bind_set)
                
        
        # store all the connections attached to the shape visiblity and reconnect
        if self.controlshape_path != "":
            control_pylib.importShapes( self.controlshape_path, relative=True )
        
        # restore all of the shape visibility connections becuause theyve been replaced by the ones on disk.
        for shape in shape_visibility_connections.keys():
            try:
                cmds.connectAttr(shape_visibility_connections[shape], shape+".visibility")
            except RuntimeError:
                print ("rig.postbuild(): Could not connect {} to {}".format(shape_visibility_connections[shape], shape+".visibility"))
                pass

        # root and world offset visibility attributes
        cmds.connectAttr(attribute_pylib.add(self.master.name+".masterACtrl", value=1), self.masterA.name+"Shape.v")
        cmds.connectAttr(attribute_pylib.add(self.master.name+".masterBCtrl", value=0), self.masterB.name+"Shape.v")
        cmds.connectAttr(attribute_pylib.add(self.master.name+".masterCCtrl", value=0), self.masterC.name+"Shape.v")

        # Need to add the component options at the end of focus issues
        # The previous component loop is needed to store visibility connections
        for component in self.components:
            # Add all the component options now so we dont get viewport focus issues.
            for ctrl in component.controls:
                component.addComponentOptions(ctrl.name)

    def registerComponent(self, component):

        # string attr on rig node that keeps track of all components for querying
        current_components = cmds.getAttr(self.component_attr)
        
        if not current_components:
            current_components = ""

        cmds.setAttr(self.component_attr, current_components+"; "+component.components_dag, type="string")
        
        self.components.append(component)
        return component

    
    def importSkeleton(self):
        if not (os.path.exists(self.skeleton_path)):
            print ("rig.importSkeleton(): %s does not exist." % self.skeleton_path)
            return False
    
        # import file
        joints = []
        
        # turn off segment scale compensate to allow for rig scaling.
        for joint in (mayafile_pylib.importFile(self.skeleton_path)):
            if cmds.objectType(joint) != "joint":
                continue
            
            joints.append(joint)
            
            cmds.setAttr(joint+".segmentScaleCompensate", 0)
            
            hasParent = bool(cmds.listRelatives(joint, parent=True))
            if not hasParent:
                try:
                    self.joint_root
                except AttributeError:
                    self.joint_root = joint
                     
        
        cmds.parent(self.joint_root, self.skeleton_dag)
        
        return True

    def importGeo(self):
        if self.geometry_path != "":
            if not (os.path.exists(self.geometry_path)):
                print ("rig.importGeo(): %s does not exist." % self.geometry_path)

            geo = mayafile_pylib.importFile(self.geometry_path, returnRoots=True)
            cmds.parent(geo, self.geo_dag)
            
    def importUtility(self):
        if self.utility_path != "":
            if not (os.path.exists(self.utility_path)):
                print ("rig.importUtility(): %s does not exist." % self.utility_path)
                return False
            
            utility = mayafile_pylib.importFile(self.utility_path)
            cmds.parent(utility, self.utility_dag)
        
    
    def importSkinWeights(self):
    
        geo = []
        files = os.listdir(self.skinweights_path)

        for file in files:
            obj = file.split(".")[0]
            type = file.split(".")[-1]
            
            if type == "xml":
                print ("rig.importSkinWeights(): Loading {}".format(file))
                skincluster, node = skincluster_pylib.importWeights(self.skinweights_path+file)
                if node:
                    geo.append(node)

        return geo

        
    def inPlaceMode(self):
        ''' In place mode for cycles '''
        cmds.addAttr(self.masterA_control, ln="inPlaceMode", at="long", max=1, min=0, k=True)
        ipmattr = self.masterA_control + ".inPlaceMode"
        
        switchmd = cmds.createNode("multiplyDivide", n="inPlaceSwitch_md")
        cmds.connectAttr(ipmattr, switchmd+".input1X")
        cmds.setAttr(switchmd+".input2X", -1)
        
        md = cmds.createNode("multiplyDivide", n="inPlace_md")
        cmds.connectAttr(switchmd+".outputX", md+".input1X")
        cmds.connectAttr(self.root+".tz", md+".input2X")
        
        attribute_pylib.connectAttr(md+".outputX", self.masterA_control.replace("Ctrl", "Zero")+".tz")
    
    def createExportRig(self):
        ''' Run createExportJoints() on all the components '''

        # this is used for offsetting an asset in the game engine
        self.displacement_root_joint = cmds.createNode("joint", name="Root")
        
        # rotate joint orient to match Unreal engine
        cmds.setAttr(self.displacement_root_joint+".jointOrient", -90, 0, 0, type="float3")
        cmds.setAttr(self.displacement_root_joint+".visibility", False)
        
        self.displacement = Control( name="CnDisplacementCtrl", 
                                     size=30, 
                                     shapeType="square", 
                                     lockAndHide=["v"], 
                                     parent=self.rig_dag, 
                                     matrix=self.displacement_root_joint,
                                     inputJoint=self.displacement_root_joint,
                                     shapeRotation=[-90, 0, 0],
                                     depth=1,
                                     color="green"
        )
        
        for component in self.components:
            component.createExportJoints()

        base_joint_name = MayaName(self.joint_root)
        base_joint_name.category = ""

        cmds.parent(base_joint_name, self.displacement_root_joint)
        
        cmds.connectAttr(self.export_skeleton_attr, self.displacement_root_joint+".v")
        
        cmds.connectAttr(self.joint_root+".scale", str(base_joint_name)+".scale")
        
    def parentExportJoint(self, child, parent):
        ''' change the name of the joint to the export joint and parent. '''

        parent_joint_name = MayaName(parent)
        parent_joint_name.category = ""
        
        if isinstance(child, list):
            for cc in child:
                child_joint_name = MayaName(cc)
                child_joint_name.category = ""
        
                cmds.parent(child_joint_name, parent_joint_name)
        else:
            child_joint_name = MayaName(child)
            child_joint_name.category = ""
        
            cmds.parent(child_joint_name, parent_joint_name)
            
    def constrainExportJoints(self):
        ''' Because of offsetParentMatrix the constraint needs to happen at the end '''

        for component in self.components:
            for joint in component.export_joints.keys():
                export_joint_name = MayaName(joint)
                export_joint_name.category = ""
                
                #constraints_pylib.offsetParentMatrixConstraint(str(joint), str(export_joint_name))
                cmds.parentConstraint(str(joint), str(export_joint_name))
                #cmds.connectAttr(str(joint)+".scale", str(export_joint_name)+".scale")
        

    def removeExportJoint(self, joint, component):
        ''' remove an export joint correctly '''
        
        delete_joint_name = MayaName(joint)
        delete_joint_name.category = ""
        
        cmds.delete(str(delete_joint_name))
        component.export_joints.pop(joint)

