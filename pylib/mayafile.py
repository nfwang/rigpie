 

import os
import maya.cmds as cmds


def saveNewVersion(filepath=""):
    ''' Saves maya files into versions folder to keep file path consistent for referencing '''
    
    # use the existing file path if nothing is given
    if not filepath:
        filepath = cmds.file(query=1, sceneName=1)
    else:
        # if there is no scene name, rename the scene
        cmds.file(rename=filepath)
    
    filename, filetype = os.path.splitext(filepath)
    filebase = os.path.basename(filename)
    versions_path = filename + ".versions"

    latest_version = 0
    
    if filetype != ".ma":
        res = cmds.confirmDialog( title="Warning!", 
                                  message="Only maya ascii should be used!\nContinue?", 
                                  defaultButton="Cancel", 
                                  button=['Yes','Cancel'],
                                  messageAlign="center"
        )
        if res == "Yes":
            return False
    
    
    # Create a version folder if one does not exist
    if (not os.path.exists(versions_path)):
        cmds.sysFile( versions_path, makeDir=True )
    else:
        dirList = os.listdir(versions_path)
        for fname in dirList:
            # split the file twice to get the version number
            version_string = os.path.splitext(os.path.splitext(fname)[0])[1]
            version_string = version_string.lstrip(".")
            try:
                version = int(version_string)
            except:
                version = 0            
            if version > latest_version:
                latest_version = version
    
    latest_version_string = str(latest_version+1)
    new_filepath = versions_path + "/" +filebase + "." + latest_version_string.zfill(4) + filetype
    cmds.sysFile( filepath, copy=new_filepath )

    cmds.file(save=True)
    
    return True
    
def importFile(path, loadReferenceDepth="none", returnRoots=False):
    ''' return a list of imported objects
    
        loadReferenceDepth: [ "all", "none", "topOnly"]
        returnRoots: return only objects parented to world
    '''
    
    imported = []
    current_scene = cmds.ls()
    
    cmds.file(path, loadReferenceDepth=loadReferenceDepth, i=True, mergeNamespaceWithParent=True)
    
    for node in cmds.ls():
        if node not in current_scene:
            if returnRoots:
                if cmds.listRelatives(node, parent=True):
                    continue
            imported.append(node)
    
    return imported