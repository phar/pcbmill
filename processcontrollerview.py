import sys
import numpy
import cv2
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize ,QTimer
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal,pyqtSlot, QObject
import os
from gcode import *
import inspect
import glob
import json

class ProcessController(QObject):
	next_process = pyqtSignal(int)
	begin_process = pyqtSignal()
	end_process = pyqtSignal()
	settings_update =  pyqtSignal(dict)
#	new_process_file = pyqtSignal(GcodeFile)
	new_cam_files = pyqtSignal(GcodeFile)

	def __init__(self,parent, cnccb):
		QObject.__init__(self)
		self.cnccb = cnccb
		self.parent = parent
		self.millsettings = {}
		self.settingsdict ={}
		self.variables = {}
		self.projectdir = "/tmp"
#		self.millsettingsfile = "mill_settings.json"
		self.scriptdir = "flatcam_scripts"
		self.cncscriptdir = "cnc_scripts"
		self.toolsettingsdir = "processes"
		self.camsettingsdir = "camsettings"
		self.process_step_index = None
		self.projectfiles = {}
		self.completed_steps = []
		
#		self.loadMillSettings()
		self.next_process.connect(self.parent.updateprocess)
		self.parent.millsettings_update.connect(self.millsettings_update)


		self.process = [
#			("Process Gerber Files", lambda x: self.dummy(x)),

			("Init Mill",lambda: self.cnccb.send_command("HOMEMILL"),[]),
			("Set PCB Origin",lambda: self.runlinuxcncjob("set_pcb_origin.txt"),[]),
			("Process Drills", lambda: self.runCAM2("drills"),[]),
			
			
			("Change to first Drill",lambda : self.dummy(),[]),
			("tool change complete",lambda : self.dummy(),[]),
			("Probe && Drill Topside",lambda : self.dummy(),[]),
			("Calibrate Cam To Drills",lambda : self.dummy(),[]),
			
			
			("Process Top Side", lambda: self.runCAM2("top"),[]),
			("Change to Milling Tool",lambda x: self.dummy(x),[]),
			("Tool change complete",lambda x: self.dummy(x),[]),
			("Align Top Side",lambda x: self.dummy(x),[]),
			("Probe && Mill Topside",lambda x: self.dummy(x),[]),


			("Process Bottom Side", lambda: self.runCAM2("bottom"),[]),
			("Move milling tool to changetool height",lambda x: self.dummy(x),[]),
			("tool change complete",lambda x: self.dummy(x),[]),
			("Align Bottom Side",lambda x: self.dummy(x),[]),
			("Probe && Mill Bottom side", lambda x: self.dummy(x),[]),

			("Process Outline", lambda: self.runCAM2("cutout"),[]),
			("Move milling tool to changetool height", lambda x: self.dummy(x),[]),
			("tool change complete",lambda x: self.dummy(x),[]),
			("Align Bottom Side",lambda x: self.dummy(x),[]),
			("Cut-out Bottom side",lambda x: self.dummy(x),[]),

			("Move milling tool to changetool height",lambda x: self.dummy(x),[]),
			("tool change complete",lambda x: self.dummy(x),[])
			]
		
	def millsettings_update(self, settings):
		self.millsettings = settings
		
	def patchTemplateFileToFile(self,patchdict, template,dst=None):
		if dst == None:
			(dfd, dst) = tempfile.mkstemp()
		else:
			dfd = os.open(dst,os.O_RDONLY)
		print("wrote %s for %s" % (dst, inspect.stack()[1][3]))
		sf = open(template,"r")
		ll = sf.readlines()
		for l in ll:
			line = l.strip()
			for  v,vv in patchdict.items():
				if  '%' + ("%s"  % v) + '%'  in line:
					line = line.replace('%' + ("%s"  % v) + '%', str(vv))
			os.write(dfd,b"%s\n" % bytearray(line,"utf-8"))
		sf.close()
		os.close(dfd)
		return dst

	def setCurrentGcode(self, filename):
		self.gcodeobj = GcodeFile(self.projectdir, filename)
		self.gcoodefilename = filename
		self.set_gcode.emit(self.gcodeobj)

	def getProcessName(self,i):
		return self.process[i][0]
		
	def getProcess(self,i):
		return self.process[i]

	def getProcessList(self):
		l = []
		for (n,fn,req) in self.process:
			l.append((n,req))
		return l
		
	def __getitem__(self, i):
		return self.settingsdict[i]
	
	def __setitem__(self, i, d):
		self.settingsdict[i] = d

	def updateproject(self,prjectuple):
		self.projectdir = prjectuple[0]
		self.projectfiles = prjectuple[1]
		self.process_step_index = None
		self.makeVarDict()
		self.nextProcess()
		self.begin_process.emit()

	def mill_init(self):
