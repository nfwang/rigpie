 

from PySide2 import QtCore, QtWidgets, QtGui
import os

def getMayaWindow():
    for widget in QtWidgets.QApplication.topLevelWidgets():
        try:
            if widget.objectName() == "MayaWindow":
                return widget
        except:
            pass
    print('"MayaWindow" not found.')
    
    return None
