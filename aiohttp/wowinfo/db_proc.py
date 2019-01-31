from auction import *
import logging
import logging.handlers
import pathlib

#interval = 1800 #초
interval = 5400 #초
tok = ''
defaultset = '기본구성'
locale = 'ko_KR'
myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
cli = 'b934788e2cde4166acb93dcbf558040f'
pwd = 'nMA7eloEh2rHFEiRw9Xs5j0Li6ZaFA5A'
tok_url = 'https://apac.battle.net/oauth/token'  #apac = kr, tw

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
    serverlist = await get_serverlist()
    '''
    # 한국 와우 서버 리스트를 가져옵니다
    serverlist = []
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.212',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(db.tbl_wow_server_info.select()):
                serverlist.append(r[0])

    # 제거해봅니다. 초기에 굳이 하지 않아도 handle(index.html)가 처리합니다
    #await fetch_auction()
    
    #serverlist = ['아즈샤라']
    log.info(f'serverlist = {serverlist}')
    '''
    # 주기마다 반복합니다
    while True:
        loop = asyncio.get_event_loop()
        loop.create_task(timer_proc(serverlist))
        await asyncio.sleep(intv)

async def timer_proc(serverlist):
    for s_ in serverlist:
        await db_update_from_server(s_, defaultset)

logging.basicConfig(filename='dbproc.log', level=logging.INFO, format='%(asctime)s-%(message)s')
loop = asyncio.get_event_loop()
loop.run_until_complete(main_proc(interval))