#		os.system("%s homeall.py" % self.settings['linuxcnc_python'])
		print("init mill")
		
	def runCurrentProcess(self):
		if self.process[self.process_step_index][1]():
			self.completed_steps.append(self.process_step_index)
		
	def nextProcess(self):
		print(self.process_step_index)
		if self.process_step_index == None:
			self.process_step_index = 0
		else:
			if (self.process_step_index +1) < len(self.process):
				self.process_step_index+= 1
			else:
				self.end_process.emit()
				return
				
		self.next_process.emit(self.process_step_index)
	
	def setProcessStep(self,step):
		i = 0
		
		for (n,fn,req) in self.process:
			if step == n:
				if step != self.process_step_index:
					self.process_step_index = i
					self.next_process.emit(self.process_step_index)
					return
			i += 1
			
	
	def dummy(self,x ):
		print("DUMMY",x)
		
	def runCAM(self,camscript):
		r = None
		self.camscript = self.patchTemplateFileToFile(self.variables,os.path.join( self.scriptdir,camscript))
		try:
			r = os.system("%s %s --shellfile=%s" % (self['flatcam_python'],self['flatcam'],self.camscript))
			#fixme detect errors!
		finally:
			os.remove(self.camscript)
		if r == None:
			return 0
		elif r == 0:
			return 1
		else:
			return 0

	def runCAM2(self, camevent):
		r = 0
		self.makeVarDict()
		print(self.variables)
		if camevent == "top":
			cam_files =  "top.nc"
			r = self.runCAM("flatcam_process_top.txt")
		elif camevent == "bottom":
			cam_files =   "bottom.nc"
			r= self.runCAM("flatcam_process_bottom.txt")
		elif camevent == "drills":
			cam_files =   "topdrill.nc"
			r = self.runCAM("flatcam_process_drills.txt")
		elif camevent == "cutout":
			cam_file =  "cutout.nc"
			r = self.runCAM("flatcam_process_bottom_cutout.txt")
		if r:
			self.new_cam_file = GcodeFile(self.camfilepath,cam_files)
			self.new_cam_files.emit(self.new_cam_file)
		return r
	
	def getPCBConfigs(self):
		config = []
		f = glob.glob('%s%s*.json' % (self.toolsettingsdir,os.sep))
		for fn  in f:
			config.append( fn)
		return config

	def getCAMConfigs(self):
		config = []
		f = glob.glob('%s%s*.json' % (self.camsettingsdir,os.sep))
		for fn  in f:
			config.append( fn)
		return config
		
	def loadSettings(self,settingsfile):
		f = open(settingsfile,"rb")
		self.settingsdict = {**self.settingsdict, **json.load(f)}
		self.makeVarDict()

#	def loadMillSettings(self):
#		f = open(self.millsettingsfile,"rb")
#		self.settingsdict = json.load(f)
#		self.makeVarDict()

	def makeVarDict(self):
		self.variables = {}
		self.variables['project_path'] = self.projectdir
		self.variables['dirsep'] = os.sep
		self.camfilepath = os.path.join(self.variables['project_path'],'camfiles')

		for n,v in  self.projectfiles.items():
			self.variables[n] = v

		for n,v in self.settingsdict.items():
			self.variables[n] = v
		
		self.settings_update.emit(self.variables)


