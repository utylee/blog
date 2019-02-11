import sys
import asyncio
#import requests        # 비동기 방식인 aiohttp.ClientSession().get()으로 바꾸기로 합니다
import aiohttp
import aiofiles
import json
import pycurl
from collections import defaultdict
import math
import datetime
import time

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.sql import and_, or_, not_
from aiopg.sa import create_engine

import db_tableinfo as db
import auction_classes as a_cl
import logging

# db_proc에서 사용되느냐 wowinfo에서 사용되느냐에 따라 log 설정을 바뀌되록 합니다
if(sys.argv[0][-10:] == 'db_proc.py'):
    log = logging.getLogger('dbproc')
elif(sys.argv[0][-14:] == 'test_master.py'):
    from test_master import log_path
    log = logging.getLogger(log_path)
else:
    from test import log_path
    log = logging.getLogger(log_path)

'''
https://kr.api.blizzard.com/wow/item/152505?locale=ko_KR&access_token=USt2y7pxKKiJ1yLYDjshaEM2k71sXdbCp3
https://wow.zamimg.com/images/wow/icons/large/inv_misc_herb_riverbud.jpg
http://media.blizzard.com/wow/icons/{18:36:56}/inv_misc_herb_riverbud.jpg
'''
#server = '아즈샤라'
locale = 'ko_KR'
name_list = ['부자인생', '부자인셍', '부쟈인생', '부쟈인섕','부자인솅','부자인생의소환수','부자인셈']
my_item = []
tok = ''
myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
cli = 'b934788e2cde4166acb93dcbf558040f'
pwd = 'nMA7eloEh2rHFEiRw9Xs5j0Li6ZaFA5A'
tok_url = 'https://apac.battle.net/oauth/token'  #apac = kr, tw

async def get_oauth():
    auth = aiohttp.BasicAuth(login=cli, password=pwd)
    print('OAuth 토큰을 요청합니다')
    log.info('OAuth 토큰을 요청합니다')
    async with aiohttp.ClientSession(auth=auth) as sess:
        async with sess.get(tok_url,params='grant_type=client_credentials') as resp:
            tok_load = json.loads(await resp.text())
            tok = tok_load['access_token']
    return tok

async def get_wowtoken(tok):
    wowtok_req_url = f'https://kr.api.blizzard.com/data/wow/token/index?namespace=dynamic-kr&locale={locale}&access_token={tok}'

    async with aiohttp.ClientSession() as sess:
        async with sess.get(wowtok_req_url) as resp:
            #print(await resp.text())
            load = json.loads(await resp.text())
            price = load['price']
    return price

