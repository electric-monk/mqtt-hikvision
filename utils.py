import subprocess

def transcode(input, frm, to):
	cmd = ["ffmpeg"]
	cmd.extend(frm)
	cmd.extend(["-i", "-"])
	cmd.extend(to)
	cmd.append("-")
	task = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
	return task.communicate(input=input)[0]

def wave_to_ulaw(input):
	return transcode(input, ["-f", "wav"], ["-ar", "8000", "-ac", "1", "-ab", "64k", "-f", "mulaw"])

def ulaw_to_wave(input):
	return transcode(input, ["-ar", "8000", "-ac", "1", "-f", "mulaw"], ["-acodec", "pcm_s16le", "-f", "s16le", "-ar", "16000", "-ac", "1", "-f", "wav"])

