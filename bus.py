import paho.mqtt.client as mqtt
import threading

class Config:
	def __init__(self):
		self.username = None
		self.password = None
		self.host = None
		self.port = 1883
		self.site = "default"

	def create_client(self, name):
		res = mqtt.Client(name)
		if self.username is not None:
			res.username_pw_set(self.username, self.password)
		return res

	def connect(self, client):
		client.connect(self.host, self.port)

class Client:
	def __init__(self, name, config):
		self.client = config.create_client(name)
		self.client.on_connect = self.on_connect
		self.client.on_disconnect = self.on_disconnect
		config.connect(self.client)

	def run(self):
		self.thread = threading.Thread(target=self.client.loop_forever)
		self.thread.start()
	def stop(self):
		self.client.disconnect()

	def on_connect(self, client, userdata, flags, result_code):
		pass
	def on_disconnect(self, client, userdata, flags, result_code):
		pass

class Recorder(Client):
	def __init__(self, id, config):
		super().__init__(f"recorder_{id}", config)
		self.site = config.site
	def publish_wave(self, wave_file):
		self.client.publish(f"hermes/audioServer/{self.site}/audioFrame", wave_file)

class Player(Client):
	def __init__(self, id, config):
		super().__init__(f"player_{id}", config)
		self.site = config.site
		self.on_wave = None
	def on_connect(self, client, userdata, flags, result_code):
		super().on_connect(client, userdata, flags, result_code)
		endpoint = f"hermes/audioServer/{self.site}/playBytes/+"
		self.client.subscribe(endpoint)
		self.client.message_callback_add(endpoint, self.on_play_bytes)
	def on_play_bytes(self, client, userdata, message):
		if self.on_wave is not None:
			self.on_wave(message.payload)