#async def proc(server, item_list):
async def db_update_from_server(engine, server, defaultset):
    global tok
    # 임시 딕셔너리를 만듭니다. 전체 db를 아이템별로 처리합니다
    temp_dict = {}
    # DB에 접속해둡니다
    async with engine.acquire() as conn:
        #battle dev api 로서 api key를 사용해 일단 json 주소를 전송받습니다
        print('json주소를 받아옵니다')
        log.info('json주소를 받아옵니다')
        #url = 'https://kr.api.battle.net/wow/auction/data/{}?locale={}&apikey={}'.format(server, locale, myapi)

        #battlenet dev api 대변혁으로 로그인 방식이 바뀌었습니다 자칭 OAuth 방식
        domain = 'kr.api.blizzard.com'
        #먼저 토큰을 요청합니다
        tok = await get_oauth()
        '''
        https://us.api.blizzard.com/wow/auction/data/medivh?locale=en_US&access_token=USt2y7pxKKiJ1yLYDjshaEM2k71sXdbCp3
        '''
        req_url = f'https://{domain}/wow/auction/data/{server}?locale={locale}&access_token={tok}' 
        print(req_url)
        log.info(req_url)

        # .loads 함수인 것을 봅니다. s가 없는 load 함수는 파일포인터를 받더군요
        # requests가 아닌 aiohttp.ClientSession get 을 사용한 비동기방식으로 변경합니다
        start_time = time.time()
        dump_ts = 0             # 블리자드서버 경매데이터 덤프 시각 timestamp
        dump_ts_str = ''        # 블리자드서버 경매데이터 덤프 시각 timestamp 스트링

        # 와우토큰 
        wowtoken_price = await get_wowtoken(tok)
        print(f'토큰가격:{wowtoken_price}')
        log.info(f'토큰가격:{wowtoken_price}')

        # ssl 체크에서 에러가 나서 ssl 체크를 빼주는 옵션을 찾아서 넣어주었습니다
        #async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as sess:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(req_url) as resp:
                #print(await resp.text())
                load = json.loads(await resp.text())
                js_url = load['files'][0]['url']
                dump_ts = round(int(load['files'][0]['lastModified']) / 1000)
                #str_now = datetime.datetime.fromtimestamp(ts).strftime('%H:%M-%m/%d/%y')
                dump_ts_str = datetime.datetime.fromtimestamp(dump_ts).strftime('%H:%M-%m/%d/%y')
                print(f'덤프시각:{dump_ts}, {dump_ts_str}')
                log.info(f'덤프시각:{dump_ts}, {dump_ts_str}')
            async with sess.get(js_url) as resp:
                print('주소:{} \n로부터 json 덤프 파일을 다운로드합니다...\n'.format(js_url))
                log.info('주소:{} \n로부터 json 덤프 파일을 다운로드합니다...\n'.format(js_url))
                async with aiofiles.open(f'auction-{server}.json', 'wb') as f:
                    await f.write(await resp.read())
        # 덤프 시각을 db에 기록합니다
        #str_now = datetime.datetime.now().strftime('%H:%M-%m/%d/%y')
        print(f'dumped_time:{dump_ts_str}')
        log.info(f'dumped_time:{dump_ts_str}')
        await conn.execute(db.tbl_wow_server_info.update().where(db.tbl_wow_server_info.c.server==server).values
                                    (dumped_time=dump_ts_str))

        end_time = time.time()
        elapsed_time = round(end_time - start_time)
        # 가격 삽입시 30분 단위로 몇 번 지났는지 확인하기 위한 변수
        #elapsed_quot_for_chain = round((dump_ts - start_time) / 1800)
        # 받아온 json에 옥션 json 파일의 주소를 포함한 리스폰스를 보내줍니다. 
        print('.다운로드 완료!')
        log.info('.다운로드 완료!')
        print(f'다운로드에 총 {elapsed_time}초 소요')
        log.info(f'다운로드에 총 {elapsed_time}초 소요')
        #print(f'서버 덤프시각에 비해 [30분단위]{elapsed_quot_for_chain}회가 경과하였습니다({dump_ts_str})')
        print('.파싱을 시작합니다')
        log.info('.파싱을 시작합니다')
        async with aiofiles.open(f'auction-{server}.json', 'r') as f:
            js = json.loads(await f.read())
        #print(js['auctions'])

        target_item_name = "하늘 골렘"
        # 저장된 파일을 읽은 후 한줄씩 탐색합니다
        sellers = []
        min_seller = ''
        i = 0
        price = 0
        min = 0
        max = 0
        avg = 0
        sum = 0


        total = len(js['auctions'])
        print('-- 총 {} 개의 경매 아이템이 등록되어있습니다'.format(total))
        log.info('-- 총 {} 개의 경매 아이템이 등록되어있습니다'.format(total))
        # wow token 가격도 추가로 마지막에 넣어줍니다
        js['auctions'].append({'item': 999999, 'buyout': wowtoken_price, 'quantity': 1, 'owner': 'BLIZZARD Ent.'})

        start_a = time.time()
        for l in js['auctions']:
            num = 0
            cur = int(l['item'])
            price = 0
            if l['buyout'] == 0:
                price = int(l['bid'] / int(l['quantity']))
            else:
                price = int(l['buyout'] / int(l['quantity'])) # 묶음 가격을 감안하지 못해서 추가합니다

            # 해당아이템에 대한 딕트-리스트가 존재하지 않을경우
            if temp_dict.get(cur) is None:
                # 굳이 이름은 arranged table 에 넣지 않기에 (id만) 굳이 가져오는 
                #       프로세스로 인한 시간 낭비를방지합니다
                # !!라고 생각했으나 이 프로세스를 행하지 않으면 item존재를 로컬 db상 존재유무를 알수
                #   없습니다. 속도도 해당아이템 최초의 경우에만 가져오고 속도도 빨라서 큰 영향
                #   없다고 생각됩니다.
                #temp_name = ''
                res_ = await get_item_name_and_icon(conn, cur)
                temp_name, temp_image = res_

                #print(temp_name)
                #temp_dict[cur] = {'item_name': temp_name, 'num': int(l['quantity']), 'min': price, 'min_seller': l['owner']}
                temp_dict[cur] = {'item_name': temp_name, 'num': int(l['quantity']), 'min': price, 'min_seller': l['owner'], 'image': temp_image}
            # 해당아이템 딕트가 이미 존재할 경우
            else:
                temp_dict[cur]['num'] = temp_dict[cur]['num'] + l['quantity']
                temp_dict[cur]['num'] = temp_dict[cur]['num'] + l['quantity']

                if (int(temp_dict[cur]['min']) == 0) or (price < temp_dict[cur]['min']):
                    temp_dict[cur]['min'] = price
                    temp_dict[cur]['min_seller'] = l['owner']
            # sleep을 줘서 점유를 풀어줍니다
            # 0.05 이상의 값을 줄 경우 어떤 경우에 있으서 transport 에러 워닝이 뜹니다.
            # sleep을 0으로 하라는 말도 있는데 그렇게 하니 오히려 행이 좀 걸리는 것 같습니다.
            # 관련 정보 링크https://github.com/aio-libs/aiohttp/issues/1115
            #await asyncio.sleep(0.01)

            # 내가 경매에 부친 물건이 있는지 표시합니다
        #print(temp_dict)
        ## 각 item 반복작업 종료
        
        end_a = time.time()
        elap_a = round(end_a - start_a, 2)
        elap_a_min = round(elap_a / 60)
        print(f'JSON 파싱 소요시간: {elap_a} 초({elap_a_min}분)')
        log.info(f'JSON 파싱 소요시간: {elap_a} 초({elap_a_min}분)')


        # arranged_auction db에 삽입 프로세스 by 만들어진 temp_dict를 통해...
        #
        #
        now__ = datetime.datetime.now().strftime('%H:%M-%m/%d/%y')
        print(f'\n## {now__} : 이제 {server} db에 정리한 데이터를 삽입하기 시작합니다')
        log.info(f'\n## {now__} : 이제 {server} db에 정리한 데이터를 삽입하기 시작합니다')
        #print(temp_dict.keys())
        start_time = time.time()

        for id_ in temp_dict.keys():
            found = 0
            dict_ = temp_dict[id_]
            str_chain = ''
            
            #async for r in conn.execute(tbl_arranged_auction.select().where(and_((tbl_arranged_auction.c.server==server),(tbl_arranged_auction.c.item==id_)))):
            async for r in conn.execute(select([db.tbl_arranged_auction.c.item]).where(and_((db.tbl_arranged_auction.c.server==server),(db.tbl_arranged_auction.c.item==id_)))):
                #print(r)
                found = 1

            ##temp_dict[cur] = {'item_name': temp_name, 'num': int(l['quantity']), 'min': price, 'min_seller': l['owner']}
            # arranged auction에 없다면 초기 튜플을 삽입합니다
            if found == 0:
                #print('no found')

                # min_chain 초기스트링만들기
                # 30분씩 하루 48 데이터, 그것을 30배(한달치) 한 1440개의 데이터를 보관하기로 합니다
                #1439개의 0을 ?로 구분하고 마지막은 현재 최저가 min을 넣어놓습니다
                for i_ in range(0, 1439):
                    str_chain = str_chain + '0?'
                str_chain = str_chain + str(dict_['min'])

                await conn.execute(db.tbl_arranged_auction.insert().values(server=server,
                                                    item=id_,
                                                    num=dict_['num'],
                                                    min=dict_['min'],
                                                    min_seller=dict_['min_seller'],
                                                    min_chain=str_chain,
                                                    edited_time=dump_ts_str,
                                                    edited_timestamp=dump_ts,
                                                    image=dict_['image'],
                                                    fame=0))
            # 해당 튜플이 있을 경우
            else:
                do_ = 0       # 튜플 업데이트 여부를 결정합니다.시간이 30분 이내면 삽입하지 않습니다
                # str_chain 을 가져온 후 새 가격을 추가해줍니다
                async for sel_ in conn.execute(db.tbl_arranged_auction.select().where(
                        and_((db.tbl_arranged_auction.c.server==server),(db.tbl_arranged_auction.c.item==id_)))):
                    last_timestamp = sel_[7]
                    cur_timestamp = round(time.time())
                    q_ = 0
                    if(last_timestamp is not None):
                        q_ = round((cur_timestamp - last_timestamp) / 1800) - 1 #반올림
                    #print(f'q_: {q_}')
                    str_chain = sel_[5]
                    l_chain = str_chain.split('?')
                    l_chain_len = len(l_chain)
                    if(l_chain_len != 1440):
                        print('!!! 가격 chain 개수가 맞지 않습니다. --> id: {}, {} 개'.format(id_,l_chain_len))
                        print('!!!  마지막 5개 값:{}'.format(l_chain[-5:]))
                        print('!!!  (잠재적위험) 자동수정1440개로 조정합니다')
                        log.info('!!! 가격 chain 개수가 맞지 않습니다. --> id: {}, {} 개'.format(id_,l_chain_len))
                        log.info('!!!  마지막 5개 값:{}'.format(l_chain[-5:]))
                        log.info('!!!  (잠재적위험) 자동수정1440개로 조정합니다')
                        l_chain = l_chain[l_chain_len - 1440:]
                        str_chain = '?'.join(l_chain)
                        do_ = 2
                    # 텀이 길어 빈 30분횟수가 있을 경우
                    if (q_ > 0):
                        last_cell = l_chain[-1]
                        # 30분 경과 횟수만큼 반복하여 마지막 값을 추가합니다
                        for _ in range(0, q_):
                            l_chain.append(last_cell)
                        str_chain = '?'.join(l_chain[q_+1:]) + '?' + str(dict_['min'])
                        if(do_ == 2):
                            size_ = len(str_chain.split('?'))
                            print(f'수정후 사이즈:{size_}')
                            log.info(f'수정후 사이즈:{size_}')
                        do_ = 1
                    # 텀이 30분일 경우 (round 반올림이라 15분(0.5)부터 45분(1.4)까지가 여기에 해당될듯)
                    elif q_ == 0:
                        str_chain = str_chain.split('?', 1)[1] + '?' + str(dict_['min'])
                        if(do_ == 2):
                            size_ = len(str_chain.split('?'))
                            print(f'수정후 사이즈:{size_}')
                            log.info(f'수정후 사이즈:{size_}')
                        do_ = 1
                # 30분 이내일 경우는 insert를 패스합니다. 개수 조정이 필요할 경우에는 인서트합니다
                if do_ == 0:
                    continue

                await conn.execute(db.tbl_arranged_auction.update().where(and_((db.tbl_arranged_auction.c.server==server),(db.tbl_arranged_auction.c.item==id_))).values(num=dict_['num'],
                                                    min=dict_['min'],
                                                    min_seller=dict_['min_seller'],
                                                    min_chain=str_chain,
                                                    edited_time=dump_ts_str,
                                                    edited_timestamp=dump_ts,
                                                    image=dict_['image']))
            #top_six = await worldcup_six(conn)
    

        #인기 탑5를 선별합니다
        top_six = {}
        top_six = await worldcup_six(conn, server)
        #5개만 취해서 기본구성 set를 업데이트합니다
        # loop 내에서 y를 통한 dict 아이템 찾을 시 다시 해싱을 하므로 좀 변경해봤습니다
        for k, v in top_six.items():
            #top_six[k] = str(k) + '?' + str(top_six[k])
            top_six[k] = str(k) + '?' + str(v)  # top_six[k]는 v로 바꾸면 변수 변경은 안되더군여
        top_six.pop(6)        #마지막 아이템을 제거합니다
        top_six[0] = "0?WoW 토큰"
        top_six_str = ','.join(top_six.values())
        print(f'top_six string: {top_six_str}')
        log.info(f'top_six string: {top_six_str}')

        #기본구성 db에 삽입해줍니다
        await conn.execute(db.tbl_item_set.update().where(db.tbl_item_set.c.set_name==defaultset)
                            .values(itemname_list=top_six_str))

        end_time = time.time()
        elapsed_time = math.floor(end_time - start_time)
        elapsed_min = 0
        if(elapsed_time > 60):
            elapsed_min = round(elapsed_time / 60)
        elapsed_time = round(end_time - start_time)
        print(f'서버 {server}에 대한 삽입 정리 프로세스 종료')
        print(f'총 {elapsed_time} 초({elapsed_min}분)가 소요되었습니다')
        log.info(f'서버 {server}에 대한 삽입 정리 프로세스 종료')
        log.info(f'총 {elapsed_time} 초({elapsed_min}분)가 소요되었습니다')
        
        return 

