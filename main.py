import vk_audio
import config as conf

vk = vk_audio.VkAudio(login=conf.LOGIN, password=conf.PASSWORD)
data = vk.search("Rapture Rising JT machinima")
audio = data.Audios
print(audio)
# playlists = data.PLaylists
# artists = data.artists_info
