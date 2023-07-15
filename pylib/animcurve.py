 
import maya.cmds as cmds
import tempfile
import rigpie.pylib.mayafile as mayafile_pylib
import rigpie.pylib.attribute as attribute_pylib

source_path = (str(__file__)).replace("pylib/animcurve.py", "")
biped_anim_path = source_path + "data/biped_curves_rom.mb"
biped_anim_path = biped_anim_path.replace("\\", "/")

def loadAnimCurvesFromMayaScene(anim_curve_path=biped_anim_path):
    '''import maya file that has anim curves and connect all the imported curves'''
    
    anim_curves = mayafile_pylib.importFile(anim_curve_path)

    for ac in anim_curves:
        tokens = ac.split("_")
        
        node = ""
        for ii in range(len(tokens)):
            if ii == 0:
                node = tokens[0]
            elif ii != (len(tokens)-1):
                node = node + "_" + tokens[ii]
                
        attr = node + "." + tokens[-1]
        
        try:
            cmds.connectAttr(ac+".output", attr)
        except:
            print (ac, "->", attr)
            

def exportRigAnimCurves():
    ''' dump anim curves to a temp maya scene'''
    
    anim_curves = []
    controls = cmds.ls("*Ctrl") + cmds.ls("*Options")
    
    for ctrl in controls:
        conns = cmds.listConnections(ctrl, source=True, destination=False)
        
        if not conns:
            continue
            
        for conn in conns:
            if "animCurve" in cmds.objectType(conn):
                attribute_pylib.breakConnection(conn+".output")
                anim_curves.append(conn)
    
    cmds.select(anim_curves)
    
    filepath = (tempfile.gettempdir()).replace("\\", "/") + "/rigpie_anim_curve_dump.mb"
    cmds.file(filepath, force=True, options="v=0", exportSelected = True, type="mayaBinary")
    
    
def importRigAnimCurves():
    ''' import anim curves from exportRigAnimCurves file '''
    
    filepath = (tempfile.gettempdir()).replace("\\", "/") + "/rigpie_anim_curve_dump.mb"
    loadAnimCurvesFromMayaScene(filepath)