async def worldcup_six(conn, server):       # server는 받습니다만 실제로 아즈샤라 서버 인기도
    ret_dict = {}
    ind = 1         # 0번은 후에 WoW 토큰을 위해 남겨두고 1부터 시작합니다
    async for result in conn.execute(
            select([db.tbl_arranged_auction.c.item, db.tbl_arranged_auction.c.fame])
            .order_by(sa.desc(db.tbl_arranged_auction.c.fame)).limit(6)
            .where(db.tbl_arranged_auction.c.server=='아즈샤라')):
        ret_dict[ind] = await get_item_name(conn, result[0])
        ind += 1
    #print(ret_dict)
    return ret_dict

# battle dev 로부터 아이템을 가져옵니다
async def get_item(id):
    global tok
    #print(f'토큰:{tok}')
    if(id == 999999):   #WoW 토큰
        return ['WoW 토큰', 'wow_token01']
    item_req_url = f'https://kr.api.blizzard.com/wow/item/{id}?locale=ko_KR&access_token={tok}'
    # requests를 비동기형 aiohttp 의 clientssion get 으로 대치합니다
    async with aiohttp.ClientSession() as sess:
        #async with sess.get('https://kr.api.battle.net/wow/item/{}?locale={}&apikey={}'.format(id, locale, myapi)) as resp:
        async with sess.get(item_req_url) as resp:
            js = json.loads(await resp.text())

    #print(js['name'])
    # 데이터를 못가져오는 경우가 발생해 아래와 같은 루틴을 추가했습니다. 
    if js.get('status') is not None:
        if js['status'] == 'nok':
            return ['', '']
    else:
        try:
            return [js['name'], js['icon']]
        # 에러날 경우 그냥 널을 리턴해줘봅니다
        except:
            return ['', '']
  
