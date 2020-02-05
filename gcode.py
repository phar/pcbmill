
import pickle
import math
import matplotlib
import numpy as np
from scipy.interpolate import interp2d
import matplotlib.pyplot as plt
from scipy import interpolate
from scipy.interpolate import griddata
from matplotlib import collections  as mc
from scipy.interpolate import griddata
import tempfile
import random
import os


class GcodeFile(object):
	def __init__(self,path, filename, point=(0,0), angle=0, offsetx=0,offsety=0):
		self.board_dims = {"MIN_X":0.0,"MAX_X":0.0,"MIN_Y":0.0,"MAX_Y":0.0}
		self.filename = os.path.join(path,filename)
		self.path = path
		
		self.gcodeflavors = ["LinuxCNC", "Mach3" , "Mach4"]
		self.gcodeflavor ="LinuxCNC"
		f = open(self.filename)
		self.gcodelines = []
		self.lastcodes = {}
		gcodelines = f.readlines()
		f.close()
		
		self.zmesh = self.zeromesh
		self.lastx = 0
		self.lasty = 0
		self.lastz = 0
		self.evaluations_per_mm = 100 #for height mappin
		self.rotpoint = point
		self.rotangle = angle
		self.offsetx = offsetx
		self.offsety = offsety
		self.overridez = None

		lastg = ""
		lastgval = None
		
		for ll in gcodelines:
			lll,lcts = self.filterComments(ll.strip())
			if lcts.split(",")[0] == "MSG":
				if lcts.split(",")[1].split("=")[0] == "Change to tool dia":
					pass #fixme			
			lll = lll.replace("X"," X")
			lll = lll.replace("Y"," Y")
			lll = lll.replace("Z"," Z")
			lll = lll.replace("F"," F")
			lll = lll.replace("M"," M")
			lll = lll.replace("S"," S")
			lll = lll.replace("  "," ")#conditioning
			if (len(lll)):
				cmdsplit = lll.strip().split(" ")
				args = {}
				for l in cmdsplit:
					args[l[0]] = float(l[1:])

				if 'G' in args:
					lastgval = args['G']
					lastg = 'G'
				elif 'M' in args:
					lastg  = 'M'
					lastgval = args['M']
				elif 'S' in args:
					lastg  = 'S'
					lastgval = args['S']
				else:
					if lastg == 'G':
						args[lastg] = lastgval
						lastgval = args['G']

				self.gcodelines.append(args)
					
		self.recalc_board_dims()
		#self.loadNullMesh()
				
	def get_board_dims(self):
		return (self.board_dims['MIN_X'],self.board_dims['MAX_X'],self.board_dims['MIN_Y'],self.board_dims['MAX_X'])

	def recalc_board_dims(self):
		lastx = 0
		lasty = 0
		for args in self.gcodelines:
			if "Y" in args:
				thisy = args["Y"]
			else:
				thisy = lasty
			
			if "X" in args:
				thisx =  args["X"]
			else:
				thisx = lastx
			
			(thisx,thisy) = self.getRotatedPoint((thisx,thisy))
			
			if thisy >  self.board_dims["MAX_Y"]:
				self.board_dims["MAX_Y"] = thisy

			elif thisy <  self.board_dims["MIN_Y"]:
				self.board_dims["MIN_Y"] = thisy

			if thisx>  self.board_dims["MAX_X"]:
				self.board_dims["MAX_X"] = thisx

			elif thisx <  self.board_dims["MIN_X"]:
				self.board_dims["MIN_X"] = thisx

	def zeromesh(self,x,y):
		return 0
	
	def split_line(self,x1,y1,x2,y2):
		segments = []
		l = math.sqrt(((x2-x1)**2.0) + ((y2 - y1)**2.0))
		if l > (1.0 / self.evaluations_per_mm):
			for i in np.linspace(0,l/(1.0 / self.evaluations_per_mm)):
				x = x1 + (i / (l/(1.0 / self.evaluations_per_mm))) * (x2 - x1)
				y = y1 + (i / (l/(1.0 / self.evaluations_per_mm))) * (y2 - y1)
				segments.append({"X":x,"Y":y})
			segments.append({"X":x2,"Y":y2})
		else:
			segments.append({"X":x2,"Y":y2})
		return segments
	
	def loadNullMesh(self):
		x = [random.randint(0,10) for x in range(20)]
		y = [random.randint(0,10) for x in range(20)]
		z = [0.0  for x in range(20)]
		self.zmesh = interp2d(x, y, z, kind='linear')
	
	def setProbePoints(self,probepntlst):
		self.probedx = []
		self.probedy = []
		self.probedz = []

		for l in probepntlst:
			(x,y,z)  = [float(x) for x in l.strip().split()][:3]
			self.probedx.append(x)
			self.probedy.append(y)
			self.probedz.append(z)
		self.zmesh = interp2d(self.probedx, self.probedy, self.probedz, kind='cubic')
	
	def loadProbedPointsFile(self,filename):
		f = open(filename)
		if self.gcodeflavor == "LinuxCNC":
			ll = f.readlines()
			pnts = []
			for l in ll:
				pnts.append([float(x) for x in l.strip().split()][:3])
		self.setProbePoints(pnts)

	def generateProbePoints(self,xpts,ypts):
		xx = np.linspace(self.offsetx+self.board_dims["MIN_X"],self.offsetx+self.board_dims["MAX_X"],xpts)
		yy = np.linspace(self.offsety+self.board_dims["MIN_Y"],self.offsety+self.board_dims["MAX_Y"],ypts)
		pts = []
		for y in yy:
			for x in xx:
				pts.append((x,y))
		return pts

	def writeProbeGcodeFile(self,pts,feedrate=100, proberate=75, probebottom=-1, filename=None, probefile=None):
		if filename == None:
			(fd, filename) = tempfile.mkstemp()
			os.close(fd)
		
		if probefile == None:
			(fd, probefile) = tempfile.mkstemp()
			os.close(fd)

		f =open(filename,"w")
		f.write("F%f\n" % feedrate)
		if self.gcodeflavor == "LinuxCNC":
			f.write("(PROBEOPEN %s)\n" % probefile)
			for x,y in pts:
				f.write("G0 X%f Y%f Z%f\n" % (x,y,5));
				f.write("G38.3 Z%f F%f\n" % (probebottom,proberate));
				f.write("G1 Z%f\n" % (5));
			f.write("(PROBECLOSE)\n")
		elif self.gcodeflavor == "Mach3":
			f.write("M40\n")
			Gprobe       = "G31"
	#            ZProbeValue  = "#2002"
			f.write("M41\n")

		elif self.gcodeflavor == "Mach4":
			f.write("M40\n")
				#            Gprobe       = "G31"
			f.write("M41\n")

		f.write("M2\n")
		f.close()
		print("probefiles",filename,probefile)
		return (filename,probefile)

	def getMeshGraphParams(self):
		x2 = np.linspace(self.board_dims["MIN_X"], self.board_dims["MAX_X"], abs(self.board_dims["MAX_X"] - self.board_dims["MIN_X"])*100) #evaluate 1/100th of a mm
		y2 = np.linspace(self.board_dims["MIN_Y"], self.board_dims["MAX_Y"], abs(self.board_dims["MAX_X"] - self.board_dims["MIN_X"])*100)
		Z2 = self.zmesh(x2, y2)	
		return (x2,y2,Z2)
		
	def showHeightMesh(self):
		(x2,y2,Z2) = self.getMeshGraphParams()
		fig, ax = plt.subplots()
		X2, Y2 = np.meshgrid(x2, y2)
		c = ax.pcolormesh(X2, Y2, Z2)
		fig.colorbar(c, ax=ax)
		plt.show()

	def setOffset(self,x,y):
		self.offsetx = x
		self.offsety = y
		self.recalc_board_dims()

	def setRotationPoint(self,pt):
		self.rotpoint = pt
		self.recalc_board_dims()

	def getRotatedPoint(self, point):
		ox, oy = self.rotpoint
		px, py = point
		qx=math.cos(self.rotangle)*(px-ox)-math.sin(self.rotangle)*(py-oy) + ox
		qy=math.sin(self.rotangle)*(px-ox)+math.cos(self.rotangle)*(py-oy) + oy
		return qx, qy

	def setRotationAngle(self,angle):
		self.rotangle = math.radians(angle)
		self.recalc_board_dims()

	def filterComments(self,line):
		nl = []
		comment = 0
		commenttxt = ""
		for l in line:
			if l == '(':
				comment = 1
			elif l == ')' and comment == 1:
				comment = 0
			else:
				if comment != 1:
					nl.append(l)
				else:
					commenttxt += l
		
		return "".join(nl),commenttxt
		
