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

import cryptography.hazmat

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class DESEncrypt():
	def __init__(self, key):
		assert(isinstance(key, bytes))
		assert(len(key) == 8)
		backend = default_backend()
		self._cipher = Cipher(algorithms.TripleDES(key), modes.ECB(), backend = backend)
		self._padder = padding.PKCS7(64)

	def encrypt(self, plaintext):
		encryptor = self._cipher.encryptor()
		padder = self._padder.padder()
		padded_plaintext = padder.update(plaintext) + padder.finalize()
		return encryptor.update(padded_plaintext) + encryptor.finalize()

	def decrypt(self, ciphertext):
		decryptor = self._cipher.decryptor()
		padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
		unpadder = self._padder.unpadder()
		return unpadder.update(padded_plaintext) + unpadder.finalize()

if __name__ == "__main__":
	des = DESEncrypt(bytes.fromhex("dde6ba6412edcac2"))
	plain = des.decrypt(bytes.fromhex("04fadaa90aad680e87cfc88a0432e8081a6e761f67964a2109362ef11ae1f8903a08b5608634b43a9a2884ee37cb18cd49be82a19165fe4c7d656d9e42277df84cdcb4f6dc8172325d1c64ac8cb2acf6"))
	assert(plain == b"/sdcard/DCIM/Screenshots/Screenshot_20181118-121219_Samsung Internet.jpg")
