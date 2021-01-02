#!/usr/bin/env python3
#	airdroidclient - Scriptable interface to the Airdroid smart phone app
#	Copyright (C) 2019-2020 Johannes Bauer
#
#	This file is part of airdroidclient.
#
#	airdroidclient is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	airdroidclient is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with airdroidclient; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import sys
import argparse
import contextlib
from AirdroidConnection import AirdroidConnection
from FriendlyArgumentParser import FriendlyArgumentParser

def host_path(text):
	if ":" not in text:
		raise argparse.ArgumentTypeError("'%s' is not a valid hostname:pathspec" % (text))
	return text.split(":", maxsplit = 1)

parser = FriendlyArgumentParser()
parser.add_argument("--port", metavar = "port", type = int, default = 8888, help = "Port that Airdroid uses. Defaults to %(default)d.")
parser.add_argument("-o", "--overwrite", choices = [ "never", "always" ], default = "never", help = "Overwrite local files if they already exist. Can be any of %(choices)s, defaults to %(default)s.")
parser.add_argument("-r", "--recurse", action = "store_true", help = "Recursively copy files.")
parser.add_argument("-n", "--no-copy", action = "store_true", help = "Do not copy files, just print what would happen.")
parser.add_argument("-z", "--zero-files", action = "store_true", help = "Create files with filesize zero.")
parser.add_argument("-e", "--empty-directories", action = "store_true", help = "Preserve empty directories.")
parser.add_argument("-f", "--fast-skip", action = "store_true", help = "When encountering a file that is named identically to one locally present, do not verify file size, but skip it immediately.")
parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity.")
parser.add_argument("src", metavar = "hostname:pathspec", type = host_path, help = "Hostname or IP address where the Airdroid connection can be reached and ")
parser.add_argument("dst", metavar = "pathname", type = str, help = "Filename or directory name that is the local destination")
args = parser.parse_args(sys.argv[1:])

class AndroidCopier():
	def __init__(self, args):
		self._args = args

		uri = "http://%s:%d" % (args.src[0], args.port)
		self._adc = AirdroidConnection(uri, verbose = (self._args.verbose >= 1))
		self._adc.login()

	def _copy_directory(self, remote_path, local_path):
		if not remote_path.endswith("/"):
			remote_path += "/"
		if not local_path.endswith("/"):
			local_path += "/"
		with contextlib.suppress(FileExistsError):
			os.makedirs(local_path)
		for vfsentry in self._adc.list_directory(remote_path):
			if vfsentry.filetype == "file":
				self._copy_file(vfsentry.path, local_path + os.path.basename(vfsentry.path))
			elif self._args.recurse:
				dirname = os.path.basename(vfsentry.path)
				self._copy_directory(remote_path + dirname + "/", local_path + dirname + "/")
		if not self._args.empty_directories:
			with contextlib.suppress(OSError):
				os.rmdir(local_path)

	def _copy_file(self, remote_filename, local_filename):
		if os.path.isfile(local_filename) and self._args.fast_skip:
			print("Fast skipping: %s" % (remote_filename))
			return

		fstat = self._adc.stat_file(remote_filename)
		if fstat is None:
			print("Cannot stat: %s" % (remote_filename))
			return

		if (fstat.size == 0) and (not self._args.zero_files):
			print("Filesize zero: %s" % (remote_filename))
			return

		if os.path.exists(local_filename):
			if self._args.overwrite != "always":
				print("Not overwriting: %s --(%s)--> %s" % (remote_filename, fstat.size, local_filename))
				return

		# Copy
		print("%s --(%s)--> %s" % (remote_filename, fstat.size, local_filename))
		if not self._args.no_copy:
			with open(local_filename, "wb") as f:
				content = self._adc.retrieve_file(remote_filename)
				written = f.write(content)
				success = (written == fstat.size)
			os.utime(local_filename, (fstat.mtime, fstat.mtime))
			if not success:
				print("Error copying: %s" % (remote_filename), file = sys.stderr)
				os.unlink(local_filename)

	def run(self):
		remote_path = self._args.src[1]
		local_path = self._args.dst

		root_stat = self._adc.stat(remote_path)
		if root_stat is None:
			print("Could not stat: %s" % (remote_path), file = sys.stderr)
			return
		if self._args.verbose >= 2:
			print("Root stat: %s" % (str(root_stat)))

		if root_stat.filetype == "file":
			self._copy_file(remote_path, local_path)
		else:
			self._copy_directory(remote_path, local_path)

ac = AndroidCopier(args)
ac.run()
