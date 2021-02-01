from aiohttp import web

async def hello(request):
    return web.Response(text="Hello, world")

async def main():
    app = web.Application()
    app.add_routes([web.get('/', hello)])
    return app
