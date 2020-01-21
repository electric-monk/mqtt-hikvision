import bus, hiksound, utils
import config
import time

cfg = bus.Config()
cfg.host = config.mqtt.host
cfg.username = config.mqtt.username
cfg.password = config.mqtt.password

camera = hiksound.Hikvision(config.cam.host, config.cam.username, config.cam.password)
audio = camera.openAudioChannel(1)

recorder = bus.Recorder("record", cfg)
player = bus.Player("play", cfg)

player.on_wave = lambda wave: audio.play(utils.wave_to_ulaw(wave))

player.run()
recorder.run()
while True:
	time.sleep(1/10)
	data = audio.read()
	wave = utils.ulaw_to_wave(data)
	recorder.publish_wave(wave)