class ProcessControllerView(QDialog,QObject):
	controller = pyqtSignal(list)
	millsettings_update = pyqtSignal(dict)
	
	def __init__(self,parent,cnccb):
		QDialog.__init__(self)
		self.parent = parent
		self.pc = ProcessController(self, cnccb)
		self.pc.new_cam_files.connect(self.newcam)
		self.gridLayout = QGridLayout(self)
		self.setWindowTitle("Process Conroller")
		self.setLayout(self.gridLayout)
		self.feedrate = 100
		self.makeWindow()
		self.parent.millsettings_update.connect(self.millsettings_update.emit)
		self.parent.updateproject.connect(self.pc.updateproject)
		self.parent.updateproject.connect(self.updateproject)

	def newcam(self,gcodeobj):
		self.cadfile.setText(gcodeobj.filename)
	
	def updateprocess(self, index):
		self.proocessstep.setCurrentIndex(index)
		

	def updateproject(self,prjectuple):
		self.projectpath.setText(prjectuple[0])

	def makeWindow(self):
		self.button = {}
		btnline =0
		
		label = QLabel("Project Path:")
		self.projectpath = QLabel("<none>")
		self.gridLayout.addWidget(label, btnline, 0)
		self.gridLayout.addWidget(self.projectpath, btnline, 1,1,2)
		btnline+=1

		label = QLabel("Cad File:")
		self.cadfile = QLabel("<none>")
		self.gridLayout.addWidget(label, btnline, 0)
		self.gridLayout.addWidget(self.cadfile, btnline, 1)
		btnline+=1


		self.button["home"] = QPushButton('Home', self)
#		self.button["home"].setIcon(QIcon('images/right.png'))
#		self.button["home"].setIconSize(QtCore.QSize(24,24))
		self.button["home"].pressed.connect(lambda : self.handleButton("home"))
		self.gridLayout.addWidget(self.button["home"], btnline, 0)

		self.button["zero"] = QPushButton('Set PCB Zero', self)
#		self.button["zero"].setIcon(QIcon('images/right.png'))
#		self.button["zero"].setIconSize(QtCore.QSize(24,24))
		self.button["zero"].pressed.connect(lambda : self.handleButton("zero"))
		self.gridLayout.addWidget(self.button["zero"], btnline, 2)
		btnline+=1

		self.button["right"] = QPushButton('', self)
		self.button["right"].setIcon(QIcon('images/right.png'))
		self.button["right"].setIconSize(QtCore.QSize(24,24))
		self.button["right"].pressed.connect(self.pc.runCurrentProcess)
		self.gridLayout.addWidget(self.button["right"], btnline, 0)

		self.button["up"] = QPushButton('', self)
		self.button["up"].setIcon(QIcon('images/redo.png'))
		self.button["up"].setIconSize(QtCore.QSize(24,24))
		self.button["up"].pressed.connect(lambda : self.handleButton("up"))
		self.gridLayout.addWidget(self.button["up"], btnline, 1)

		self.button["next"] = QPushButton('', self)
		self.button["next"].setIcon(QIcon('images/next.png'))
		self.button["next"].setIconSize(QtCore.QSize(24,24))
		self.button["next"].pressed.connect(self.pc.nextProcess)
		self.gridLayout.addWidget(self.button["next"], btnline, 2)
		btnline += 1
		self.proocessstep = QComboBox()
		self.proocessstep.currentIndexChanged.connect(self.changestep)
		
		for (s,d) in self.pc.getProcessList():
			self.proocessstep.addItem(s)
		
		self.gridLayout.addWidget(self.proocessstep, btnline, 0,1,3)

	def changestep(self):
		self.pc.setProcessStep(self.proocessstep.currentText())

	def handleButton(self,b):
		self.pressed = None
		

	

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	mainWin = ProcessControllerView()
	mainWin.show()
	sys.exit( app.exec_() )
