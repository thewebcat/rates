from aiohttp.web import UrlDispatcher

from rates.core.views import PairsList, WebSocket

__all__ = (
    'urls',
)

urls = UrlDispatcher()

urls.add_route('GET', r'/pairs', PairsList, name='pairs-list')
urls.add_route('GET', r'/ws', WebSocket, name='websocket')
