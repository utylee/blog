from auction import *
import logging

interval = 1800 #초
tok = ''
defaultset = '기본구성'
locale = 'ko_KR'
myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
cli = 'b934788e2cde4166acb93dcbf558040f'
pwd = 'nMA7eloEh2rHFEiRw9Xs5j0Li6ZaFA5A'
tok_url = 'https://apac.battle.net/oauth/token'  #apac = kr, tw

async def main_proc(intv):
    # 한국 와우 서버 리스트를 가져옵니다
    serverlist = []
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            async for r in conn.execute(db.tbl_wow_server_info.select()):
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

logging.basicConfig(filename='dbproc.log', level=logging.INFO, format='%(asctime)s-%(message)s')
loop = asyncio.get_event_loop()
loop.run_until_complete(main_proc(interval))