# 로컬 db에서 id를 통해 이름을 가져옵니다
async def get_item_name(conn, id):
    name = ''
    result = 0
    #async for r in conn.execute(tbl_items.select().where(tbl_items.c.name==name)):
        #id = r[0]
    async for r in conn.execute(select([db.tbl_items.c.name]).where(db.tbl_items.c.id==id)):
        name = r[0]
        result = 1
    return name 

# 로컬 db에서 이름을 통해 id를 가져옵니다
async def get_item_id(conn, name):
    id = 0
    result = 0
    #async for r in conn.execute(tbl_items.select().where(tbl_items.c.name==name)):
        #id = r[0]
    async for r in conn.execute(select([db.tbl_items.c.id]).where(db.tbl_items.c.name==name)):
        id = r[0]
        result = 1
        '''
    #해당 아이템이 로컬 테이블에 없다면 받아온 후 로컬 테이블에 저정합니다
    if result == 0:
        print(f'### item {name} 이 로컬에 없기에 battlenet dev를 통해 이름을 가져옵니다...')
        name = await get_item(item_id)
        icon_name = 
        print(name)
        await conn.execute(tbl_items.insert().values(id=int(item_id), name=name))
        '''
    return id 

# 로컬 db에서 id를 통해 이름를 가져옵니다
async def get_item_name_and_icon(conn, item_id):
    result = 0          # 아무것도 없는 경우
    name = ''
    icon_name = ''
    async for r in conn.execute(db.tbl_items.select().where(db.tbl_items.c.id==item_id)):
        #if len(r[2]) == 0:
        if (r[2] is None) or (len(r[2]) == 0):
            print(f'item no.{item_id}의 이름은 찾았으나 icon_name은 비어있습니다')
            log.info(f'item no.{item_id}의 이름은 찾았으나 icon_name은 비어있습니다')
            name = r[1]
            result = 1  # icon_name만 없는 경우
        else :
            name, icon_name = r[1], r[2]
            result = 2  # 모두 있는 경우
    #해당 아이템이 로컬 테이블에 없다면 받아온 후 로컬 테이블에 저정합니다
    if result == 0:
        print(f'### item no. {item_id} 이 로컬에 없기에 battlenet dev를 통해 가져옵니다...')
        log.info(f'### item no. {item_id} 이 로컬에 없기에 battlenet dev를 통해 가져옵니다...')
        name, icon_name = await get_item(item_id)
        print(f'name: {name}, icon_name: {icon_name}')
        log.info(f'name: {name}, icon_name: {icon_name}')
        await conn.execute(db.tbl_items.insert().values(id=int(item_id), name=name, icon_name=icon_name))
    elif result == 1:
        print(f'### item no. {item_id} 의 icon_name은 비어있기에 battlenetdev를 통해 icon_name만 가져옵니다...')
        log.info(f'### item no. {item_id} 의 icon_name은 비어있기에 battlenetdev를 통해 icon_name만 가져옵니다...')
        name, icon_name = await get_item(item_id)
        print(f'name: {name}, icon_name: {icon_name}')
        log.info(f'name: {name}, icon_name: {icon_name}')
        await conn.execute(db.tbl_items.update().where(db.tbl_items.c.id==int(item_id)).values(icon_name=icon_name))

    return name, icon_name

