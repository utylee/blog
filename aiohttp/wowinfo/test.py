import asyncio
from aiohttp import web
import aiohttp_mako 
import sqlalchemy as sa
from aiopg.sa import create_engine
from auction import get_decoed_item_set, db_update_from_server
import datetime
from db_tableinfo import *
'''
metadata = sa.MetaData()
items = {}
myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
locale = 'ko_KR'
'''

# 서버 선택
server = '아즈샤라'
#currentset = '격아약초세트1'
currentset = 'defaultset'

# 관심 아이템들 목록
pin_items = ['하늘 골렘', '아쿤다의 이빨', '닻풀', # 심해 가방', '사술매듭 가방'
            '살아있는 강철', '민첩의 전투 물약', '물결의 영약'] #'호화로운 모피']
#pin_items = ['살아있는 강철', '하늘 골렘']

# fetch 실행 주기 :5분
interval = 1800 #초
ws = 0
ar = {} 

# 웹소켓 핸들러입니다
async def ws_handle(request):
    global ws
    ws = web.WebSocketResponse()
    #print(ws)
    await ws.prepare(request)
    #print(ws)

    async for msg in ws:
        if msg.data == 'connect':
            print('update on connect')
            await ws.send_str('update')

    return ws

async def update(request):
    global ar
    global server
    global currentset
    print("/update handler came in")
    #print(ar)
    
    #ar = await get_decoed_item_set(server, currentset)
    data = {}
    data['ar'] = ar

    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(tbl_wow_server_info.select().where(tbl_wow_server_info.c.server==server)):
                data['time'] = r[1]

    return web.json_response(data)
    #return web.json_response(ar)

@aiohttp_mako.template('index.html')
async def handle(request):
    #return web.Response(text='fuck')
    global ar
    global server
    '''
    ar = [{'name':'사술매듭 가방', 'price': [30,20,40], 'image':'inv_tailoring_hexweavebag.jpg'},
        {'name':'하늘 골렘', 'price': [150000,20,40], 'image':'ability_mount_shreddermount.jpg'},
        {'name':'심해 가방', 'price': [150000,20,40], 'image':'inv_tailoring_80_deepseabag.jpg'},
        {'name':'유령무쇠 주괴', 'price': [150000,20,40], 'image':'inv_ingot_ghostiron.jpg'},
        {'name':'호화로운 모피', 'price': [150000,20,40], 'image':'inv_misc_nativebeastfur.jpg'},
        {'name':'살아있는 강철', 'price': [30,20,40], 'image':'inv_ingot_livingsteel.jpg'}]
        '''

    return {'name': '7', 'imageroot': '../static/images/' ,'ar':ar, 'server':server}

async def init():
    global interval
    global ws
    init_data()
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
    app.router.add_get('/update', update)

    # 웹소켓 핸들러도 get을 통해 정의해줘야합니다
    ws = app.router.add_get('/ws', ws_handle)

    loop = asyncio.get_event_loop()
    loop.create_task(main_proc(interval))

    return app

async def main_proc(intv):
    # 한국 와우 서버 리스트를 가져옵니다
    serverlist = []
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(tbl_wow_server_info.select()):
                serverlist.append(r[0])

    await fetch_auction()
    
    serverlist = ['아즈샤라']
    # 주기마다 반복합니다
    while True:
        loop = asyncio.get_event_loop()
        loop.create_task(timer_proc(serverlist))
        await asyncio.sleep(intv)

async def timer_proc(serverlist):
    for s_ in serverlist:
        await db_update_from_server(s_)
        await fetch_auction()

async def fetch_auction():
    print('.경매장 정보 가져오기 시작')

    global ws
    global ar
    global currentset
    global server

    #result_dict = await proc(item_list)
    #ar = await proc(server,item_list)
    ar = await get_decoed_item_set(server, currentset)

    print('update in fetch')
    try:
        print('ws: send update string')
        await ws.send_str('update')
    except:
        print('ws send err!!!!')

def init_data():
    global ar


    ar = {'사술매듭 가방': {'num': 10, 'min': 1379999900, 'min_seller': '밀림왕세나씨', 'min_chain':'0'}, 
                '심해 가방': {'num': 300, 'min': 18000000, 'min_seller': '인중개박살'}, 
                '호화로운 모피': {'num': 158, 'min': 4000, 'min_seller': '우렝밀렵'}, 
                '하늘 골렘': {'num': 173, 'min': 18560000, 'min_seller': '남미왕'}, 
                '살아있는 강철': {'num': 77, 'min': 34900000, 'min_seller': '임리치'}, 
                '민첩의 전투 물약': {'num': 25, 'min': 3505000, 'min_seller': 'Spit'}}
    for a in ar.keys():
        ar[a]['image'] = 'inv_tailoring_hexweavebag.jpg'
        min_chain = []
        for c_ in range(0, 1440):
            min_chain.append(0)
        ar[a]['min_chain'] = min_chain 
        ar[a]['gold'] = 0
        ar[a]['silver'] =0
        ar[a]['copper'] =0

web.run_app(init(),port=7777)
