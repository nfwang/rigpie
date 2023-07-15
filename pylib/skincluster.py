
import json
import os
import functools

import maya.cmds as cmds
import maya.mel as mel
import xml.etree.ElementTree

import rigpie.pylib.joint as joint_pylib

def skinAs(source, target, removeUnused=False):
    ''' Copy one objects skinweights and influences to another object without a skincluster.'''
    
    source_skincluster = findRelatedSkinCluster(source)
    influences = cmds.skinCluster(source_skincluster, inf=True, q=True)
    
    cmds.select(influences)
    target_skincluster = cmds.skinCluster(target, influences, bindMethod=0, toSelectedBones=True)[0]
    
    cmds.copySkinWeights( ss=source_skincluster, ds=target_skincluster, surfaceAssociation="closestPoint", influenceAssociation=["label","closestJoint"], noMirror=True, normalize=True)

    if removeUnused:
        removeUnusedInfluences(target_skincluster)

    return target_skincluster

def selectVertsGreaterThanThreshold(mesh_objects, threshold=4):
    ''' select all the verts who have influences count higher than threshold '''
    
    for mesh in mesh_objects:
        skincluster = findRelatedSkinCluster(mesh_objects)
        if not skincluster:
            cmds.warning( "skincluster.selectVertsGreaterThanThreshold(): no valid skincluster found on {}".format(mesh))
            continue
        
        for mesh in cmds.skinCluster(skincluster, q=True, geometry=True):
            vertices = cmds.polyListComponentConversion(mesh, toVertex=True)
            vertices = cmds.filterExpand(vertices, selectionMask=31)  # polygon vertex

            res = []
            for vert in vertices:
                joints = cmds.skinPercent(skincluster, vert, query=True, ignoreBelow=0.000001, transform=None)

                if len(joints) > threshold:
                    res.append(vert)

    cmds.select(res)
    

def copyAvgWeights(normalize=True):
    ''' Copy the average skincluster weights from the selected points. '''
    selection = cmds.ls(selection=True, flatten=True)
    mesh = cmds.ls(selection=True, objectsOnly=True)
    
    try:
        skincluster = findRelatedSkinCluster (mesh[0])
    except IndexError:
        print ("skincluster.copyAvgWeights(): Please select a mesh vert.")
    
    master_dict = {}
    averaged_weights = {}
    count = 0
    
    for sel in selection:
        try:
            transforms = cmds.skinPercent( skincluster, sel, ignoreBelow=0.00001, query=True, t=None )
        except RuntimeError:
            print ("skincluster.copyAvgWeights(): No verts selected")
        values = cmds.skinPercent( skincluster, sel, ignoreBelow=0.00001, query=True, value=True )
        
        weight_dict = {}
        if transforms:
            for index in range(len(transforms)):
                weight_dict[transforms[index]] = values[index]
            master_dict[count] = weight_dict
        else:
            print ("skincluster.copyAvgWeights(): No joints influencing selected points")
        count += 1

    weight_keys = []
    for ii in range(len(master_dict)):
        for k in master_dict[ii].keys():
            if k not in weight_keys:
                weight_keys.append(k)

    count = 0
    for key in weight_keys:
        weight_sum = 0
        count_sum = 0
        for ii in range(len(master_dict)):
            count_sum += 1
            if key in master_dict[ii].keys():
                weight_sum += master_dict[ii][k]
        count += 1

        #round off weight values
        average_value = weight_sum/count_sum
        averaged_weights[key] = round(average_value, 4)

    if normalize:
        keys = list(averaged_weights.keys())
        
        values = []
        for key in keys:
            values.append(averaged_weights[key])
        if values:
            sum = functools.reduce(lambda x,y:x+y, values)
            values = [ x/(sum*1.0)*normalize for x in values]
            
            for ii in range(len(values)):
                key = keys[ii]
                val = values[ii]
                averaged_weights[key] = val
        else:
            return
            
    return averaged_weights

