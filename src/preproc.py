
# Arduino python implementation
# Copyright (C) 2010  Lucian Langa
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import config
import prefs
import re
import os
import tempfile
import misc

MAIN = "hardware/arduino/cores/arduino/main.cpp"

"""Returns the index of the first character that's not whitespace, a comment
or a pre-processor directive."""
def firstStatement(instr):
	m = re.match(r"""\s+|
		/\*[^*]*(?:\*(?!/)[^*]*)*\*/
		|\s+|
		(//.*\n)+"""
		, instr, re.VERBOSE)
	if not m: return 0
	return m.end(0)

def lastInclude(instr):
	m = re.finditer(r"^#include\s+[\w+\".<>\-]+", instr, re.M)
	try:
		return max(enumerate(m))[1].end()
	except:
		return 0


def findPrototype(instr):
	pro = []
	m = re.findall(r"^\w+\s+\w+\([^)]*\)[\s+/*\w*\s+]*;", instr, re.M)
	for z in m:
		q = re.findall("\w+\s+\w+", z)
		pro.append(q[0])
	return pro

def genPrototype(instr):
	hdup = 0
	hdr = ""
	"""find exisiting prototypes"""
	proto = findPrototype(instr)
	m = re.findall(r"^\w+\s+\w+\([^)]*\)[\s+/*\w*\s+]*{", instr, re.M)
	for z in m:
		t = re.findall("\w+\s+\w+", z)
		for p in proto:
			if p==t[0]: hdup=1
		if hdup:
			hdup=0
			continue
		q = re.findall("\w+\s+\w+\([^)]*\)", z)
		hdr = hdr + q[0]+";\n"
	return hdr


def findIncludes(instr, local=False):
	res = ""
	m = re.findall(r"^\s*#include\s+[\w+\".<>\-]+", instr, re.M)
	l = [z.split()[1].strip('<>"') for z in m]
	my = []
	for z in l:
		path = os.path.join(misc.getArduinoLibsPath(), z.strip(".h"))
		if os.path.exists(path) or os.path.exists(path.lower()) or \
				os.path.exists(path.upper()):
			my.append(os.path.join(misc.getArduinoLibsPath(), z.strip(".h")))
		if config.user_library:
			for q in config.user_library.split(';'):
				fl = os.path.join(q.strip(), z)
				if os.path.exists(fl) or os.path.exists(fl.lower()) or \
					os.path.exists(fl.upper()):
						my.append(q.strip())
				fl = os.path.join(q.strip(), z.strip(".h"))
				if os.path.exists(fl) or os.path.exists(fl.lower()) or \
					os.path.exists(fl.upper()):
						my.append(os.path.join(q.strip(), z.strip(".h")))
		if local and (os.path.exists(z.strip(".h")) or \
				os.path.exists(z.strip(".h").lower()) or \
				os.path.exists(z.strip(".h").upper())):
			my.append(z.strip(".h"))

		if config.sketchFile:
			sketchPath = os.path.dirname(config.sketchFile)
			"is this really required"
			if local and os.path.exists(sketchPath):
				my.append(sketchPath)

			sp = os.path.join(sketchPath, z.strip(".h"))
			if local and os.path.exists(sp):
				my.append(sp)

			sp = os.path.abspath(os.path.join(sketchPath, ".."))
			if local and os.path.exists(sp):
				my.append(sp)

			sp = os.path.abspath(os.path.join(sketchPath, "..", z.strip(".h")))
			if local and os.path.exists(sp):
				my.append(sp)


	for z in l:
		for r, d, f in os.walk(misc.getArduinoLibsPath()):
			if len(f)>0:
				for file in f:
					if file.strip(".h")+".cpp" == z.strip(".h")+".cpp":
						my.append(r)
	if len(my) == 0:
		for z in l:
			for r, d, f in os.walk(misc.getArduinoLibsPath()):
				if len(f)>0:
					my.extend([r for file in f if file == z])
					for file in f:
						if file == z: break
	return list(set(my))

def makeBufferTempfile(buffer):
	pass


def addHeaders(path, b):
	line = 0
	cont = b.get_text(b.get_start_iter(), b.get_end_iter())
	fs = firstStatement(cont)
	if fs != None:
		proto = genPrototype(cont)
		lastinc = lastInclude(cont)
		incl = "\n#include \""+misc.getArduinoAPIFile()+"\"\n"
		result = cont[:fs:] + incl + cont[fs:lastinc:] + "\n" \
			 + proto + cont[lastinc:] + "\n\n"
	else:
		result = "\n#include \""+misc.getArduinoAPIFile()+"\"\n"+cont+"\n\n"

	of = tempfile.mktemp(".cpp", "", path)
	w = file(of, "w")
	w.write(result)
	w.close()
	for l in proto.splitlines(): line += 1
	return (of, line)

def generateCFlags(path, b):
	#cont = b.get_text(b.get_start_iter(), b.get_end_iter())
	cont = b
	test = []
	result = []
	for i in findIncludes(cont):
		flag = os.path.join(misc.getArduinoLibsPath(), i)
		if flag not in set(test):
			test.append(flag)
			result.append("-I"+flag)
		lib = os.path.join(config.user_library, i)
		if lib not in set(test):
			test.append(lib)
			result.append("-I"+lib)
	for i in findIncludes(cont, True):
		if i not in set(test):
			test.append(i)
			result.append("-I"+i)
	return result

def generateLibs(path, b):
	cont = b.get_text(b.get_start_iter(), b.get_end_iter())
	return [i for i in findIncludes(cont, True)]
