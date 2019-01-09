
import aiohttp_mako
from aiohttp import web 


@aiohttp_mako.template('index.html')
async def handle(request):
    return {}


def init():
    app = web.Application()

    #aiohttp_mako.setup(app, directories='html-test')
    lookup = aiohttp_mako.setup(app,directories=['html-test'], 
                                    input_encoding='utf-8',
                                    output_encoding='utf-8',
                                    default_filters=['decode.utf8'])


    app.router.add_get('/', handle)
    app.router.add_static('/static', 'static')
    return app

web.run_app(init(), port=8989)
