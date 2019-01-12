import asyncio
import aiohttp
import json

import sqlalchemy as sa
from sqlalchemy.sql import and_, or_, not_
from aiopg.sa import create_engine

from db_tableinfo import *

cli = 'b934788e2cde4166acb93dcbf558040f'
pwd = 'nMA7eloEh2rHFEiRw9Xs5j0Li6ZaFA5A'
url = 'https://apac.battle.net/oauth/token'

'''
https://kr.api.blizzard.com/wow/item/152505?locale=ko_KR&access_token=USt2y7pxKKiJ1yLYDjshaEM2k71sXdbCp3
'''
'''
# item name을 저장한 테이블입니다
tbl_items = sa.Table('items', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255)),
        sa.Column('file_name', sa.String(255)))
        '''

async def main():
    auth = aiohttp.BasicAuth(login=cli, password=pwd)
    async with aiohttp.ClientSession(auth=auth) as sess:
    #async with aiohttp.ClientSession() as sess:
        #async with sess.post(url,data='grant_type=client_credentials',encoded=True) as resp:
        async with sess.get(url,params='grant_type=client_credentials') as resp:
            res = await resp.text()
            js = json.loads(res)
            tok = js['access_token']
            print(tok)
    id = 22790
    req_url = f'https://kr.api.blizzard.com/wow/item/{id}?locale=ko_KR&access_token={tok}'

    print(req_url)
    # requests를 비동기형 aiohttp 의 clientssion get 으로 대치합니다
    async with aiohttp.ClientSession() as sess:
        async with sess.get(req_url) as resp:
            r = await resp.text()
            print(r)
            #js = json.loads(await resp.text())
    #print(js)

    #print(js['name'])
    #일단 가져온 값중 이름만 취하기로 합니다
    # 데이터를 못가져오는 경우가 발생해 아래와 같은 루틴을 추가했습니다. 
    '''
    if js.get('status') is not None:
        if js['status'] == 'nok':
            return ''
    else:
        return js['name']
        '''
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            id_ = 25055
            async for tuple_ in conn.execute(tbl_items.select().where(tbl_items.c.id==id_)):
                await conn.execute(tuple_.update().values(icon_name='허허허'))



    return

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
