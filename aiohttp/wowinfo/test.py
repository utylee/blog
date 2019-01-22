import asyncio
from aiohttp import web
import aiohttp_mako 
import sqlalchemy as sa
from aiopg.sa import create_engine
#from auction import *
import auction as au
#from auction import get_decoed_item_set, get_decoed_item, db_update_from_server
#from auction_classes import *
import auction_classes as ac 
#from auction_classes import Set
import datetime
import time
#from db_tableinfo import *
import db_tableinfo as di 
'''
metadata = sa.MetaData()
items = {}
clientID = 'b934788e2cde4166acb93dcbf558040f'
new_myapi = 'nMA7eloEh2rHFEiRw9Xs5j0Li6ZaFA5A'
myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
locale = 'ko_KR'
'''

# 서버 선택
server = '아즈샤라'
#currentset = '격아약초세트1'
currentset = '기본구성'
defaultset = '기본구성'
imageroot = 'https://wow.zamimg.com/images/wow/icons/large/'

# 관심 아이템들 목록
pin_items = ['하늘 골렘', '아쿤다의 이빨', '닻풀', # 심해 가방', '사술매듭 가방'
            '살아있는 강철', '민첩의 전투 물약', '물결의 영약'] #'호화로운 모피']
#pin_items = ['살아있는 강철', '하늘 골렘']

# fetch 실행 주기 :5분
interval = 1800 #초
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

async def update_indiv(request):
    print('/update_indiv handler came in')
    pos_no = request.match_info['num']
    item_name = request.match_info['itemname']
    srver = request.match_info['server']
    item_set = request.match_info['cur_itemset']

    a = time.time()
    indiv_ar = await get_decoed_item(srver, item_set, pos_no, item_name)
    b = time.time()
    sub = round(b - a,2)
    print(f':{sub}초 소요')
    data = {}
    data['indiv_ar'] = indiv_ar 
    data['num'] = pos_no

    return web.json_response(data)

async def update(request):
    global ar
    global server
    #global currentset
    itemset = ''
    print('/update handler came in')

    itemset = request.match_info['itemset']
    srver = request.match_info['server']
    print(f':itemset = {itemset}')

    '''
    if currentset != itemset:
        currentset = itemset
        ar = await get_decoed_item_set(server, currentset)
    '''
    # 굳이 글로벌로 균일하게 갖고 있는 것은 말이 안됩니다. 사용자가 원하는 상황마다 그대로 전달해줘야합니다
    start_time = time.time()
    set_ = Set(itemset).fork()
    dict_ = await set_.get_decoed_item_set(srver)
    #array = await get_decoed_item_set(srver, itemset)
    finished_time = time.time()
    proc_time = round(finished_time - start_time, 3)
    print(f'fetch elapsed time: {proc_time} 초')

    #print(ar)
    #ar = await get_decoed_item_set(server, currentset)
    data = {}
    itemsets = []

    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(tbl_wow_server_info.select().where(tbl_wow_server_info.c.server==server)):
                data['time'] = r[1]
            #async for r in conn.execute(tbl_item_set.select()):
                #itemsets.append(r[0])

    #data['ar'] = ar
    #data['itemsets'] = itemsets
    data['ar'] = dict_
    data['itemsets'] = await get_itemsets()
    #data['currentset'] = currentset 

    return web.json_response(data)

@aiohttp_mako.template('index.html')
async def handle(request):
    #return web.Response(text='fuck')
    global ar
    global server
    global currentset
    global imageroot
    
    itemsets = await get_itemsets()
    #itemsets.remove(currentset)
    # default set이냐 아니냐로 분기하기 위함입니다
    set_ = Set(currentset).fork()
    dict_ = await set_.get_decoed_item_set(server)
    #array = await set_.get_decoed_item_set(server)
    #array = await get_decoed_item_set(server, currentset)
    #print(f'dict_:{dict_}')

    '''
    return {'name': '7', 'imageroot': '../static/images/' ,'ar':ar, 'server':server,
                    'itemsets': itemsets, 'current_itemset':currentset}
    '''
    return {'name': '7', 'imageroot': imageroot ,'ar':dict_, 'server':server,
                    'itemsets': itemsets, 'current_itemset':currentset}

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
    app.router.add_get('/update/{server}/{itemset}', update)
    app.router.add_get('/update_indiv/{num}/{server}/{cur_itemset}/{itemname}', update_indiv)

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

    # 제거해봅니다. 초기에 굳이 하지 않아도 handle(index.html)가 처리합니다
    #await fetch_auction()
    
    serverlist = ['아즈샤라']
    # 주기마다 반복합니다
    while True:
        loop = asyncio.get_event_loop()
        loop.create_task(timer_proc(serverlist))
        await asyncio.sleep(intv)

async def timer_proc(serverlist):
    for s_ in serverlist:
        await db_update_from_server(s_, defaultset)
        await fetch_auction()

async def fetch_auction():
    print('.경매장 정보 가져오기 시작')

    global ws
    global ar
    global currentset
    global server

    #ar = await get_decoed_item_set(server, currentset)

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

async def get_itemsets():
    itemset_names = []
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(tbl_item_set.select()):
                itemset_names.append(r[0])
    return itemset_names

web.run_app(init(),port=7777)
