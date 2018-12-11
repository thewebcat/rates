import asyncio
import json
import re
from datetime import datetime


import aiohttp

import aioredis

import asyncpg

from rates.config import settings


class PointsUpdater:
    def __init__(self, url, loop):
        self.url = url
        self.loop = loop
        self.session = aiohttp.ClientSession(loop=loop)

    async def _fetch(self, url):
        async with self.session.get(url) as response:
            status = response.status
            assert status == 200
            data = await response.text()
            return data

    @staticmethod
    async def load_pairs():
        conn = await asyncpg.connect(**settings.DATABASE)
        values = await conn.fetch("""SELECT id, symbol FROM pairs""")
        await conn.close()
        return values

    @staticmethod
    async def insert_point(symbol, pair_id, value):
        conn = await asyncpg.connect(**settings.DATABASE)
        await conn.execute("""
                INSERT INTO points(pair_id, value) VALUES($1, $2)
            """, pair_id, value)
        await conn.close()
        redis = await aioredis.create_redis(('redis', 6379),
                                            db=1, encoding='utf-8')
        await redis.publish(f'channel:{pair_id}',
                            json.dumps({'symbol': symbol, 'timestamp': datetime.now().timestamp(), 'pair_id': pair_id,
                                        'value': value}))

    async def __call__(self):
        data = await self._fetch(self.url)
        data = data.replace(',}', '}')
        data = re.search(r'null\((.*?)\);', data).group(1)
        rates = json.loads(data)

        pairs = await self.load_pairs()

        for item in rates['Rates']:
            for pair in pairs:
                if item['Symbol'] == pair.get('symbol'):
                    await self.insert_point(pair.get('symbol'), pair.get('id'),
                                            (float(item['Bid']) + float(item['Ask'])) / 2)


loop = asyncio.get_event_loop()
update = PointsUpdater(url='https://ratesjson.fxcm.com/DataDisplayer', loop=loop)


async def periodic_update():
    while True:
        await update()
        await asyncio.sleep(5, loop=loop)

task = loop.create_task(periodic_update())
loop.run_forever()
