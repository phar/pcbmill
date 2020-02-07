import sys
import numpy
import cv2
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize ,QTimer
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal,pyqtSlot, QObject
from shapely.geometry import mapping, shape, Point

class CameraView(QDialog,QObject):
	frame_click = pyqtSignal(Point)
	frame = pyqtSignal(QImage)
	def __init__(self,parent = None):
		QDialog.__init__(self)
		self.parent = parent
		self.setWindowTitle("Camera View")
		self.gridLayout = QGridLayout(self)
		self.setLayout(self.gridLayout)  

		self.cap = cv2.VideoCapture(0)

		self.makeWindow()
		self.timer = QTimer()
		self.timer.timeout.connect(self.tick)
		self.timer.start(100)
		self.settings = {}
		self.parent.millsettings_update.connect(self.settings_update)
		
	def settings_update(self,settings):
		self.settings = settings
		print(self.settings)

	def tick(self):
		ret, frame = self.cap.read()

		height, width, channel = frame.shape
		bytesPerLine = 3 * width
		self.frame_center =  Point(frame.shape[1]/2.0,frame.shape[0]/2.0)
		
		self.lastframe = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)

		cv2.line(frame,(int(width/2),0),(int(width/2),height),(0,255,255),1)
		cv2.line(frame,(0, int(height/2)),(width, int(height/2)),(0,255,255),1)

		self.lastview = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
		self.frame.emit(self.lastframe)
		self.camview.setPixmap(QPixmap.fromImage(self.lastview))

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
		self.camview = QLabel()
		self.tick()
		self.gridLayout.addWidget(self.camview, btnline, 1)
		self.camview.mouseReleaseEvent = self.clickview
		btnline += 1

	def clickview(self, event):
		(x,y) = (event.x(), event.y())
		(xd,yd) = ((self.frame_center.x - x) * self.settings['camera_mm_per_pixel']), ((self.frame_center.y - y) * self.settings['camera_mm_per_pixel'])
		self.frame_click.emit(Point((xd,yd)))

	def cancel(self):
		self.doneit.emit({})
		self.reject()
		
	def update_filelist(self,var):
		for ii,dd in self.filewidgetlist.items():
			self.projectfiles[ii] = dd.currentText()
		self.doneit.emit(self.projectfiles)
		self.accept()

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	mainWin = CameraView()
	mainWin.show()
	sys.exit( app.exec_() )
