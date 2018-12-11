from aiohttp import web

from rates.core.app import init_app


if __name__ == '__main__':
    web.run_app(init_app(), port=8000)
