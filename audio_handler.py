import asyncio

import config as conf  # custom configurations
from pyrogram import Client
import requests
import vk_audio
from vkaudiotoken import get_kate_token, get_vk_official_token


api_id = conf.API_ID
api_hash = conf.API_HASH


# print(get_vk_official_token(login, password))


# app = Client("music_session", api_id, api_hash, phone_number=conf.PHONE_NUMBER)

class UserClass:
    app = Client("music_session", api_id, api_hash, phone_number=conf.PHONE_NUMBER)

    async def find_audio(self, query, page=1):
        page = page - 1
        print('start')
        async with self.app:
            messages = []
            async for message in self.app.search_messages(conf.YT_MUSIC_DATABASE_CHANNEL_ID, query=query,
                                                          limit=conf.ELEMENTS_PER_PAGE,
                                                          offset=page * conf.ELEMENTS_PER_PAGE):
                messages.append(message)
        print('ff')
        return messages


async def search_vk_audio(query: str):
    kate_client = get_kate_token(conf.LOGIN, conf.PASSWORD)
    kate_token = kate_client['token']
    kate_user_agent = kate_client['user_agent']

    sess = requests.session()
    sess.headers.update({'User-Agent': kate_user_agent})

    result = sess.get(
        "https://api.vk.com/method/audio.search",
        params=[
            ('access_token', kate_token),
            ('audios', '371745461_456289486'),
            ('q', query),
            ('v', '5.95'),
        ]
    )
    js = result.json()
    for elem in js['response']['items']:
        print(vk_audio.decode(elem['url']))
    print(js)


def vk_audio_search():
    vk = vk_audio.VkAudio(login=conf.LOGIN, password=conf.PASSWORD)
    data = vk.search("burn")
    audio = data.Audios
    print(audio)




if __name__ == '__main__':
    asyncio.run(search_vk_audio("Lion"))
    # vk_audio_search()
#     user_class = UserClass()
#     user_class.app.run(user_class.find_audio(query="Lion"))
