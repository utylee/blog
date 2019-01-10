'''
/run local t,m,r=time()/60,1140;r=m-((t-24857880)%m);if r>720 then r=r-720;print(string.format("습격중!-%02d:%02d",r/60,r%60)) else print(string.format("다음습격-%02d:%02d",r/60,r%60)) end
'''

from aiohttp import web
import aiohttp_mako
import time

async def calc():
    t = time() / 60
    pass


@aiohttp_mako.template('index.html')
async def handle(request):
    calc()

    return ''

def init():
    app = web.Application()

    aiohttp_mako.setup(app,directories=['html_attack'], 
                                    input_encoding='utf-8',
                                    output_encoding='utf-8',
                                    default_filters=['decode.utf8'])

    app.router.add_get('/', handle)
    app.router.add_static('/static', 'static')

    return app

web.run_app(init(),port=5555)