'''
# item에 대응하는 이미지 파일명을 가져오고 가격을 단위로 분리합니다 db가 다릅니다 wowinfo db에 이미
async def deco_dictset(data):
    # db접속 한번에 다 처리합니다. 접속으로인한 딜레이를 제거하기 위함입니다. 실제로 영향이 클지는 모르겠지만
    async with create_engine(user='postgres',
                            database='wowinfo',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            # 이미지 파일명을 대입합니다
            for a in data.keys():
                async for r in conn.execute(tbl_images.select().where(tbl_images.c.item_name==a)):
                    data[a]['image'] = r[1]
                    print('------\n{}\n{}'.format(a, data))

                # 골드,실버,카퍼 를 분리해줍니다
                price = int(data[a]['min'])

                if price < 10000:
                    data[a]['gold'] = 0
                else:
                    data[a]['gold'] = math.floor(price / 10000)

                price = price - data[a]['gold'] * 10000
                if price < 100:
                    data[a]['silver'] = 0
                else:
                    data[a]['silver'] = math.floor(price / 100)

                data[a]['copper'] = price - data[a]['silver'] * 100

    return data
'''
async def get_item_set(conn, setname):
    itemlist = []

    #async for r in conn.execute(tbl_item_set.select(tbl_item_set.c.itemname_list).where(tbl_item_set.c.set_name==setname)) :
    print(f'setname:{setname}');
    log.info(f'setname:{setname}');
    async for r in conn.execute(db.tbl_item_set.select().where(db.tbl_item_set.c.set_name==setname)) :
        itemlist = r[1].split(',')

    print(itemlist)
    log.info(itemlist)
    return itemlist

