#! /usr/bin/env python
#
# update script for ufb
#
# jaksi

"""
ufb update script-je
"""

import sys
import urllib
import subprocess
import time
import os
import commands
import shutil


try:
	shutil.move(u'bot.py', u'backup/bot.py')
	urllib.urlretrieve(u'https://raw.github.com/shinarit/lulzbot/updatetest/bot.py', u'bot.py')
	shutil.move(u'uf.py', u'backup/uf.py')
	urllib.urlretrieve(u'https://raw.github.com/shinarit/lulzbot/updatetest/uf.py', u'uf.py')
	subprocess.Popen([u'python', u'bot.py'])
	sys.exit()
except:
	sys.exit([1])
