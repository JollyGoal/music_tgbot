import config as conf  # custom configurations
from pyrogram import Client
import asyncio

api_id = conf.API_ID
api_hash = conf.API_HASH

# app = Client("music_session", api_id, api_hash, phone_number=conf.PHONE_NUMBER)


async def find_audio(query, page=0):
    print('start')
    async with app:
        messages = []
        async for message in app.search_messages(conf.MUSIC_DATABASE_CHANNEL_ID, query=query,
                                                 limit=conf.ELEMENTS_PER_PAGE,
                                                 offset=page * conf.ELEMENTS_PER_PAGE):
            messages.append(message)
    print('ff')
    return messages


if __name__ == '__main__':
    app = Client("music_session", api_id, api_hash, phone_number=conf.PHONE_NUMBER)
    app.run(find_audio("Lion"))