async def get_decoed_item(engine, server, user_, itemset_, pos_, name_, fullstr=''):
    dict_ = {}
    fame = 0

    async with engine.acquire() as conn:
        id_ = await get_item_id(conn, name_) 
        image_path = ''
        async for it_ in conn.execute(db.tbl_items.select().where(db.tbl_items.c.id==id_)):
            img_url = it_[2]
            #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{img_}.jpg'
        async for tuple_ in conn.execute(db.tbl_arranged_auction.select().where(and_((db.tbl_arranged_auction.c.item==id_),(db.tbl_arranged_auction.c.server==server)))):
            #print('name_:{}'.format(name_))
            dict_['name'] = name_ 
            dict_['num'] = tuple_[2]
            #dict_['min'] = tuple_[3]
            dict_['min_seller'] = tuple_[4]
            dict_['min_chain'] = tuple_[5].split('?')
            #dict_['edited_time'] = tuple_[6]
            dict_['image'] = img_url
            #print(f'icon_name:{img_url}')
            fame = tuple_[9]
            if fame is None:
                fame = 0
            fame += 1

            # 골드,실버,카퍼 를 분리해줍니다
            price = int(tuple_[3])

            if price < 10000:
                dict_['gold'] = 0
            else:
                dict_['gold'] = math.floor(price / 10000)

            price = price - dict_['gold'] * 10000
            if price < 100:
                dict_['silver'] = 0
            else:
                dict_['silver'] = math.floor(price / 100)

            dict_['copper'] = price - dict_['silver'] * 100
        # fame 을 1 증가시켜줍니다
        # fame 증가시키는 프로세스를 별도 task로 실행시켜 multitasking을 구현합니다.
        # 사용자 응답시간이 많이 빨라집니다. 1회 업데이트에 0.1초씩 걸리더군요. rpi3b+에서..
        await increase_fame(engine, server, id_, fame)

        # 현재 itemset의 해당 아이템 칸 값을 새 아이템명으로 변경해줍니다
        # 별도의 task로 실행시켜 최대한 일단 사용자에게 반응을 먼저하도록 노력합니다
        # itemset이 입력되지 않은 경우(update_indiv가 아닌 rq_item 에서의 요청)는 itemset update를 생략합니다
        if(itemset_):
            log.info('itemset이 입력되어 수정해줍니다')
            set_ = a_cl.Set(itemset_).fork()
            await set_.update_itemset(engine, user_, itemset_, pos_, name_, fullstr)
    return dict_

