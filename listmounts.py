import psutil
partitions = psutil.disk_partitions()

for p in partitions:
	if p.mountpoint[:7] == b"/media/":
		print p.mountpoint
