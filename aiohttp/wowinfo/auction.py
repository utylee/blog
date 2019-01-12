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
from sqlalchemy.sql import and_, or_, not_
from aiopg.sa import create_engine

from db_tableinfo import *


myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
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


#async def proc(server, item_list):
async def db_update_from_server(server):
    global tok
    # 임시 딕셔너리를 만듭니다. 전체 db를 아이템별로 처리합니다
    temp_dict = {}
    # DB에 접속해둡니다
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            #battle dev api 로서 api key를 사용해 일단 json 주소를 전송받습니다
            print('json주소를 받아옵니다')
            #url = 'https://kr.api.battle.net/wow/auction/data/{}?locale={}&apikey={}'.format(server, locale, myapi)

            #battlenet dev api 대변혁으로 로그인 방식이 바뀌었습니다 자칭 OAuth 방식
            cli = 'b934788e2cde4166acb93dcbf558040f'
            pwd = 'nMA7eloEh2rHFEiRw9Xs5j0Li6ZaFA5A'
            tok_url = 'https://apac.battle.net/oauth/token'  #apac = kr, tw
            domain = 'kr.api.blizzard.com'
            locale = 'ko_KR'
            auth = aiohttp.BasicAuth(login=cli, password=pwd)
            #먼저 토큰을 요청합니다
            print('OAuth 토큰을 요청합니다')
            async with aiohttp.ClientSession(auth=auth) as sess:
                async with sess.get(tok_url,params='grant_type=client_credentials') as resp:
                    tok_load = json.loads(await resp.text())
                    tok = tok_load['access_token']
            '''
            https://us.api.blizzard.com/wow/auction/data/medivh?locale=en_US&access_token=USt2y7pxKKiJ1yLYDjshaEM2k71sXdbCp3
            '''
            req_url = f'https://{domain}/wow/auction/data/{server}?locale={locale}&access_token={tok}' 
            print(req_url)

            # .loads 함수인 것을 봅니다. s가 없는 load 함수는 파일포인터를 받더군요
            # requests가 아닌 aiohttp.ClientSession get 을 사용한 비동기방식으로 변경합니다
            start_time = time.time()
            dump_ts = 0             # 블리자드서버 경매데이터 덤프 시각 timestamp
            dump_ts_str = ''        # 블리자드서버 경매데이터 덤프 시각 timestamp 스트링

            # ssl 체크에서 에러가 나서 ssl 체크를 빼주는 옵션을 찾아서 넣어주었습니다
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as sess:
            #async with aiohttp.ClientSession() as sess:
                async with sess.get(req_url) as resp:
                    print(await resp.text())
                    load = json.loads(await resp.text())
                    js_url = load['files'][0]['url']
                    dump_ts = round(int(load['files'][0]['lastModified']) / 1000)
                    #str_now = datetime.datetime.fromtimestamp(ts).strftime('%H:%M-%m/%d/%y')
                    dump_ts_str = datetime.datetime.fromtimestamp(dump_ts).strftime('%H:%M-%m/%d/%y')
                    print(f'덤프시각:{dump_ts}, {dump_ts_str}')
                async with sess.get(js_url) as resp:
                    print('주소:{} \n로부터 json 덤프 파일을 다운로드합니다...\n'.format(js_url))
                    async with aiofiles.open(f'auction-{server}.json', 'wb') as f:
                        await f.write(await resp.read())
            # 덤프 시각을 db에 기록합니다
            #str_now = datetime.datetime.now().strftime('%H:%M-%m/%d/%y')
            print(f'dumped_time:{dump_ts_str}')
            await conn.execute(tbl_wow_server_info.update().where(tbl_wow_server_info.c.server==server).values
                                        (dumped_time=dump_ts_str))

            end_time = time.time()
            elapsed_time = round(end_time - start_time)
            # 가격 삽입시 30분 단위로 몇 번 지났는지 확인하기 위한 변수
            #elapsed_quot_for_chain = round((dump_ts - start_time) / 1800)
            # 받아온 json에 옥션 json 파일의 주소를 포함한 리스폰스를 보내줍니다. 
            print('.다운로드 완료!')
            print(f'다운로드에 총 {elapsed_time}초 소요')
            #print(f'서버 덤프시각에 비해 [30분단위]{elapsed_quot_for_chain}회가 경과하였습니다({dump_ts_str})')
            print('.파싱을 시작합니다')
            async with aiofiles.open(f'auction-{server}.json', 'r') as f:
                js = json.loads(await f.read())
            #print(js['auctions'])

            target_item_name = "하늘 골렘"
            #target_item_name = "얼어붙은 보주"
            #target_item_name = "호화로운 모피"
            #target_item_name = "묘지기의 투구"
            #target_item_name = "강봉오리"
            #target_item_name = "해안 마나 물약"
            #target_item_name = "파멸의 증오"
            #target_item_name = "야만의 피"
            target_item_name = "사술매듭 가방"
            #target_item_name = "심해 가방"
            #target_item_name = "영웅의 얼어붙은 무구"
            #target_item_name = "폭풍 은 광석"
            #target_item_name = "살아있는 강철"
            #target_item_name = "황천의 근원"
            #target_item_name = "드레나이 가루"
            #target_item_name = "폭풍 은 광석"
            #target_item_name = "진철주괴"
            #target_item_name = "유령무쇠 주괴"

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
            print('총 {} 개의 경매 아이템이 등록되어있습니다'.format(total))
            result_dict_set = defaultdict(dict)

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
                    temp_dict[cur] = {'item_name': temp_name, 'num': int(l['quantity']), 'min': price, 'min_seller': l['owner']}
                    temp_dict[cur] = {'item_name': temp_name, 'num': int(l['quantity']), 'min': price, 'min_seller': l['owner'], 'image': temp_image}
                # 해당아이템 딕트가 이미 존재할 경우
                else:
                    temp_dict[cur]['num'] = temp_dict[cur]['num'] + l['quantity']
                    temp_dict[cur]['num'] = temp_dict[cur]['num'] + l['quantity']

                    if (int(temp_dict[cur]['min']) == 0) or (price < temp_dict[cur]['min']):
                        temp_dict[cur]['min'] = price
                        temp_dict[cur]['min_seller'] = l['owner']

                # 내가 경매에 부친 물건이 있는지 표시합니다
            #print(temp_dict)
            ## 각 item 반복작업 종료



            # arranged_auction db에 삽입 프로세스 by 만들어진 temp_dict를 통해
            #
            #
            now__ = datetime.datetime.now().strftime('%H:%M-%m/%d/%y')
            print(f'\n## {now__} : 이제 {server} db에 정리한 데이터를 삽입하기 시작합니다')
            #print(temp_dict.keys())
            start_time = time.time()

            for id_ in temp_dict.keys():
                found = 0
                dict_ = temp_dict[id_]
                str_chain = ''
                
                async for r in conn.execute(tbl_arranged_auction.select().where(and_((tbl_arranged_auction.c.server==server),(tbl_arranged_auction.c.item==id_)))):
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

                    await conn.execute(tbl_arranged_auction.insert().values(server=server,
                                                        item=id_,
                                                        num=dict_['num'],
                                                        min=dict_['min'],
                                                        min_seller=dict_['min_seller'],
                                                        min_chain=str_chain,
                                                        edited_time=dump_ts_str,
                                                        edited_timestamp=dump_ts,
                                                        image=dict_['image']))
                # 해당 튜플이 있을 경우
                else:
                    do_ = 0       # 튜플 업데이트 여부를 결정합니다.시간이 30분 이내면 삽입하지 않습니다
                    # str_chain 을 가져온 후 새 가격을 추가해줍니다
                    async for sel_ in conn.execute(tbl_arranged_auction.select().where(
                            and_((tbl_arranged_auction.c.server==server),(tbl_arranged_auction.c.item==id_)))):
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
                            print('!!! 가격 chain 개수가 맞지 않습니다. --> id: {}, {} 개'.format(id_,len(l_chain)))
                            print('!!!  마지막 5개 값:{}'.format(l_chain[-5:]))
                            print('!!!  (잠재적위험) 자동수정1440개로 조정합니다')
                            l_chain = l_chain[l_chain_len - 1440:]
                        # 텀이 길어 빈 30분횟수가 있을 경우
                        if (q_ > 0):
                            last_cell = l_chain[-1]
                            # 30분 경과 횟수만큼 반복하여 마지막 값을 추가합니다
                            for _ in range(0, q_):
                                l_chain.append(last_cell)
                            str_chain = '?'.join(l_chain[q_+1:]) + '?' + str(dict_['min'])
                            do_ = 1
                        # 텀이 30분일 경우 (round 반올림이라 15분(0.5)부터 45분(1.4)까지가 여기에 해당될듯)
                        elif q_ == 0:
                            str_chain = str_chain.split('?', 1)[1] + '?' + str(dict_['min'])
                            do_ = 1
                    # 30분 이내일 경우는 insert를 패스합니다
                    if do_ == 0:
                        continue

                    await conn.execute(tbl_arranged_auction.update().where(and_((tbl_arranged_auction.c.server==server),(tbl_arranged_auction.c.item==id_))).values(num=dict_['num'],
                                                        min=dict_['min'],
                                                        min_seller=dict_['min_seller'],
                                                        min_chain=str_chain,
                                                        edited_time=dump_ts_str,
                                                        edited_timestamp=dump_ts,
                                                        image=dict_['image']))

        #return await deco_dictset(result_dict_set)
        end_time = time.time()
        elapsed_time = math.floor(end_time - start_time)
        elapsed_min = 0
        if(elapsed_time > 60):
            elapsed_min = round(elapsed_time / 60)
        elapsed_time = round(end_time - start_time)
        print(f'서버 {server}에 대한 삽입 정리 프로세스 종료')
        print(f'총 {elapsed_time} 초({elapsed_min}분)가 소요되었습니다')
        
        return 


