#	airdroidclient - Scriptable interface to the Airdroid smart phone app
#	Copyright (C) 2019-2019 Johannes Bauer
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
import collections
import contextlib
import urllib.parse
import requests
from DESEncrypt import DESEncrypt

class ConnectionException(Exception): pass

class AirdroidConnection():
	_VFSEntry = collections.namedtuple("VFSEntry", [ "filetype", "path", "size", "mtime" ])
	_FILETYPES = {
		0:	"file",
		1:	"systemdir",
		2:	"dir",
	}

	def __init__(self, endpoint):
		self._endpoint = endpoint
		self._sess = requests.Session()
		self._login_data = { }
		self._des_crypto = None

	def _get(self, path, params = None, result = "json"):
		uri = self._endpoint + path
		if params is not None:
			uri += "?" + urllib.parse.urlencode(params)
		response = self._sess.get(uri)
		if response.status_code != 200:
			raise ConnectionException("Error sending request to %s to Airdroid: %s" % (path, str(response)))
		if result == "json":
			data = response.json()
		elif result == "raw":
			data = response.content
		else:
			data = response
		return data

	def login(self):
		login_data = self._get("/sdctl/comm/lite_auth/")
		des_mask = bytes.fromhex(login_data["7bb"][3 : 3 + 4])
		masked_des_key = bytes.fromhex(login_data["dk"])
		des_key = bytes(keybyte ^ des_mask[i % len(des_mask)] for (i, keybyte) in enumerate(masked_des_key))
		self._des_crypto = DESEncrypt(des_key)
		self._login_data = login_data
		return login_data

	def get_file_properties(self, filename):
		params = {
			"files":		os.path.basename(filename),
			"dirs":			"",
			"spath":		os.path.dirname(filename),
			"uris":			"",
			"child_uris":	"",
			"7bb":			self._login_data["7bb"],
			"des":			"1",
		}
		result = self._get("/sdctl/file_v21/properties", params)
		filetype = self._FILETYPES.get(result["code"], "unknown")
		vfsentry = self._VFSEntry(filetype = filetype, path = filename, size = result["size"], mtime = result["last_modified_time"] / 1000)
		return vfsentry

	def query_path(self, filename):
		params = {
			"cur_path":		filename,
			"uri":			"",
			"child_uri":	"",
			"7bb":			self._login_data["7bb"],
			"des":			"1",
		}
		result = self._get("/sdctl/file_v21/query", params)
		base_path = result["cur_path"]
		if not base_path.endswith("/"):
			base_path += "/"
		for entry in result["list"]:
			filetype = self._FILETYPES.get(entry["type"], "unknown")
			_VFSEntry = collections.namedtuple("VFSEntry", [ "filetype", "path", "size", "mtime" ])
			vfsentry = self._VFSEntry(filetype = filetype, path = base_path + entry["name"], size = entry.get("size", 0), mtime = entry["last_modified"] / 1000)
			yield vfsentry

	def walk_path(self, filename):
		for vfsentry in self.query_path(filename):
			yield vfsentry
			if vfsentry.filetype in [ "systemdir", "dir" ]:
				yield from self.walk_path(vfsentry.path)

	def mkdir(self, path):
		result = self._get("/sdctl/file_v21/createdir", params)

	def queryfile(self, path):
		result = self._get("/sdctl/file_v21/querydir", params)

	def retrieve_file(self, filename, mtime = None):
		filename = filename.encode("utf-8")
		encrypted_filename = self._des_crypto.encrypt(filename)
		params = {
			"pathfile":			encrypted_filename.hex(),
			"saveas":			"1",
			"7bb":				self._login_data["7bb"],
			"des":				"1",
		}
		if mtime is not None:
			params["last_modified"] = round(mtime * 1000)
		content = self._get("/sdctl/file_v21/export", params, result = "raw")
		return content

	def download_vfsentry(self, vfsentry, destination_directory, on_exists = "ignore"):
		assert(on_exists in [ "ignore", "overwrite", "overwrite_if_newer" ])
		with contextlib.suppress(FileExistsError):
			os.makedirs(destination_directory)
		destination_filename = destination_directory + "/" + os.path.basename(vfsentry.path)
		if (on_exists == "ignore") and os.path.exists(destination_filename):
			return
		if on_exists == "overwrite_if_newer":
			existing_mtime = os.path.stat(destination_filename).st_mtime
			print(existing_mtime)
			raise NotImplementedError("TODO")

		content = self.retrieve_file(vfsentry.path)
		with open(destination_filename, "wb") as f:
			f.write(content)
		os.utime(destination_filename, (vfsentry.mtime, vfsentry.mtime))

	def download_file(self, filename, destination_directory, on_exists = "ignore"):
		vfsentry = self.get_file_properties(filename)
		return self.download_vfsentry(vfsentry, destination_directory, on_exists = on_exists)
