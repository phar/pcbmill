import sys
import numpy
import cv2
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize ,QTimer
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal,pyqtSlot, QObject
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from matplotlib import collections  as mc
import numpy as np
from scipy import interpolate
from scipy.interpolate import griddata


class BoardView(QDialog,QObject):
	frame = pyqtSignal(QImage)
	def __init__(self,parent = None):
		QDialog.__init__(self)
		self.setWindowTitle("Board View")

#		self.setWindowModality(QtCore.Qt.ApplicationModal)
		self.gridLayout = QGridLayout(self)     
		self.setLayout(self.gridLayout)  

		self.makeWindow()


	def makeWindow(self):
		btnline = 0	
	

		self.dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
		self.plotWidgetax = self.dynamic_canvas.figure.subplots()
		self.gridLayout.addWidget(self.dynamic_canvas, 0, 0,btnline,1)
		cid = self.dynamic_canvas.mpl_connect('button_press_event', self.boardclick)
		self.temp()
		
	def boardclick(self, event):
		if  event.dblclick and event.button == 1:
			print("dblckicked board",event.xdata, event.ydata)

	def temp(self):
		x = np.linspace(-1,1,100)
		y =  np.linspace(-1,1,100)
		npts = 400
		px, py = np.random.choice(x, npts), np.random.choice(y, npts)
		X, Y = np.meshgrid(x,y)
		Ti = griddata((px, py), f(px,py), (X, Y), method='cubic')
		c = self.plotWidgetax.pcolormesh(X, Y, Ti)
	
		
	def new_cam_files(self, gcodefile):
		(lines,rapidlines) = gcodefile.previewGcode()
		lc = mc.LineCollection(lines)
		rlc = mc.LineCollection(rapidlines,color="red")

		print(lc)
		print(rlc)
		self.plotWidgetax.add_collection(lc)
		self.plotWidgetax.add_collection(rlc)
		self.plotWidgetax.plot()
		self.dynamic_canvas.draw()

def f(x, y):
	s = np.hypot(x, y)
	phi = np.arctan2(y, x)
	tau = s + s*(1-s)/5 * np.sin(6*phi)
	return 5*(1-tau) + tau
	
if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	mainWin = BoardView()
	mainWin.show()
	sys.exit( app.exec_() )
