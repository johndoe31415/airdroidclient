#!/usr/bin/env python3
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

import sys
from AirdroidConnection import AirdroidConnection
from FriendlyArgumentParser import FriendlyArgumentParser

parser = FriendlyArgumentParser()
parser.add_argument("--port", metavar = "port", type = int, default = 8888, help = "Port that Airdroid uses. Defaults to %(default)d.")
parser.add_argument("-p", "--path", metavar = "path", default = "/sdcard/DCIM/Camera", help = "Path that is downloaded from the smart phone. Defaults to %(default)s.")
parser.add_argument("-l", "--local", metavar = "path", default = "camera", help = "Local directory that the downloaded files are stored into. Defaults to %(default)s.")
parser.add_argument("hostname", metavar = "ipaddress", type = str, help = "Hostname or IP address where the Airdroid connection can be reached")
args = parser.parse_args(sys.argv[1:])

uri = "http://%s:%d" % (args.hostname, args.port)
adc = AirdroidConnection(uri)
adc.login()
for vfsentry in adc.query_path(args.path):
	print(vfsentry.path, vfsentry.size)
	adc.download_vfsentry(vfsentry, args.local)