# 	def getDrills(self):
# 		points = []
# 		for gline in self.gcodelines:
# 			if "G" in gline:
# 				gval = gline.pop('G', None)
# 				if gval in [82.0]:
# 					points.append(gline["X"],gline["Y"])
# 		return points

	def previewGcode(self):
		lines = []
		rapidlines = []
		lastix = 0
		lastiy = 0
		lastox = 0
		lastoy = 0
		for args in self.gcodelines:

			if "G" in args:
				if "Y" in args:
					thisy = args["Y"]
				else:
					thisy = lastiy
				
				if "X" in args:
					thisx =  args["X"]
				else:
					thisx = lastix
				
				(thisx,thisy) = self.getRotatedPoint((thisx,thisy))
				
				if args["G"] == 0.0:
					rapidlines.append([(lastox,lastoy), (thisx,thisy)])
					lastox = thisx
					lastoy = thisy
				elif args["G"] == 1.0:
					lines.append([(lastox,lastoy), (thisx,thisy)])
					lastox = thisx
					lastoy = thisy

				if "Y" in args:
					lastiy = args["Y"]
				if "X" in args:
					lastix =  args["X"]
					
		return (lines, rapidlines)
	
	def showGcodePlot(self):
		(lines,rapidlines) = self.previewGcode()
		print(lines)
		print(rapidlines)
		fig, ax = plt.subplots()
		lc = mc.LineCollection(lines)
		rlc = mc.LineCollection(rapidlines,color="red")
		ax.add_collection(lc)
		ax.add_collection(rlc)

		ax.plot()
		plt.show()
	
	def writeGcodeFile(self,filename=None):
		if filename == None:
			(fd, filename) = tempfile.mkstemp()
		else:
			fd = os.open(filename,os.O_WRONLY|os.O_CREAT)

		for p in  self.getNextGcode():
			os.write(fd,  bytes("%s\n" % p, "utf-8"))

		os.close(fd)
		return filename
			


	def printGcodeFile(self):
		for p in  self.getNextGcode():
			print(p)

	def getDrillLocs(self,drillbottom=0.0):
		locs = []
		lastx = 0
		lasty = 0
		lastz = None
		for args in self.gcodelines:

			if "G" in args:
				if "Y" in args:
					thisy = args["Y"]
				else:
					thisy = lasty
				
				if "X" in args:
					thisx =  args["X"]
				else:
					thisx = lastx
				(thisx,thisy) = self.getRotatedPoint((thisx,thisy))
				if args["G"] == 1.0:
					if args["Z"] == drillbottom:
						locs.append((thisx,thisy))

				lastx = thisx
				lasty = thisy

		return locs
	
	
	def writeDrillLocsFile(self,filename = None):
		if filename == None:
			(fd, filename) = tempfile.mkstemp()
		else:
			fd = os.open(filename,os.O_WRONLY|os.O_CREAT)
		
		for x,y in  self.getDrillLocs():
			os.write(fd,  bytes("%f %f\n" % (x,y), "utf-8"))
		
		os.close(fd)
		return filename

		
	def getNextGcode(self):
		for gline in self.gcodelines:
			#print gline
			if "M" in gline:
				gval = gline.pop('M', None)
				pcode = "M%d "% gval
				thisg =  "M"
			elif "G" in gline:
				gval = gline.pop('G', None)
				pcode = "G%d "% gval
				thisg =  "G"
			elif "S" in gline:
				gval = gline.pop('S', None)
				pcode = "S%d "% gval
				thisg =  "S"
			else:
				pcode = ""
				thisg = ""
				gval = None

			thisx =  gline.pop('X', self.lastx)
			thisy =  gline.pop('Y', self.lasty)
			
			if self.overridez == None:
				thisz =  gline.pop('Z', self.lastz)
			else:
				thisz = self.overridez

			self.lastx = thisx
			self.lasty = thisy
			self.lastz = thisz
			
			if ("G" == thisg and gval in [0.0, 1.0, 82.0]):
				for p in  self.split_line(self.lastx,self.lasty,thisx,thisy):
					self.lastx = p['X']
					self.lasty = p['Y']
				
					(p['X'],p['Y']) = self.getRotatedPoint((p['X'],p['Y']))
					
					gcode = ""
					gline['X'] = p['X'] + self.offsetx
					gline['Y'] = p['Y'] + self.offsety
					gline['Z'] = thisz + self.zmesh(gline['X'], gline['Y'])
					
					for n,v in gline.items():
						self.lastcodes[n] = v
						gcode += "%s%f " % (n,v)
					
					yield pcode+gcode
	
			else:
				gcode = ""
				for n,v in gline.items():
					self.lastcodes[n] = v
					gcode += "%s%f " % (n,v)
				
				#print pcode + gcode
				yield pcode + gcode

if __name__ == "__main__":
	#f = GcodeFile("./","topdrill.nc")
	f = GcodeFile("/media/phar/CAC8-AF5B/pcbmill/camfiles/","top.nc")
	f.setRotationPoint((20,20))
	f.setRotationAngle(0)
	f.setOffset(20,20)
#	print(f.generateProbePoints(5,5))
#	f.writeProbeGcodeFile("test",f.generateProbePoints(5,5))
	f.showGcodePlot()
#	f.showHeightMesh()
#	f.writeGcodeFile("t1.gcode")
	print(f.getDrillLocs())
	f.writeDrillLocsFile(filename="drilltest.txt")
#	print(f.get_board_dims())
#	f.loadProbedPointsFile("probe_points.txt")
#	f.showHeightMesh()
 