def pasteAvgWeights(avgWts):
    '''Apply the copyAvgWeights dictionary to the selected points'''
    
    selection = cmds.ls(selection=True, flatten=True)
    mesh = cmds.ls(selection=True, objectsOnly=True)
    
    try:
        skincluster = findRelatedSkinCluster (mesh[0])
    except IndexError:
        print ("skincluster.pasteAvgWeights(): No points selected")
        
    cmd = "skinPercent"
    for k in avgWts.keys():
        cmd += " -tv %s %s" % (k ,avgWts[k])
    cmd += " " + skincluster
    for v in selection:
        cmd += " " + v
        
    mel.eval(cmd)

def findRelatedSkinCluster(node):
    import maya.mel as mel
   
    skincluster = cmds.ls(cmds.listHistory(node), type="skinCluster")
    
    if skincluster:
        
        return skincluster[0]
        
    return None

    

def exportWeights(node, filepath):

    sc = findRelatedSkinCluster(node)
    
    if not sc:
        cmds.warning('exportWeights(): ' + node + ' is not connected to a skinCluster!')
            
    filename = node + "_skinweights.xml"
    
    attributes = ['envelope', 'skinningMethod', 'normalizeWeights', 'deformUserNormals', 'useComponents']
    cmds.deformerWeights(filename, path=filepath, export=1, attribute=attributes, deformer=sc)

    return True
    

def importWeights(filepath, autoJoint=True):
    ''' xml, using Deformer weights for speed '''
    
    filename = os.path.basename(filepath)
    path = filepath.replace(filename, "")
    node = filename.split("_skinweights.xml")[0]
    skincluster = node+"_skincluster"
    
    if not cmds.objExists(node):
        cmds.warning("importWeights(): {} does not exist.".format(node))
        return False, False
        
    root = xml.etree.ElementTree.parse(filepath).getroot()

    joints = []
    for atype in root.findall('weights'):
        jnt = atype.get('source')
        shape = atype.get('shape')
        verts = atype.get('max')
        clusterName = atype.get('deformer')

        if not cmds.objExists(jnt):
            if autoJoint:
                cmds.createNode("joint", name=jnt)
            else:
                cmds.error("importWeights(): {} does not exists in scene.  Turn on autoJoint?")
        
        joints.append(jnt)

    cmds.select(cl=1)
    cmds.select(node)
    cmds.select(joints)

    skincluster = cmds.skinCluster(node, joints, name=skincluster, tsb=1, mi=8, sm=0)[0]
    mel.eval('deformerWeights -import -deformer \"{0}\" -path \"{1}\" \"{2}\";'.format(skincluster, path, filename))

    cmds.skinPercent(skincluster, node, normalize=True)
    cmds.select(cl=1)
    
    skincluster = cmds.rename(skincluster, node+"_skincluster")    

    return skincluster, node

def removeUnusedInfluences(skincluster, target_influences=[]):
    ''' Faster version of removeUnusedInfluences '''

    influences = cmds.skinCluster(skincluster, query=True, influence=True)
    
    weighted = cmds.skinCluster(skincluster, query=True, weightedInfluence=True)
    
    unused = [inf for inf in influences if inf not in weighted]
    
    if target_influences:
        unused = [
                inf for inf in influences
                if inf in target_influences
                if inf not in weighted
                ]

    cmds.skinCluster(skincluster, e=True, removeInfluence=unused)


