
from PySide2 import QtCore, QtWidgets, QtGui
import maya.cmds as cmds
import maya.mel as mel

def getMayaWindow():
    for widget in QtWidgets.QApplication.topLevelWidgets():
        try:
            if widget.objectName() == "MayaWindow":
                return widget
        except:
            pass
    print('"MayaWindow" not found.')
    return None


def show():
    
    # create dialog    
    mayaWindow = getMayaWindow()

    dialog = rigpieUtilityDialog(parent=mayaWindow)

    dialog.setWindowTitle('Rig Pie Utility')
    dialog.setObjectName('rigpieUtilityWindow')

    dialog.show()
    
    
class rigpieUtilityDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        main_vbox = QtWidgets.QVBoxLayout(self)
        
        # menu bar
        menu_hbox = QtWidgets.QHBoxLayout(self)
        
        self.menuBar = QtWidgets.QMenuBar(parent=parent) # requires parent
        self.settings_menu = QtWidgets.QMenu(self)
        self.settings_menu.setTitle("Settings")
        self.menuBar.addMenu(self.settings_menu)
        self.settings_menu.addAction("Anim Friendly")
        self.settings_menu.triggered[QtWidgets.QAction].connect(self.selectAllControls)
        
        menu_hbox.addWidget(self.menuBar)
        main_vbox.addLayout(menu_hbox)
        
        # select group
        rowa_hbox = QtWidgets.QHBoxLayout(self)
        select_vbox = QtWidgets.QVBoxLayout(self)
        select_group = QtWidgets.QGroupBox(self)
        select_group.setTitle("Select Controls")
        
        self.select_all_btn = QtWidgets.QPushButton(self)
        self.select_all_btn.setText("All")
        self.select_all_btn.setMaximumWidth(80)
        self.select_all_btn.setToolTip('Select All Controls on scene')
        self.select_all_btn.clicked.connect(self.updateUI)
        
        select_vbox.addWidget(self.select_all_btn)

        self.select_component_controls_btn = QtWidgets.QPushButton(self)
        self.select_component_controls_btn.setText("Component")
        self.select_component_controls_btn.setMaximumWidth(80)
        self.select_component_controls_btn.setToolTip('Select Controls of a selected controls components')
        self.select_component_controls_btn.clicked.connect(self.updateUI)

        select_vbox.addWidget(self.select_component_controls_btn)

        select_group.setLayout(select_vbox)
        
        rowa_hbox.addWidget(select_group)
        main_vbox.addLayout(rowa_hbox)
        
    def updateUI(self):
        ''' Update the UI '''
        
        pass

    def selectAllControls(self):
        pass
        
    def closeEvent( self, event ):
        super().closeEvent( event )