# battle dev 로부터 아이템을 가져옵니다
async def get_item(id):
    global tok
    #print(f'토큰:{tok}')
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

# 로컬 db에서 이름을 통해 id를 가져옵니다
async def get_item_id(conn, name):
    id = 0
    result = 0
    async for r in conn.execute(tbl_items.select().where(tbl_items.c.name==name)):
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
    async for r in conn.execute(tbl_items.select().where(tbl_items.c.id==item_id)):
        #if len(r[2]) == 0:
        if (r[2] is None) or (len(r[2]) == 0):
            print(f'item no.{item_id}의 이름은 찾았으나 icon_name은 비어있습니다')
            name = r[1]
            result = 1  # icon_name만 없는 경우
        else :
            name, icon_name = r[1], r[2]
            result = 2  # 모두 있는 경우
    #해당 아이템이 로컬 테이블에 없다면 받아온 후 로컬 테이블에 저정합니다
    if result == 0:
        print(f'### item no. {item_id} 이 로컬에 없기에 battlenet dev를 통해 가져옵니다...')
        name, icon_name = await get_item(item_id)
        print(f'name: {name}, icon_name: {icon_name}')
        await conn.execute(tbl_items.insert().values(id=int(item_id), name=name, icon_name=icon_name))
    elif result == 1:
        print(f'### item no. {item_id} 의 icon_name은 비어있기에 battlenetdev를 통해 icon_name만 가져옵니다...')
        name, icon_name = await get_item(item_id)
        print(f'name: {name}, icon_name: {icon_name}')
        await conn.execute(tbl_items.update().where(tbl_items.c.id==int(item_id)).values(icon_name=icon_name))

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
    async for r in conn.execute(tbl_item_set.select().where(tbl_item_set.c.set_name==setname)) :
        itemlist = r[1].split(',')

    print(itemlist)
    return itemlist

async def get_decoed_item_set(server, setname):
    dict_ = {}
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            itemlist = await get_item_set(conn, setname)
            for name_ in itemlist:
                id_ = await get_item_id(conn, name_) 
                image_path = ''
                #async for image_ in conn.execute(tbl_images.select([tbl_images.c.file_name]).where(tbl_images.c.item_name==name_)):
                '''
                async for image_ in conn.execute(tbl_images.select().where(tbl_images.c.item_name==name_)):
                    image_path = image_[1]
                    '''
                async for it_ in conn.execute(tbl_items.select().where(tbl_items.c.id==id_)):
                    img_url = it_[2]
                    #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{img_}.jpg'
                async for tuple_ in conn.execute(tbl_arranged_auction.select().where(and_((tbl_arranged_auction.c.item==id_),(tbl_arranged_auction.c.server==server)))):
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
