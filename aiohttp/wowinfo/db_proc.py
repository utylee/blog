import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
from auction import *
import logging
import logging.handlers
import pathlib
import ujson as json
#from collections import defaultdict

#interval = 1800 #초
#interval = 3600 #초
interval = 6000 #초
tok = ''
defaultset = '기본구성'
locale = 'ko_KR'
myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
cli = 'b934788e2cde4166acb93dcbf558040f'
pwd = 'nMA7eloEh2rHFEiRw9Xs5j0Li6ZaFA5A'
tok_url = 'https://apac.battle.net/oauth/token'  #apac = kr, tw
servers_dict = {}

# 로깅을 설정합니다. getLogger()를 통해 root를 설정해 놓으면 이후 logging으로 바로 사용해도 됩니다
log = logging.getLogger('dbproc')
log.setLevel(logging.INFO)
#저렇게 home 경로에 저장하니 두줄씩 써지는 버그가 있습니다
#fileHandler = logging.FileHandler('/home/pi/dbproc.log')
myhome = str(pathlib.Path.home())
fileHandler = logging.handlers.RotatingFileHandler(filename=myhome+'/dbproc.log', maxBytes=10*1024*1024,
                                                   backupCount=10)
fileHandler.setFormatter(logging.Formatter('[%(asctime)s]-(%(name)s)-%(message)s'))
log.addHandler(fileHandler)

async def main_proc(intv):
    global defaultset
    engine = await create_engine(user='postgres', 
                            database='auction_db',
                            host='192.168.0.212',
                            password='sksmsqnwk11')
    #serverlist = await get_serverlist(engine)
    #size = len(serverlist)
    #az = serverlist.index('아즈샤라')
    #hj = serverlist.index('하이잘')
    #etc_l = [ _ for _ in serverlist if _ != '아즈샤라' and _ != '하이잘']
    #log.info(etc_l)
    '''
        아즈샤라:   18분
        하이잘:     13분
        헬스크림:   7분
        말퓨리온:   5분
        가로나:     4분
        굴단:       3분
        줄진:       3분
        노르간논:   4분
        달라란:     3분
        듀로탄:     3분
        데스윙:     4분
        렉사르:     3분
        불타는 군단: 3분
        세나리우스: 3분
        스톰레이지: 4분
        윈드러너:   3분
        와일드해머: 3분
        알렉스트라자:4분
        '''

    # 변경된 api에 대응합니다
    # 토큰을 가져옵니다
    tok = await get_oauth()

    # realm 들을 가져옵니다
    #l_servers_pair = await get_realm(tok)
    await get_realm(tok)



    # 아즈샤라, 하이잘은 매시간 탐색, 나머지 16개 서버는 세시간 단위로 나눠서탐색합니다

    r_list = [['아즈샤라', '하이잘', '헬스크림', '말퓨리온'],
                ['아즈샤라', '가로나','굴단', '줄진', '노르간논', '달라란', '듀로탄', '데스윙', '렉사르'], 
                ['아즈샤라', '불타는 군단', '세나리우스', '스톰레이지', '윈드러너'
                                        , '와일드해머', '알렉스트라자']]
    # 주기마다 반복합니다
    while True:
        for serverlist in r_list:
            loop = asyncio.get_event_loop()
            loop.create_task(timer_proc(engine, serverlist))
            await asyncio.sleep(intv)

async def timer_proc(engine, serverlist):
        for s_ in serverlist:
            #await db_update_from_server(engine, s_, defaultset)
            # 서버이름과 아이디모두를 튜플로 넘겨줍니다
            await db_update_from_server(engine, (s_,servers_dict[s_]), defaultset)

async def get_oauth():
    auth = aiohttp.BasicAuth(login=cli, password=pwd)
    print('OAuth 토큰을 요청합니다')
    log.info('OAuth 토큰을 요청합니다')
    async with aiohttp.ClientSession(auth=auth) as sess:
        async with sess.get(tok_url,params='grant_type=client_credentials') as resp:
            tok_load = json.loads(await resp.text())
            tok = tok_load['access_token']
    return tok

# 변경된 api에 대응하는 realm id를 가져오는 함수입니다
#https://kr.api.blizzard.com/data/wow/realm/index?namespace=dynamic-kr&locale=ko_KR&access_token=US4uLYR6CkMOk066Dv8om5O2P3oBRdm53m
async def get_realm(tok):
    url = f'https://kr.api.blizzard.com/data/wow/realm/index?namespace=dynamic-kr&locale=ko_KR&access_token={tok}'
    result = ''
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            #result = await resp.text()
            load = json.loads(await resp.text())
            #log.info(load['realms'])
            l = load['realms']
            for i in l:
                #log.info(i)
                servers_dict[i['name']] = i['id']

logging.basicConfig(filename='dbproc.log', level=logging.INFO, format='%(asctime)s-%(message)s')
loop = asyncio.get_event_loop()
loop.run_until_complete(main_proc(interval))
