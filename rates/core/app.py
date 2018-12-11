from aiohttp import web

import aioredis

import asyncpg

from rates.config import settings
from rates.core.routes import urls

__all__ = (
    'init_app',
)


async def on_shutdown(app):
    for ws in app['websockets']:
        await ws.close(code=1001, message='Server shutdown')


async def init_app():
    app = web.Application(router=urls, debug=settings.DEBUG)
    app['pool'] = await asyncpg.create_pool(**settings.DATABASE)
    app['redis'] = await aioredis.create_redis(('redis', 6379),
                                               db=1, encoding='utf-8')
    app['websockets'] = []

    app.on_cleanup.append(on_shutdown)
    return app
