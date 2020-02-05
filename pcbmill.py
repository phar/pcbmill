from gcode import *
import tempfile
import json
import os
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import *

from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import re
import subprocess
from matplotlib.backends.backend_qt5agg import FigureCanvas 
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from shapely.geometry import mapping, shape, Point
import glob
import inspect
from gerbersort import *
from controllerview import *
from cameraview import *
#from graphview import *
from boardview import *
from processcontrollerview import *
import subprocess


class MainWindow(QMainWindow):
	count = 0
	set_gerber_files = pyqtSignal(dict)
	
	def __init__(self, parent = None):
		super(MainWindow, self).__init__(parent)
		self.mdi = QMdiArea()
		
		self.projectdir = "/tmp"
		self.setCentralWidget(self.mdi)
		bar = self.menuBar()
		self.windows = {}
		self.current_gcode = None
		self.gcodeobj = None
		
#
#		extractAction.clicked.connect(self.dummy)
#
		self.toolBar = self.addToolBar("File")
		open = QAction(QIcon("open.bmp"),"open",self)
		self.toolBar.addAction(open)

		self.app_icon = QIcon()
		self.app_icon.addFile('images/icon`.png', QtCore.QSize(64,64))
		self.setWindowIcon(self.app_icon)
	

		file = bar.addMenu("File")
		file.addAction("Open Gerber")
		file.addAction("cascade")
		file.addAction("Tiled")
		file.triggered[QAction].connect(self.windowaction)
		
		self.window = bar.addMenu("Windows")
		self.window.triggered[QAction].connect(self.windowsaction)
		self.setWindowTitle("PCB Mill")
		
		self.windows["process"] = ProcessControllerView(self)
		self.mdi.addSubWindow(self.windows["process"])
		self.windows["process"].show()
		self.window.addAction("process")

		self.windows["controller"] = ControllerView(self)
		self.mdi.addSubWindow(self.windows["controller"])
		self.windows["controller"].show()
		self.window.addAction("controller")
	
		self.windows["cam"] = CameraView(self)
		self.mdi.addSubWindow(self.windows["cam"])
		self.windows["cam"].show()
		self.window.addAction("cam")

#		self.windows["graph"] = GraphView(self)
#		self.mdi.addSubWindow(self.windows["graph"])
#		self.windows["graph"].show()
#		self.window.addAction("graph")

		self.windows["board"] = BoardView(self)
		self.mdi.addSubWindow(self.windows["board"])
		self.windows["board"].show()
		self.window.addAction("board")
		self.windows["process"].pc.new_cam_files.connect(self.windows["board"].new_cam_files)
		
		
		
		label = QLabel("Cam Config:")
		self.toolBar.addWidget(label)
		self.camsettings = QComboBox()
		self.camsettings.currentIndexChanged.connect(self.changecamsettings)
		self.toolBar.addWidget(self.camsettings)
		for fn  in self.windows["process"].pc.getCAMConfigs():
			self.camsettings.addItem(os.path.basename(fn))
		self.changecamsettings()

		label = QLabel("PCB Settings:")
		self.toolBar.addWidget(label)
		self.stocksettings = QComboBox()
		self.toolBar.addWidget(self.stocksettings)
		self.stocksettings.currentIndexChanged.connect(self.changepcbsettings)
		for fn  in self.windows["process"].pc.getPCBConfigs():
			self.stocksettings.addItem(os.path.basename(fn))
		self.changepcbsettings()

	
		subprocess.Popen(["python","./cncproxyserver.py"]) #fixme
		
		self.statusBar = QStatusBar()
		self.setStatusBar(self.statusBar)
		
		self.statusBar.show()
		self.statusBar.showMessage("is clicked")
		

	def changepcbsettings(self):
#		self.loadMillSettings()
		print("load")
		self.windows["process"].pc.loadSettings(os.path.join(self.windows["process"].pc.toolsettingsdir, self.stocksettings.currentText()))
		self.windows["process"].pc.makeVarDict()
	
	def changecamsettings(self):
		self.windows["process"].pc.loadSettings(os.path.join(self.windows["process"].pc.camsettingsdir, self.camsettings.currentText()))
		self.windows["process"].pc.makeVarDict()
		
	def windowsaction(self, q):
		print("triggered")
		self.windows[q.text()].show()
		
	def windowaction(self, q):
		print("triggered")
		
		if q.text() == "New":
			MainWindow.count = MainWindow.count+1
			sub = QMdiSubWindow()
			sub.setWidget(QTextEdit())
			sub.setWindowTitle("subwindow"+str(MainWindow.count))
			self.mdi.addSubWindow(sub)
			sub.show()
			
		if q.text() == "Open Gerber":
			self.projectdir =  QFileDialog.getExistingDirectory(None, 'Select a folder:', '/media',QFileDialog.ShowDirsOnly)
			G = GerberSort(self,self.projectdir)
			G.doneit.connect(self.windows["process"].pc.updateproject)
			G.exec_()
			
		if q.text() == "cascade":
			self.mdi.cascadeSubWindows()
			
		if q.text() == "Tiled":
			self.mdi.tileSubWindows()
		
	def dummy(self):
		pass
		
def main():
	app = QApplication(sys.argv)
	ex = MainWindow()
	ex.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
  main()
