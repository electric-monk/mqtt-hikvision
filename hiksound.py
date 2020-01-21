import urllib.request
import xml.etree.ElementTree as ET
import threading
import queue
import http.client
import time
import socket

import logging
http.client.HTTPConnection.debuglevel=1000
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

# A horrible hack, so as to allow us to recover the socket we still need from urllib
class SocketGrabber:
	def __init__(self):
		self.sock = None
	def __enter__(self):
		self._temp = socket.socket.close
		socket.socket.close = lambda sock: self._close(sock)
		return self
	def __exit__(self, type, value, tb):
		socket.socket.close = self._temp
		if tb is not None:
			self.sock = None
	def _close(self, sock):
		if sock._closed:
			return
		if self.sock == sock:
			return
		if self.sock is not None:
			self._temp(self.sock)
		self.sock = sock

class Hikvision:

	class _AudioChannel:
		def __init__(self, owner, index):
			req = urllib.request.Request(f"{owner._base}/ISAPI/System/TwoWayAudio/channels/{index}/open", method='PUT')
			resp = owner._opener.open(req)
			audiopath = f"{owner._base}/ISAPI/System/TwoWayAudio/channels/{index}/audioData"
			with SocketGrabber() as sockgrab:
				req = urllib.request.Request(audiopath, method='PUT')
				resp = owner._opener.open(req)
				self._output = sockgrab.sock
			self._tosend = queue.Queue()
			timer = threading.Thread(target = self._send128)
			self.sent = 0
			self.blank = 0
			timer.start()
			with SocketGrabber() as sockgrab:
				req = urllib.request.Request(audiopath, method='GET')
				resp = owner._opener.open(req)
				self._input = sockgrab.sock
			capture = threading.Thread(target = self._reader)
			self._received = queue.Queue()
			capture.start()

		def _reader(self):
			while True:
				data = self._input.recv(4096)
				if len(data):
					self._received.put(data)

		chunksize = 128

		def _send128(self):
			try:
				while True:
					time.sleep(1.0/64)
					if not self._tosend.empty():
						self._output.send(self._tosend.get())
						self.sent += 1
					else:
						self._output.send(b'\xff' * self.chunksize)
						self.blank += 1
			except Exception as e:
				print(f"Sent {self.sent} blank {self.blank} [{e}]")

		def play(self, ulaw_data):
			for x in [ulaw_data[i:i+self.chunksize] for i in range(0, len(ulaw_data), self.chunksize)]:
				self._tosend.put(x + (b'\xff' * (self.chunksize - len(x))))

		def read(self):
			res = b''
			max_count = 100
			while max_count and not self._received.empty():
				res += self._received.get()
				max_count -= 1
			return res

	def __init__(self, ip, username, password):
		self._base = f"http://{ip}"
		mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
		mgr.add_password(None, [self._base], username, password)
		self._auth = urllib.request.HTTPDigestAuthHandler(mgr)
		self._opener = urllib.request.build_opener(self._auth)

	def getAudioChannels(self):
		req = self._opener.open(f"{self._base}/ISAPI/System/TwoWayAudio/channels")
		data = ET.XML(req.read())
		if data.tag != '{http://www.hikvision.com/ver20/XMLSchema}TwoWayAudioChannelList':
			raise ValueError(f"Didn't expect {data.tag}")
		res = []
		for channel in data:
			if channel.tag != '{http://www.hikvision.com/ver20/XMLSchema}TwoWayAudioChannel':
				raise ValueError(f"Didn't expect {channel.tag}")
			res.append(int(channel[0].text))
		return res

	def openAudioChannel(self, channel):
		return self._AudioChannel(self, channel)