def toggleExportJoints(node, ignoreMissingSkinclusters=False, force=None, debug=False):
    ''' Given a skincluster, swap to the export joint, or back to a rig joint depending what is currently on the skin
        
        node: maya node with skincluster, can also be a skincluster
        ignoreMissingSkinclusters: If a skincluster isnt found just return False and don't fail
        force: possible options [None, "rig", "export"]
            - None: Swap to other type
            - "rig": Swap to rig joints
            - "export": Swap to export joints
    '''
    
    if cmds.objectType(node) == "skinCluster":
        skincluster = node
    else:
        skincluster = findRelatedSkinCluster(node)
    
    if not skincluster:
        cmds.warning('skincluster.toggleExportJoints(): {} is not connected to a skinCluster!'.format(node))
        
        if ignoreMissingSkinclusters:
            return False
    
    influences = cmds.skinCluster(skincluster, influence=True, query=True)
    influence = influences[0]
    
    to_export = True
    if force:
        if force == "rig":
            to_export = False
        elif force == "export":
            to_export = True
        else:
            cmds.error("skincluster.toggleExportJoints(): force type {} not supported.".format(force))
    else:
        if joint_pylib.isExportJoint(influence):
            to_export = False
        else:
            to_export = True
    
    if debug:
        print("skincluster.toggleExportJoints(): toggling {}, to_export: {} ".format(node, to_export))


    # rig joint
    influences = cmds.listConnections("{}.matrix".format(skincluster), source=True)
    
    for influence in influences:
        new_influence = joint_pylib.getRigFromExportJointName(influence)
        if to_export:
            new_influence = joint_pylib.getExportFromRigJointName(influence)
        
        all_connections = cmds.listConnections(influence + ".worldMatrix[0]", plugs=True, destination=True)
        
        ii = 0
        connection = None
        for ii, conn in enumerate(all_connections):
            current_skincluster, plug = conn.split(".")
            
            if current_skincluster == skincluster:
                connection = conn
        
        find_index_start = connection.index("[")
        find_index_end = connection.index("]")

        plug_index = ""
        for ii in range(find_index_start+1, find_index_end):
            plug_index += str(connection[ii])
        
        changeInfluence(skincluster, influence, new_influence, plug_index)
        
    return True


def changeInfluence(skincluster, influence, new_influence, influence_index):
    ''' function to be used by toggleExportJoints() for multithreading '''

    cmds.connectAttr("{}.worldMatrix[0]".format(new_influence),
                     "{}.matrix[{}]".format(skincluster, influence_index), force=True
    )
    
    cmds.connectAttr("{}.objectColorRGB".format(new_influence), 
                     "{}.influenceColor[{}]".format(skincluster, influence_index), force=True
    )

    # lock influences
    lockInfluenceWeights_plug = "{}.lockInfluenceWeights".format(new_influence)
    if not cmds.objExists(lockInfluenceWeights_plug):
        cmds.addAttr(new_influence, longName="lockInfluenceWeights", shortName="liw", at="bool", defaultValue=False)

    cmds.connectAttr(lockInfluenceWeights_plug, "{}.lockWeights[{}]".format(skincluster, influence_index), force=True)

    # bind pose
    bind_pose_plug = cmds.listConnections(influence+".bindPose", plugs=True, destination=True)
    if bind_pose_plug:
        cmds.connectAttr("{}.bindPose".format(new_influence), bind_pose_plug[0], force=True)


def smoothFlood(geometry, iterations=1):
    
    if not iterations: 
        return
    
    current_tool = cmds.currentCtx()
    
    cmds.select(geometry)
    
    # get the skincluster
    skincluster = findRelatedSkinCluster(geometry)
    
    # Get skincluster influence list
    influence_list = cmds.skinCluster(skincluster,q=True,inf=True)
    
    # unlock influence
    for influence in influence_list: 
        cmds.setAttr(influence + '.lockInfluenceWeights',0)
    
    skin_paint_tool = 'artAttrSkinContext'
    if not cmds.artAttrSkinPaintCtx(skin_paint_tool, exists=True):
        cmds.artAttrSkinPaintCtx(skin_paint_tool, i1='paintSkinWeights.xpm', whichTool='skinWeights')
    
    cmds.setToolTo(skin_paint_tool)
    
    cmds.artAttrSkinPaintCtx(skin_paint_tool, edit=True, selectedattroper='smooth')
    
    # smooth
    for ii in range(iterations):
        print("skincluster.smoothFlood(): Smoothing {} at {}".format(skincluster, + str(ii+1)))
        
        for influence in influence_list:
            # Lock current influence weights
            cmds.setAttr(influence + '.lockInfluenceWeights',1)
            
            # Smooth Flood
            mel.eval('artSkinSelectInfluence artAttrSkinPaintCtx "{}"'.format(influence))

            cmds.artAttrSkinPaintCtx(skin_paint_tool, edit=True, clear=True)
            
            # Unlock current influence weights
            cmds.setAttr(influence+'.lockInfluenceWeights',0)
    
    # reset tool
    cmds.setToolTo(current_tool)