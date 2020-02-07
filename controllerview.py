import sys
import numpy
import cv2
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize ,QTimer
from PyQt5.QtGui import *
#from PyQt5.QtCore import pyqtSignal,pyqtSlot, QObject
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class ControllerView(QDialog,QObject):
	controller = pyqtSignal(list)
	position = pyqtSignal(list)
	def __init__(self,parent,cnccb):
		QDialog.__init__(self)
		self.setWindowTitle("Stage Controller")
		self.pressed = None
		self.cnccb = cnccb
#		self.setWindowModality(QtCore.Qt.ApplicationModal)
		self.gridLayout = QGridLayout(self)     
		self.setLayout(self.gridLayout)  
		self.jograte = 20
		
		self.timer = QTimer()
		self.timer.timeout.connect(self.tick)
		self.timer.start(500)
		
		self.makeWindow()

	def tick(self):
		self.position = self.cnccb.send_command("GETPOS")["ret"]
		self.xpos.setText(str(self.position[0]))
		self.ypos.setText(str(self.position[1]))
		self.zpos.setText(str(self.position[2]))
#		print(self.position)

	def makeWindow(self):
		self.button = {}
		btnline =0
		title = QLabel("X-Pos", self)
		self.xpos = QLabel("0.0", self)
		mml = QLabel("mm", self)
		self.gridLayout.addWidget(title, btnline, 0)
		self.gridLayout.addWidget(self.xpos, btnline, 1)
		self.gridLayout.addWidget(mml, btnline, 2)
		btnline +=1

		title = QLabel("Y-Pos", self)
		self.ypos = QLabel("0.0", self)
		mml = QLabel("mm", self)
		self.gridLayout.addWidget(title, btnline, 0)
		self.gridLayout.addWidget(self.ypos, btnline, 1)
		self.gridLayout.addWidget(mml, btnline, 2)
		btnline +=1

		title = QLabel("Z-Pos", self)
		self.zpos = QLabel("0.0", self)
		mml = QLabel("mm", self)
		self.gridLayout.addWidget(title, btnline, 0)
		self.gridLayout.addWidget(self.zpos, btnline, 1)
		self.gridLayout.addWidget(mml, btnline, 2)
		btnline +=1

		self.button["upleft"] = QPushButton('', self)
		self.button["upleft"].setIcon(QIcon('images/upleft.png'))
		self.button["upleft"].setIconSize(QtCore.QSize(24,24))
		self.button["upleft"].pressed.connect(lambda : self.handleButtonp("upleft"))
		self.button["upleft"].released.connect(lambda : self.handleButtonr("upleft"))
		self.gridLayout.addWidget(self.button["upleft"], btnline, 0)

		self.button["up"] = QPushButton('', self)
		self.button["up"].setIcon(QIcon('images/up.png'))
		self.button["up"].setIconSize(QtCore.QSize(24,24))
		self.button["up"].pressed.connect(lambda : self.handleButtonp("up"))
		self.button["up"].released.connect(lambda : self.handleButtonr("up"))
		self.gridLayout.addWidget(self.button["up"], btnline, 1)

		self.button["upright"] = QPushButton('', self)
		self.button["upright"].setIcon(QIcon('images/upright.png'))
		self.button["upright"].setIconSize(QtCore.QSize(24,24))
		self.button["upright"].pressed.connect(lambda : self.handleButtonp("upright"))
		self.button["upright"].released.connect(lambda : self.handleButtonr("upright"))
		self.gridLayout.addWidget(self.button["upright"], btnline, 2)

		btnline+=1

		self.button["left"] = QPushButton('', self)
		self.button["left"].setIcon(QIcon('images/left.png'))
		self.button["left"].setIconSize(QtCore.QSize(24,24))
		self.button["left"].pressed.connect(lambda : self.handleButtonp("left"))
		self.button["left"].released.connect(lambda : self.handleButtonr("left"))
		self.gridLayout.addWidget(self.button["left"], btnline, 0)

		self.button["cancel"] = QPushButton('', self)
		self.button["cancel"].setIcon(QIcon('images/cancel.png'))
		self.button["cancel"].setIconSize(QtCore.QSize(24,24))
		self.button["cancel"].pressed.connect(lambda : self.handleButtonp("cancel"))
		self.button["cancel"].released.connect(lambda : self.handleButtonr("cancel"))
		self.gridLayout.addWidget(self.button["cancel"], btnline, 1)

		self.button["right"] = QPushButton('', self)
		self.button["right"].setIcon(QIcon('images/right.png'))
		self.button["right"].setIconSize(QtCore.QSize(24,24))
		self.button["right"].pressed.connect(lambda : self.handleButtonp("right"))
		self.button["right"].released.connect(lambda : self.handleButtonr("right"))
		self.gridLayout.addWidget(self.button["right"], btnline, 2)

		btnline+=1

		self.button["downleft"] = QPushButton('', self)
		self.button["downleft"].setIcon(QIcon('images/downleft.png'))
		self.button["downleft"].setIconSize(QtCore.QSize(24,24))
		self.button["downleft"].pressed.connect(lambda : self.handleButtonp("downleft"))
		self.button["downleft"].released.connect(lambda : self.handleButtonr("downleft"))
		self.gridLayout.addWidget(self.button["downleft"], btnline, 0)

		self.button["down"] = QPushButton('', self)
		self.button["down"].setIcon(QIcon('images/down.png'))
		self.button["down"].setIconSize(QtCore.QSize(24,24))
		self.button["down"].pressed.connect(lambda : self.handleButtonp("down"))
		self.button["down"].released.connect(lambda : self.handleButtonr("down"))
		self.gridLayout.addWidget(self.button["down"], btnline, 1)

		self.button["downright"] = QPushButton('', self)
		self.button["downright"].setIcon(QIcon('images/downright.png'))
		self.button["downright"].setIconSize(QtCore.QSize(24,24))
		self.button["downright"].pressed.connect(lambda : self.handleButtonp("downright"))
		self.button["downright"].released.connect(lambda : self.handleButtonr("downright"))
		self.gridLayout.addWidget(self.button["downright"], btnline, 2)


		self.button["plus"] = QPushButton('', self)
		self.button["plus"].setIcon(QIcon('images/plus.png'))
		self.button["plus"].setIconSize(QtCore.QSize(24,24))
		self.button["plus"].pressed.connect(lambda : self.handleButtonp("plus"))
		self.button["plus"].released.connect(lambda : self.handleButtonr("plus"))
		self.gridLayout.addWidget(self.button["plus"], 3, 3)

		self.button["minus"] = QPushButton('', self)
		self.button["minus"].setIcon(QIcon('images/minus.png'))
		self.button["minus"].setIconSize(QtCore.QSize(24,24))
		self.button["minus"].pressed.connect( lambda : self.handleButtonp("minus"))
		self.button["minus"].released.connect(lambda : self.handleButtonr("minus"))
		self.gridLayout.addWidget(self.button["minus"], 5, 3)

		btnline += 1
		fl = QLabel("Feed")
		self.gridLayout.addWidget(fl, btnline, 0)

		self.feedslider = QSlider(Qt.Horizontal)
		self.feedslider.setMinimum(0)
		self.feedslider.setMaximum(600)
		self.feedslider.setValue(self.jograte)
		self.feedslider.setTickPosition(QSlider.TicksBelow)
		self.feedslider.setTickInterval(10)
		self.gridLayout.addWidget(self.feedslider, btnline, 1,1,2)
		self.feedslider.valueChanged.connect(self.feedchange)

		self.feedview = QLabel("20")
		self.gridLayout.addWidget(self.feedview, btnline, 3)


	def feedchange(self):
		self.jograte = self.feedslider.value()
		self.feedview.setText(str(self.jograte))

	def handleButtonp(self,b):
		self.pressed = b
		if b in ["up","upright","upleft"]:
			jograte = self.jograte
		elif b in ["down", "downright", "downleft"]:
			jograte = -self.jograte
		if b in ["up","down","upright","downright","upleft","downleft"]:
			self.cnccb.send_command("JOG", {"axis":"Y", "rate":jograte})

		if b in ["left","upleft","downleft"]:
			jograte = self.jograte
		elif b in ["right", "upright", "downright"]:
			jograte = -self.jograte
		if b in ["left","right","upright","downright","upleft","downleft"]:
			self.cnccb.send_command("JOG", {"axis":"X", "rate":jograte})

		if b in ["plus","minus"]:
			self.cnccb.send_command("JOG", {"axis":"Z", "rate":jograte})

	def handleButtonr(self,b):
		self.pressed = None
		if b in ["up","upright","upleft"]:
			jograte = self.jograte
		elif b in ["down", "downright", "downleft"]:
			jograte = -self.jograte
		if b in ["up","down","upright","downright","upleft","downleft"]:
			self.cnccb.send_command("JOGSTOP", {"axis":"Y", "rate":jograte})

		if b in ["left","upleft","downleft"]:
			jograte = self.jograte
		elif b in ["right", "upright", "downright"]:
			jograte = -self.jograte
			
		if b in ["left","right","upright","downright","upleft","downleft"]:
			self.cnccb.send_command("JOGSTOP", {"axis":"X", "rate":jograte})
			
		if b in ["plus","minus"]:
			self.cnccb.send_command("JOGSTOP", {"axis":"Z", "rate":jograte})
	

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	mainWin = ControllerView()
	mainWin.show()
	sys.exit( app.exec_() )