async def increase_fame(engine, srv, id_, fame):
    loop = asyncio.get_event_loop()
    loop.create_task(increase_fame_(engine, srv, id_, fame))

async def increase_fame_(engine, srv, id_, fame):
    async with engine.acquire() as conn:
        await conn.execute(db.tbl_arranged_auction.update().where(and_((db.tbl_arranged_auction.c.item==id_),(db.tbl_arranged_auction.c.server==srv))).values(fame=fame))
    log.info(f'fame ++1({fame}) (id: {id_}, {name_})')


'''
async def update_itemset(engine, itemset_, pos_, name_, fullstr=''):
    async with engine.acquire() as conn:
        itemset_l = await get_item_set(conn, itemset_)
        # 해당아이템셋이 없을경우(다른 사용자가 삭제를 했다던지) 해당 아이템셋을 그대로 만들어줍니다
        b_create = 0
        if(len(itemset_l) == 0):
            b_create = 1
            itemset_l = fullstr.split(',')
        temp_l = []
        for _ in itemset_l:
            l_ = _.split('?')
            if l_[0] == pos_:
                l_[1] = name_
            temp_l.append('?'.join(l_))
        ret_str = ','.join(temp_l)
        print(f'indiv_update: ret_str: {ret_str}')
        log.info(f'indiv_update: ret_str: {ret_str}')

        if(not b_create):
            # itemset 테이블을 업데이트해줍니다
            await conn.execute(db.tbl_item_set.update().where(db.tbl_item_set.c.set_name==itemset_)
                                .values(itemname_list=ret_str))
        else: 
            # 해당 셋이 삭제되었으므로 itemset 을 그대로 만들어줍니다
            await conn.execute(db.tbl_item_set.insert().values(set_name=itemset_,
                                                    itemname_list=ret_str,
                                                    edited_time='',
                                                    user=user))

## deprecated, itemset동작은 auction_class에서 상속받아서 따로행합니다.
async def get_decoed_item_set(server, setname):
    dict_ = {}
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.212',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            itemlist = await get_item_set(conn, setname)
            for name_ in itemlist:
                id_ = await get_item_id(conn, name_) 
                image_path = ''
                #async for image_ in conn.execute(tbl_images.select([tbl_images.c.file_name]).where(tbl_images.c.item_name==name_)):
                async for it_ in conn.execute(db.tbl_items.select().where(db.tbl_items.c.id==id_)):
                    img_url = it_[2]
                    #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{img_}.jpg'
                async for tuple_ in conn.execute(db.tbl_arranged_auction.select().where(and_((db.tbl_arranged_auction.c.item==id_),(db.tbl_arranged_auction.c.server==server)))):
                    #print('name_:{}'.format(name_))
                    dict_[name_] = {}
                    dict_[name_]['num'] = tuple_[2]
                    dict_[name_]['min'] = tuple_[3]
                    dict_[name_]['min_seller'] = tuple_[4]
                    dict_[name_]['min_chain'] = tuple_[5].split('?')
                    #print(dict_[name_]['min_chain'])
                    dict_[name_]['edited_time'] = tuple_[6]
                    
                    #dict_[name_]['edited_timestamp'] = int(tuple_[7])#timestamp는 웹에서 사용할 일이 없으므로 빼고 반납합니다
                    #dict_[name_]['image'] = image_path
                    #img_ = tuple_[8]
                    #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{tuple_[8]}.jpg'
                    #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{img_}.jpg'
                    #dict_[name_]['image'] = tuple_[8]
                    dict_[name_]['image'] = img_url
                    #print(f'icon_name:{img_url}')

                    # 골드,실버,카퍼 를 분리해줍니다
                    price = int(tuple_[3])

                    if price < 10000:
                        dict_[name_]['gold'] = 0
                    else:
                        dict_[name_]['gold'] = math.floor(price / 10000)

                    price = price - dict_[name_]['gold'] * 10000
                    if price < 100:
                        dict_[name_]['silver'] = 0
                    else:
                        dict_[name_]['silver'] = math.floor(price / 100)

                    dict_[name_]['copper'] = price - dict_[name_]['silver'] * 100

    return dict_
'''

