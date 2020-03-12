from aiohttp import web
import aiohttp_mako


async def handle(request):
    return web.Response(text='kkkk')

app = web.Application()


app.router.add_get('/', handle)

if __name__ == "__main__":
    web.run_app(app, port="9999")
