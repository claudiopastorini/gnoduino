#!/usr/bin/python
#
# Arduino python implementation
# Copyright (C) 2010  Lucian Langa <cooly@gnome.eu.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import glob
import os
import re
import logging
import subprocess
import sys
from distutils.core import setup
from distutils import cmd
import distutils.command
from distutils.command.install import install as _install

global forcesdk
forcesdk = False

for arg in sys.argv[1:]:
	if arg == 'forcesdk' or arg == 'sdist': forcesdk = True
try: sys.argv.remove('forcesdk')
except: pass

try:
    from DistUtilsExtra.command import *
    has_extras = True
except ImportError:
    logging.warn("To be able to install translations, you must install python-distutils-extra.")
    has_extras = False

def runProg(cmdline):
	sout = ""
	serr = ""
	logging.debug("CMD:-%s", cmdline)
	try:
		p = subprocess.Popen(cmdline,
			stdout = subprocess.PIPE,
			stderr = subprocess.STDOUT,
			stdin = subprocess.PIPE,
			close_fds = True)
		poll = select.poll()
		poll.register(p.stdout, select.POLLIN)
		(sout,serr) = p.communicate()
		if p.poll()==1: raise
	except:
		logging.debug("ERR:%s", sout)
		return (False, sout)
	return (True, sout)

def get_gnoduino_version():
	"""Get version from src/__init__.py."""
	text = open(os.path.join("src", "__init__.py"), "r").read()
	return re.search(r"__version__ *= *['\"](.*?)['\"]", text).group(1)

class installSchema(_install):
	def run(self):
		try:
			os.system('GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source` gconftool-2 --makefile-install-rule data/gnoduino.schemas')
		except Exception, e:
			print "Installing schema has failed."
			print "%s: %s" % (type(e), e)
			sys.exit(1)

class Pixmaps(cmd.Command):
	"""Command to build pixmaps from svg sources."""
	description = "build png files from svg sources"
	user_options = []

	def initialize_options(self):
		"""Initialize default values for options."""
		pass

	def finalize_options(self):
		"""Ensure that options have valid values."""
		pass

	def run(self):
		"""Build pixmap from svg sources."""
		if not self.dry_run:
			retcode = subprocess.call("scripts/gen-pixmaps.sh")
			if retcode != 0:
				print "Error: Unable to convert images to PNG"
				sys.exit(1)

compline = "scripts/gitlog.sh"
(run, sout) = runProg(compline)


class install(_install):
	def run(self):
		if len(glob.glob('pixmaps/*.png')) == 0:
			Pixmaps(self.distribution).run()
		# Run all sub-commands (at least those that need to be run)
		_install.run(self)
		installSchema(self.distribution).run()

def get_data_files():
    data_files = [
        ('share/gnoduino/ui', ['ui/main.ui', 'ui/arduino.xml']),
        ('share/gnoduino/', ['ChangeLog', 'NEWS', 'preferences.txt']),
        ('share/gnoduino/pixmaps', glob.glob('pixmaps/*.png')),
        ('share/gnoduino/pixmaps', ['pixmaps/48x48/gnoduino.png']),
        ('share/gnoduino/scripts', ['scripts/gen_boards.py', 'scripts/gen_programmers.py', 'scripts/gen-pixmaps.sh']),
        ('share/man/man1', ['data/gnoduino.1']),
        ('share/applications', ['data/gnoduino.desktop']),
        ('share/icons/hicolor/16x16/apps', ['pixmaps/16x16/gnoduino.png']),
        ('share/icons/hicolor/22x22/apps', ['pixmaps/22x22/gnoduino.png']),
        ('share/icons/hicolor/24x24/apps', ['pixmaps/24x24/gnoduino.png']),
        ('share/icons/hicolor/32x32/apps', ['pixmaps/32x32/gnoduino.png']),
        ('share/icons/hicolor/48x48/apps', ['pixmaps/48x48/gnoduino.png']),
        ('share/icons/hicolor/64x64/apps', ['pixmaps/64x64/gnoduino.png']),
        ('share/icons/hicolor/scalable/apps', ['pixmaps/gnoduino.svg']),
    ]
    for subdir in ("hardware", "libraries", "examples", "reference"):
        # We ship hardware/libraries/reference modules if not already installed
        if forcesdk is True or not os.path.exists(os.path.join(sys.prefix, "share", "arduino", subdir)):
            for dirpath, dirnames, filenames in os.walk(subdir):
                if ".git" not in dirpath and filenames:
                    data_files.append([os.path.join("share", "gnoduino", dirpath),
                                       [os.path.join(dirpath,i) for i in filenames]])
    return data_files

cmd_classes = {
	"pixmaps": Pixmaps,
	"install": install,
}
if has_extras:
	cmd_classes.update({
		"build" : build_extra.build_extra,
		"build_i18n" :  build_i18n.build_i18n,
	})

setup(name='gnoduino',
	version=get_gnoduino_version(),
	description='Gnome Arduino IDE implementation',
	package_dir={'gnoduino': 'src'},
	packages = ['gnoduino'],
	scripts = ['gnoduino'],

	author='Lucian Langa',
	author_email='lucilanga@gnome.org',
	url='http://gnome.eu.org/evo/index.php/Gnoduino',
	license='GPL',
	platforms='linux',
	data_files = get_data_files(),
	cmdclass=cmd_classes,
)

