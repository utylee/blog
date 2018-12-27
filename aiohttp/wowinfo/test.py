from aiohttp import web
import aiohttp_mako 

# 웹소켓 핸들러입니다
async def ws_handle(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.data == 'connect':
            await ws.send_str('fuck')

    return ws


@aiohttp_mako.template('index.html')
async def handle(request):
    #return web.Response(text='fuck')
    return {'name': '한글은 어떨지'}

async def init():
    app = web.Application()
    lookup = aiohttp_mako.setup(app,directories=['html'])
    #lookup = aiohttp_mako.setup(app, directories=['.'])
    #lookup = aiohttp_mako.setup(app)
    #mytemplate = lookup.get_template("index.html")
    #lookup.put_string('index.html', '''<h2>${name}</h2>''')

    app.router.add_get('/', handle)

    # 웹소켓 핸들러도 get을 통해 정의해줘야합니다
    app.router.add_get('/ws', ws_handle)

    return app



web.run_app(init())
