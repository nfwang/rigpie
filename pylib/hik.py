 
import os

import json
import maya.cmds as cmds
import maya.mel as mel
from rigpie.pylib.control import Control

# get the package's version of the BipedHIK.xml
source_path = (str(__file__)).replace("pylib\\hik.py", "")
biped_xml_path = source_path + "data\\BipedHIK.xml"
biped_xml_path = biped_xml_path.replace("\\", "/")

def characterizeHIK(characterizeExportJoints=True):
    ''' tag export joints for maya's human ik '''

    # load hik libraries
    mel.eval('ToggleCharacterControls;')
    
    # create a generic hik to load custom rig xml
    biped_hik = mel.eval('hikCreateCharacter("BipedHIK");')
    
    joint_prefix = ""
    if characterizeExportJoints:
        mel.eval('setCharacterObject("Root","{}",0,0);'.format(biped_hik))
    else:
        joint_prefix = "Jnt"
        
    # tag joints
    lines = [
        'setCharacterObject("CnHead{}","{}",15,0);',
        'setCharacterObject("CnHip{}","{}",1,0);',
        'setCharacterObject("CnNeck1{}","{}",20,0);',
        'setCharacterObject("CnNeck2{}","{}",32,0);',
        'setCharacterObject("CnNeck3{}","{}",33,0);',
        'setCharacterObject("CnSpine2{}","{}",8,0);',
        'setCharacterObject("CnSpine3{}","{}",23,0);',
        'setCharacterObject("CnSpine4{}","{}",24,0);',
        'setCharacterObject("LfAnkle{}","{}",4,0);',
        'setCharacterObject("LfBall{}","{}",16,0);',
        'setCharacterObject("LfClavicle{}","{}",18,0);',
        'setCharacterObject("LfElbow{}","{}",10,0);',
        'setCharacterObject("LfIndex1{}","{}",54,0);',
        'setCharacterObject("LfIndex2{}","{}",55,0);',
        'setCharacterObject("LfIndex3{}","{}",56,0);',
        'setCharacterObject("LfKnee{}","{}",3,0);',
        'setCharacterObject("LfMiddle1{}","{}",58,0);',
        'setCharacterObject("LfMiddle2{}","{}",59,0);',
        'setCharacterObject("LfMiddle3{}","{}",60,0);',
        'setCharacterObject("LfPinky1{}","{}",66,0);',
        'setCharacterObject("LfPinky2{}","{}",67,0);',
        'setCharacterObject("LfPinky3{}","{}",68,0);',
        'setCharacterObject("LfRing1{}","{}",62,0);',
        'setCharacterObject("LfRing2{}","{}",63,0);',
        'setCharacterObject("LfRing3{}","{}",64,0);',
        'setCharacterObject("LfShoulder{}","{}",9,0);',
        'setCharacterObject("LfThigh{}","{}",2,0);',
        'setCharacterObject("LfThumb1{}","{}",50,0);',
        'setCharacterObject("LfThumb2{}","{}",51,0);',
        'setCharacterObject("LfThumb3{}","{}",52,0);',
        'setCharacterObject("LfWrist{}","{}",11,0);',
        'setCharacterObject("RtAnkle{}","{}",7,0);',
        'setCharacterObject("RtBall{}","{}",17,0);',
        'setCharacterObject("RtClavicle{}","{}",19,0);',
        'setCharacterObject("RtElbow{}","{}",13,0);',
        'setCharacterObject("RtIndex1{}","{}",78,0);',
        'setCharacterObject("RtIndex2{}","{}",79,0);',
        'setCharacterObject("RtIndex3{}","{}",80,0);',
        'setCharacterObject("RtKnee{}","{}",6,0);',
        'setCharacterObject("RtMiddle1{}","{}",82,0);',
        'setCharacterObject("RtMiddle2{}","{}",83,0);',
        'setCharacterObject("RtMiddle3{}","{}",84,0);',
        'setCharacterObject("RtPinky1{}","{}",90,0);',
        'setCharacterObject("RtPinky2{}","{}",91,0);',
        'setCharacterObject("RtPinky3{}","{}",92,0);',
        'setCharacterObject("RtRing1{}","{}",86,0);',
        'setCharacterObject("RtRing2{}","{}",87,0);',
        'setCharacterObject("RtRing3{}","{}",88,0);',
        'setCharacterObject("RtShoulder{}","{}",12,0);',
        'setCharacterObject("RtThigh{}","{}",5,0);',
        'setCharacterObject("RtThumb1{}","{}",74,0);',
        'setCharacterObject("RtThumb2{}","{}",75,0);',
        'setCharacterObject("RtThumb3{}","{}",76,0);',
        'setCharacterObject("RtWrist{}","{}",14,0);'
    ]

    for line in lines:
        mel.eval(line.format(joint_prefix, biped_hik))

    mel.eval('hikUpdateDefinitionUI;')
    mel.eval('hikToggleLockDefinition();')