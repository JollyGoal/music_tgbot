import vk_audio
import config as conf  # custom configurations
import requests

vk = vk_audio.VkAudio(login=conf.LOGIN, password=conf.PASSWORD)


def find_music(text):
    data = vk.search(text)
    audios = data.Audios
    # for aud in audios:
    #     print(aud.title, " - ", aud.artist)
    return audios


def get_audio(lookup_id):
    elem = vk.get_by_id(lookup_id)
    r = requests.get(elem[0].url, allow_redirects=True)
    with open(f'cache/{elem[0].id}', 'wb') as f:
        f.write(r.content)
    return [elem[0], f'cache/{elem[0].id}']
