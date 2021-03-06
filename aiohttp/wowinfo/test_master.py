import asyncio
from aiohttp import web
import datetime
import time
import argparse
import aiohttp
import logging
import logging.handlers
import aiohttp_mako 
import sqlalchemy as sa
from aiopg.sa import create_engine
#from auction import *
import auction as auc
#from auction import get_decoed_item_set, get_decoed_item, db_update_from_server
#from auction_classes import *
import auction_classes as a_cl
#from auction_classes import Set
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
parser = argparse.ArgumentParser(description="wowinfo")
parser.add_argument('--path')
parser.add_argument('--port')

# 로깅을 설정합니다. getLogger()를 통해 root를 설정해 놓으면 이후 logging으로 바로 사용해도 됩니다
log_path = 'single'
log = logging.getLogger('single')
log.setLevel(logging.INFO)
#저렇게 home 경로에 저장하니 두줄씩 써지는 버그가 있습니다
#fileHandler = logging.FileHandler('/home/pi/wowinfo.log')
fileHandler = logging.FileHandler('single.log')
fileHandler.setFormatter(logging.Formatter('%(asctime)s-%(name)s-%(message)s'))
log.addHandler(fileHandler)


# 서버 선택
server = '아즈샤라'
#currentset = '격아약초세트1'
currentset = '기본구성'
defaultset = '기본구성'
defaultuser = 'guest'
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
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'connect':
                print('update on connect')
                log.info('update on connect')
                await ws.send_str('update')
            elif msg.data == 'close':
                await ws.close()
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connecion closed with exception {}'.format(ws.exception()))

        ''' nginx server{}에 ws관련해서 따로 설정을 해줘야합니다
        아 그냥 /ws이 아닌 / 에 아래값을 추가해주니 되네요
        location /ws {
            proxy_pass http://aiohttp;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        '''
  



    return ws

async def create_itemset(request):
    print('/create_itemset handler came in')
    log.info('/create_itemset handler came in')
    user = request.match_info['cur_user']
    setname = request.match_info['setname']
    success = await auc.create_itemset(user, setname, defaultuser, defaultset) 
    data = {}
    data['success'] = success

    return web.json_response(data)

async def delete_itemset(request):
    print('/delete_itemset handler came in')
    log.info('/delete_itemset handler came in')
    user = request.match_info['cur_user']
    setname = request.match_info['setname']
    success = await auc.delete_itemset(user, setname)
    data = {}
    data['success'] = success

    return web.json_response(data)

async def update_indiv(request):
    print('/update_indiv handler came in')
    log.info('/update_indiv handler came in')
    pos_no = request.match_info['num']
    item_name = request.match_info['itemname']
    srver = request.match_info['server']
    user = request.match_info['cur_user']
    item_set = request.match_info['cur_itemset']

    a = time.time()
    indiv_ar = await auc.get_decoed_item(srver, item_set, pos_no, item_name)
    b = time.time()
    sub = round(b - a,2)
    print(f':{sub}초 소요')
    log.info(f':{sub}초 소요')
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
    log.info('/update handler came in')

    itemset = request.match_info['itemset']
    srver = request.match_info['server']
    user = request.match_info['cur_user']
    '''
    proto = request.match_info['proto']
    print(f':itemset = {itemset}')
    if(proto == '_default'):
        print('DEFAULT!!!!')
        '''

    '''
    if currentset != itemset:
        currentset = itemset
        ar = await get_decoed_item_set(server, currentset)
    '''
    # 굳이 글로벌로 균일하게 갖고 있는 것은 말이 안됩니다. 사용자가 원하는 상황마다 그대로 전달해줘야합니다
    start_time = time.time()
    set_ = a_cl.Set(itemset).fork()
    dict_ = await set_.get_decoed_item_set(srver)
    #array = await get_decoed_item_set(srver, itemset)
    finished_time = time.time()
    proc_time = round(finished_time - start_time, 3)
    print(f'fetch elapsed time: {proc_time} 초')
    log.info(f'fetch elapsed time: {proc_time} 초')

    #print(ar)
    #ar = await get_decoed_item_set(server, currentset)
    data = {}
    itemsets = []

    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.212',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(di.tbl_wow_server_info.select().where(di.tbl_wow_server_info.c.server==server)):
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
    set_ = a_cl.Set(currentset).fork()
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
    app.router.add_get('/update/{server}/{cur_user}/{itemset}', update)
    #app.router.add_get('/update/{server}/{cur_user}/{itemset}/{proto}', update)
    app.router.add_get('/update_indiv/{num}/{server}/{cur_user}/{cur_itemset}/{itemname}', update_indiv)
    app.router.add_get('/create_itemset/{cur_user}/{setname}', create_itemset)
    app.router.add_get('/delete_itemset/{cur_user}/{setname}', delete_itemset)

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
                            host='192.168.0.212',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(di.tbl_wow_server_info.select()):
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
        await auc.db_update_from_server(s_, defaultset)
        await fetch_auction()

async def fetch_auction():
    print('.경매장 정보 가져오기 시작')
    log.info('.경매장 정보 가져오기 시작')

    global ws
    global ar
    global currentset
    global server

    #ar = await get_decoed_item_set(server, currentset)

    print('update in fetch')
    log.info('update in fetch')
    try:
        print('ws: send update string')
        log.info('ws: send update string')
        await ws.send_str('update')
    except:
        print('ws send err!!!!')
        log.info('ws send err!!!!')

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
                            host='192.168.0.212',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(di.tbl_item_set.select()):
                itemset_names.append(r[0])
    return itemset_names

#web.run_app(init(),port=7777)
if __name__ == '__main__':
    #formatter = logging.Formatter('%(asctime)s-%(message)s')
    #fileHandler.setFormatter(formatter)
    #log.addHandler(logging.FileHandler('my.log').setFormatter(logging.Formatter('%(asctime)s-%(message)s')))
    #logging.basicConfig(filename='my.log', level=logging.INFO, format='%(asctime)s-%(message)s')
    app = web.Application()
    # configure app

    args = parser.parse_args()
    web.run_app(init(), port=7777)
    #web.run_app(init(), path=args.path, port=args.port)
