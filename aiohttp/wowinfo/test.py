import asyncio
from aiohttp import web
import aiohttp_mako 
import sqlalchemy as sa
from aiopg.sa import create_engine
from auction import proc
import datetime
'''
metadata = sa.MetaData()
items = {}
myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
locale = 'ko_KR'
'''

# 서버 선택
server = '아즈샤라'

# 관심 아이템들 목록
pin_items = ['사술매듭 가방', '하늘 골렘', '심해 가방', 
            '살아있는 강철', '민첩의 전투 물약', '물결의 영약'] #'호화로운 모피']
#pin_items = ['살아있는 강철', '하늘 골렘']

# fetch 실행 주기 :5분
interval = 30000 #초
ws = 0
ar = {} 
ftime = '00:00-99/99/99'  # db dump시의 시간을 저장합니다

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
    global ftime
    #print("/update handler came in")
    #print(ar)
    
    data = {}
    data['ar'] = ar
    data['time'] = ftime

    return web.json_response(data)
    #return web.json_response(ar)

@aiohttp_mako.template('index.html')
async def handle(request):
    #return web.Response(text='fuck')
    global ar
    '''
    ar = [{'name':'사술매듭 가방', 'price': [30,20,40], 'image':'inv_tailoring_hexweavebag.jpg'},
        {'name':'하늘 골렘', 'price': [150000,20,40], 'image':'ability_mount_shreddermount.jpg'},
        {'name':'심해 가방', 'price': [150000,20,40], 'image':'inv_tailoring_80_deepseabag.jpg'},
        {'name':'유령무쇠 주괴', 'price': [150000,20,40], 'image':'inv_ingot_ghostiron.jpg'},
        {'name':'호화로운 모피', 'price': [150000,20,40], 'image':'inv_misc_nativebeastfur.jpg'},
        {'name':'살아있는 강철', 'price': [30,20,40], 'image':'inv_ingot_livingsteel.jpg'}]
        '''

    return {'name': '7', 'imageroot': '../static/images/' ,'ar':ar}

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
    loop.create_task(main_proc(pin_items, interval))

    return app

async def main_proc(item_list, intv):
    # 5분마다 반복합니다
    while True:
        await fetch_auction(item_list)

        await asyncio.sleep(intv)

async def fetch_auction(item_list):
    print('.경매장 정보 가져오기 시작')

    global ws
    global ar
    global ftime

    #result_dict = await proc(item_list)
    ar = await proc(server,item_list)

    now = datetime.datetime.now()
    ftime = now.strftime("%H:%M-%m/%d/%y")

    print('update in fetch')
    try:
        await ws.send_str('update')
    except:
        pass

def init_data():
    global ar

    ar = {'사술매듭 가방': {'num': 10, 'min': 1379999900, 'min_seller': '밀림왕세나씨'}, 
                '심해 가방': {'num': 300, 'min': 18000000, 'min_seller': '인중개박살'}, 
                '호화로운 모피': {'num': 158, 'min': 4000, 'min_seller': '우렝밀렵'}, 
                '하늘 골렘': {'num': 173, 'min': 18560000, 'min_seller': '남미왕'}, 
                '살아있는 강철': {'num': 77, 'min': 34900000, 'min_seller': '임리치'}, 
                '민첩의 전투 물약': {'num': 25, 'min': 3505000, 'min_seller': 'Spit'}}
    for a in ar.keys():
        ar[a]['image'] = 'inv_tailoring_hexweavebag.jpg'
        ar[a]['gold'] = 0
        ar[a]['silver'] =0
        ar[a]['copper'] =0

web.run_app(init(),port=7777)
