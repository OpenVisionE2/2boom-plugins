# -*- coding: utf-8 -*-
# openATV -> openPli emuscript converter
# Copyright (c) 2boom 2015
# v.0.1-r0
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import os
script = '#!/bin/sh\n\ncase "$1" in\nstart)\n\tulimit -s 512\n\tnohup %s >/dev/null &\n\t;;\nstop)\n\tkillall -9 %s\n\tsleep 2\n\t;;\nrestart|reload)\n\t$0 stop\n\tsleep 1\n\t$0 start\n\t;;\nversion)\n\techo "---"\n\t;;\ninfo)\n\techo "%s"\n\t;;\n*)\n\techo "Usage: $0 start|stop|restart"\n\texit 1\n\t;;\nesac\nexit 0\n'
emus = os.listdir("/etc")
print 'Run...'
for name in emus:
	if name.endswith(".emu"):
		emuname = binname = startcam = ''
		for line in open('/etc/%s' % name):
			if line.startswith('emuname'):
				emuname = line.split('=')[-1].strip().strip('\r').strip('\n')
			elif line.startswith('binname'):
				binname = line.split('=')[-1].strip().strip('\r').strip('\n')
			elif line.startswith('startcam'):
				startcam = line.split('=')[-1].strip().strip('\r').strip('\n')
		script_file = open('/etc/init.d/softcam.%s' % name[:-4], 'w')
		script_file.write(script % (startcam, binname, emuname))
		script_file.close()
		if os.path.isfile('/etc/init.d/softcam.%s' % name[:-4]):
			os.chmod('/etc/init.d/softcam.%s' % name[:-4], 0777)
		print '/etc/init.d/softcam.%s - Done.' % name[:-4]
print 'End...'