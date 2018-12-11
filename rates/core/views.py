import json
from datetime import datetime, timedelta

from aiohttp import web, WSMsgType # NOQA

from rates.core.log import logger


class PairsList(web.View):

    async def get(self):
        pool = self.request.app['pool']
        async with pool.acquire() as conn:
            async with conn.transaction():
                values = await conn.fetch("""SELECT id, symbol FROM pairs""")
                text = {value.get('id'): value.get('symbol') for value in values}
                return web.json_response(text)


class WebSocket(web.View):

    @staticmethod
    async def read_subscription(ws, redis, channel_id):
        channel, = await redis.subscribe(f'channel:{channel_id}')

        while await channel.wait_message():
            msg = await channel.get(encoding='utf-8')
            data = json.loads(msg)
            result = {
                'message': {'assetName': data['symbol'], 'time': data['timestamp'], 'assetId': data['pair_id'],
                            'value': data['value']},
                'action': 'point'
            }
            await ws.send_json(result)

    async def get(self): # NOQA
        pool = self.request.app['pool']
        ws = web.WebSocketResponse()
        ws['task'] = None

        await ws.prepare(self.request)
        logger.debug('websocket connection ready')

        for _ws in self.request.app['websockets']:
            await _ws.send_str('%s joined' % 1)
        self.request.app['websockets'].append(ws)

        async for msg in ws:
            logger.debug(msg)
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    for _ws in self.request.app['websockets']:
                        data_json = json.loads(msg.data)
                        if data_json['action'] == 'assets':
                            async with pool.acquire() as conn:
                                async with conn.transaction():
                                    values = await conn.fetch("""SELECT id, symbol FROM pairs""")
                            result = {
                                'action': 'assets',
                                'message': {
                                    'assets': [
                                        {
                                            'id': value.get('id'),
                                            'symbol': value.get('symbol')
                                        } for value in values
                                    ]
                                }
                            }
                            await _ws.send_json(result)

                        if data_json['action'] == 'subscribe':
                            pair_id = data_json['message']['assetId']
                            time_delta = datetime.utcnow() - timedelta(minutes=30)

                            async with pool.acquire() as conn:
                                async with conn.transaction():
                                    values = await conn.fetch("""
                                        SELECT p.symbol, timestamp, pair_id, value
                                        FROM points JOIN pairs p on points.pair_id = p.id
                                        WHERE pair_id=$1 AND timestamp > $2;""", pair_id, time_delta)
                            result = {
                                'message': {
                                    'points': [
                                        {
                                            'assetName': value.get('symbol'),
                                            'time': value.get('timestamp').timestamp(),
                                            'assetId': value.get('pair_id'),
                                            'value': value.get('value')
                                        } for value in values
                                    ]
                                }
                            }
                            await _ws.send_json(result)
                            if _ws['task']:
                                _ws['task'].cancel()
                            _ws['task'] = self.request.app.loop.create_task(
                                self.read_subscription(_ws, self.request.app['redis'], pair_id))

            elif msg.type == WSMsgType.ERROR:
                logger.debug('ws connection closed with exception %s' % ws.exception())

        self.request.app['websockets'].remove(ws)
        for _ws in self.request.app['websockets']:
            _ws.send_str('%s disconected' % 1)
            logger.debug('websocket connection closed')

        return ws
