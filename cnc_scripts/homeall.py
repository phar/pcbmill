import linuxcnc
import os
import sys
import time
s = linuxcnc.stat()
c = linuxcnc.command()

def ok_for_mdi():
	time.sleep(.1)
	s.poll()
	return not s.estop and s.enabled and s.homed and (s.interp_state == linuxcnc.INTERP_IDLE) and  (s.state == 1)


c.mode(linuxcnc.MODE_MANUAL)
c.wait_complete()
c.reset_interpreter()
c.override_limits()
c.home(0)
c.home(1)
c.home(2)
s.poll()
while not ok_for_mdi():
	c.wait_complete()

c.mode(linuxcnc.MODE_MDI)
c.mdi("G92 X1 Y1 Z%f" % 41.5)
c.mdi("G0 X2.0 Y2.0 Z%f"  % 39.5)
c.mdi("G92 X0 Y0")
s.poll()
s.poll()
while s.state != 1:
	s.poll()
c.wait_complete()
c.mode(linuxcnc.MODE_MANUAL)
c.wait_complete()
