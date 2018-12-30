import asyncio
from aiohttp import web
import aiohttp_mako 
import sqlalchemy as sa
from aiopg.sa import create_engine
from auction import proc
'''
metadata = sa.MetaData()
items = {}
myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
server = '아즈샤라'
locale = 'ko_KR'
'''


# 관심 아이템들 목록
pin_items = ['사술매듭 가방', '하늘 골렘', '심해 가방', 
            '살아있는 강철', '유령무쇠 주괴', '호화로운 모피']

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
    ar = [{'name':'사술매듭 가방', 'price': [30,20,40], 'image':'inv_tailoring_hexweavebag.jpg'},
        {'name':'하늘 골렘', 'price': [150000,20,40], 'image':'ability_mount_shreddermount.jpg'},
        {'name':'하늘 골렘', 'price': [150000,20,40], 'image':'ability_mount_shreddermount.jpg'},
        {'name':'하늘 골렘', 'price': [150000,20,40], 'image':'ability_mount_shreddermount.jpg'},
        {'name':'하늘 골렘', 'price': [150000,20,40], 'image':'ability_mount_shreddermount.jpg'},
        {'name':'살아있는 강철', 'price': [30,20,40], 'image':'inv_ingot_livingsteel.jpg'}]

    return {'name': '7', 'ar':ar}

async def init():
    app = web.Application()
    # 한글 주석들이 파싱하다가 에러가 나버리는 바람에 샘플대로 encoding 옵션을 다시 모두 넣어줬습니다
    # directories 부분을 지정해주면 샘플과 달리 파일을 직접 언급해서 가져올수 있습니다
    lookup = aiohttp_mako.setup(app,directories=['html'], 
                                    input_encoding='utf-8',
                                    output_encoding='utf-8',
                                    default_filters=['decode.utf8'])
    
    #lookup = aiohttp_mako.setup(app, directories=['.'])
    #lookup.put_string('index.html', '''<h2>${name}</h2>''')

    app.router.add_static('/static', 'static')
    app.router.add_get('/', handle)

    # 웹소켓 핸들러도 get을 통해 정의해줘야합니다
    app.router.add_get('/ws', ws_handle)

    loop = asyncio.get_event_loop()
    loop.create_task(main_proc())
    print('안오나')

    return app

async def main_proc():
    # 5분마다 반복합니다
    while True:
        await fetch_auction()

        await asyncio.sleep(300)

async def fetch_auction():
    print('.경매장 정보 가져오기 시작')
    await proc()

web.run_app(init(),port=7777)
