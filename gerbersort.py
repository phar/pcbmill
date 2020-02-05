from gcode import *
import tempfile
import json
import os
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize    
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal,pyqtSlot, QObject
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import re
import subprocess
from matplotlib.backends.backend_qt5agg import FigureCanvas 
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from shapely.geometry import mapping, shape, Point
import glob
import inspect


class GerberSort(QDialog,QObject):
	doneit = pyqtSignal(tuple)
	def __init__(self,parent = None, dir = ".y"):
		self.dir = dir
		QDialog.__init__(self)
		self.dirfiles = []
		for f in os.listdir(self.dir):
			if os.path.isfile(os.path.join(self.dir,f)):
				self.dirfiles.append(f)
 
		self.setWindowModality(QtCore.Qt.ApplicationModal)
		self.gridLayout = QGridLayout(self)     
		self.setLayout(self.gridLayout)  

		self.filestack = {

'(\S+?-Top).gbr$':		{"name":"Top Copper",'var':"top_file"}, 
'(\S+?-Bottom).gbr$':		{"name":"Bottom Copper",'var':"bottom_file"}, 
'(\S+?-F_Silk).gbr$':		{"name":"Top Silkscreen",'var':"top_silk"},
'(\S+?-B_Silk).gbr$':		{"name":"Bottom Silkscreen",'var':"bottom_silk"},
'(\S+?-Edge_Cuts).gbr$':	{"name":"board outline",'var':'outline_file'},
'(\S+?-F_Mask).gbr$':		{"name":"Top Soldermask",'var':"top_soldermask"}, 
'(\S+?-B_Mask).gbr$':		{"name":"Bottom Soldermask",'var':"bottom_soldermask"}, 
'(\S+).drl$':			{"name":"Excellon Drill",'var':"drill_file"},

'(\S+).cmp':			{"name":"Top Copper",'var':"top_file"}, 
'(\S+).gpi':			{}, 
'(\S+).sol':			{"name":"Bottom Copper",'var':"bottom_file"}, 
'(\S+).plc':			{"name":"Top Silkscreen"}, 
'outline_(\S+).plc':		{"name":"board outline",'var':'outline_file'}, 
'outline_(\S+).gpi':		{"name":"board outline",'var':"outline_file_bottom"}, 
'(\S+).stc':			{"name":"Top Soldermask",'var':"top_soldermask"}, 
'(\S+).sts':			{"name":"Bottom Soldermask",'var':"bottom_soldermask"}, 
'(\S+).drd':			{"name":"Excellon Drill",'var':"drill_file"},

'(\S+?-Top).*$':		{"name":"Top Copper",'var':"top_file"}, 
'(\S+?-Bottom).*$':		{"name":"Bottom Copper",'var':"bottom_file"}, 
'(\S+?-F.Silk).*$':		{"name":"Top Silkscreen",'var':"top_silk"},
'(\S+?-B.Silk).*$':		{"name":"Bottom Silkscreen",'var':"bottom_silk"},
'(\S+?-Edge_Cuts).*$':	{"name":"board outline",'var':'outline_file'},
'(\S+?-F.Mask).*$':		{"name":"Top Soldermask",'var':"top_silk"}, 
'(\S+?-B.Mask).*$':		{"name":"Bottom Soldermask",'var':"bottom_silk"}, 
}

		self.fileoptions = {"Top Copper":"top_file","Top Copper":"top_file","Bottom Copper":"bottom_file","Top  Silk":"top_silk","BottomSilk":"bottom_silk","Top Soldermask":"top_soldermask","Bottom Soldermask":"bottom_soldermask","Outline":"outline_file","Excellon Drill":"drill_file"}


		self.projectfiles = self.buildprojectlist()
		self.makeWindow()

	def buildprojectlist(self):
		projectfiles  = {}
		for o,v in self.fileoptions.items():
			projectfiles[v] = "<none>"

		for n,v in self.filestack.items():
			for i in self.dirfiles:
				if  re.match(n,i):
					projectfiles[v['var']] = i
	
		return projectfiles
		
	def addGerberCombo(self,label, var):
		label = QLabel(label, self) 
		
		wdgt  = QComboBox()
		wdgt.addItem("<none>")
		for i in self.dirfiles:
			wdgt.addItem(i,var)

		for f,i in self.projectfiles.items():	
			if f == var:
				wdgt.setCurrentIndex(wdgt.findText(i,QtCore.Qt.MatchFixedString))
		return (label,wdgt)


	def makeWindow(self):
		title = QLabel("Gerber Picker", self)
		self.gridLayout.addWidget(title, 0, 1)
		btnline = 0	

		self.filewidgetlist =  {}

		for i,d in self.fileoptions.items():
			(label, self.filewidgetlist[d]) = self.addGerberCombo(i, d)
			self.gridLayout.addWidget(label, btnline, 0)
			self.gridLayout.addWidget(self.filewidgetlist[d], btnline, 1)
			btnline += 1

		t = QPushButton("Save", self) 
		self.gridLayout.addWidget(t, btnline, 1)
		t.clicked.connect(lambda x: self.update_filelist(x))


		t = QPushButton("Cancel", self) 
		self.gridLayout.addWidget(t, btnline, 0)
		btnline += 1
		t.clicked.connect(self.cancel)

	def cancel(self):
		self.doneit.emit()
		self.reject()
		
	def update_filelist(self,var):
		for ii,dd in self.filewidgetlist.items():
			self.projectfiles[ii] = dd.currentText()
		self.doneit.emit((self.dir, self.projectfiles))
		self.accept()

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	dir =  QFileDialog.getExistingDirectory(None, 'Select a folder:', '/media',QFileDialog.ShowDirsOnly)
	mainWin = GerberSort(dir)
	mainWin.show()
	sys.exit( app.exec_() )