async def create_itemset(engine, user, setname, defaultuser, defaultset):
    success = 0
    dict_ = {}

    async with engine.acquire() as conn:
        found = 0
        async for r_ in conn.execute(db.tbl_item_set.select().where(and_((db.tbl_item_set.c.user==user),(db.tbl_item_set.c.set_name==setname)))):
            found += 1
        # 이미 있는 경우는 생성하지 않습니다
        if(found == 0):
            itemlist = await get_item_set(conn, defaultset)    # 초기로 '기본구성'리스트를 넣슴다
            itemstring = ','.join(itemlist)
            await conn.execute(db.tbl_item_set.insert().values(set_name=setname,
                                                    itemname_list=itemstring,
                                                    edited_time='',
                                                    user=user))
            success = 1
    return success

async def delete_itemset(engine, user, setname):
    success = 0
    dict_ = {}
    async with engine.acquire() as conn:
        await conn.execute(db.tbl_item_set.delete().where(and_((db.tbl_item_set.c.user==user),(db.tbl_item_set.c.set_name==setname))))
        success = 1
    return success


async def get_serverlist(engine):
    # 한국 와우 서버 리스트를 가져옵니다
    serverlist = []
    async with engine.acquire() as conn:
        async for r in conn.execute(db.tbl_wow_server_info.select()):
            serverlist.append(r[0])
    
    #serverlist = ['아즈샤라']
    log.info(f'serverlist = {serverlist}')
    return sorted(serverlist)
