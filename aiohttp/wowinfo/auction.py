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
#server = '아즈샤라'
locale = 'ko_KR'
name_list = ['부자인생', '부자인셍', '부쟈인생', '부쟈인섕','부자인솅','부자인생의소환수','부자인셈']
my_item = []


#async def proc(server, item_list):
async def db_update_from_server(server):
    # 임시 딕셔너리를 만듭니다. 전체 db를 아이템별로 처리합니다
    temp_dict = {}
    # DB에 접속해둡니다
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
        async with engine.acquire() as conn:
            #await conn.execute(tbl.insert().values(bid=4444))

            #battle dev api 로서 api key를 사용해 일단 json 주소를 전송받습니다
            url = 'https://kr.api.battle.net/wow/auction/data/{}?locale={}&apikey={}'.format(server, locale, myapi)

            #return
            # .loads 함수인 것을 봅니다. s가 없는 load 함수는 파일포인터를 받더군요
            print('json주소를 받아옵니다')
            '''
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, requests.get, url)
            response = await future
            load =json.loads(response.text)
            #load = json.loads(requests.get(url).text)
            '''
            # requests가 아닌 aiohttp.ClientSession get 을 사용한 비동기방식으로 변경합니다
            start_time = time.time()
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    load = json.loads(await resp.text())
                    js_url = load['files'][0]['url']
                async with sess.get(js_url) as resp:
                    print('주소:{} \n로부터 json 덤프 파일을 다운로드합니다...\n'.format(js_url))
                    async with aiofiles.open(f'auction-{server}.json', 'wb') as f:
                        await f.write(await resp.read())
            # 덤프 시각을 db에 기록합니다
            str_now = datetime.datetime.now().strftime('%H:%M-%m/%d/%y')
            await conn.execute(tbl_wow_server_info.update().where(tbl_wow_server_info.c.server==server).values
                                        (dumped_time=str_now))

            end_time = time.time()
            elapsed_time = math.floor(end_time - start_time)
            # 받아온 json에 옥션 json 파일의 주소를 포함한 리스폰스를 보내줍니다. 
            print('.다운로드 완료!')
            print(f'총 {elapsed_time}초 소요')
            print('.파싱을 시작합니다')
            async with aiofiles.open(f'auction-{server}.json', 'r') as f:
                js = json.loads(await f.read())
            #print(js['auctions'])

            '''
            with open("auction.json", "r") as f:
                js = json.load(f)
                #print(js['auctions'])
            '''

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


            '''
            target_item_id = await get_item_id(conn, target_item_name)

            item_id_list = []
            for ll in item_list:
                id_ = await get_item_id(conn, ll)
                item_id_list.append(id_)
            '''

            # 저장된 파일을 읽은 후 한줄씩 탐색합니다
            golems = []
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
                '''
                # 프로그레션을 표시합니다
                pct = int(num * 100 / total)
                print('{}번쨰- [{}%]'.format(num, pct))
                '''
                #해당 item넘버를 통해 item name을 받아옵니다
                # 로컬 테이블을 먼저 검색해보고 없는 아이템이라면 블리자드 dev웹을 통해 가져옵니다
                item = l['item']
                name = ''

                '''
                result = 0
                async for r in conn.execute(tbl_items.select().where(tbl_items.c.id==int(item))):
                    #print(r[1])
                    name = r[1]
                    result = 1
                #해당 아이템이 로컬 테이블에 없다면 받아온 후 로컬 테이블에 저정합니다
                if result == 0:
                    print('### item no. {} 이 로컬에 없기에 battlenet dev를 통해 이름을 가져옵니다...'.format(int(item)))
                    name = get_item(item)
                    print(name)
                    await conn.execute(tbl_items.insert().values(id=int(item), name=name))

                #item name 을 포함하여 현재 행을 DB에 삽입합니다
                await conn.execute(tbl_auctions.insert().values(item_name=name,
                                                    auc=l['auc'],
                                                    item=l['item'],
                                                    owner=l['owner'],
                                                    owner_realm=l['ownerRealm'],
                                                    bid=l['bid'],
                                                    buyout=l['buyout'],
                                                    quantity=l['quantity'],
                                                    timeleft=l['timeLeft'],
                                                    datetime='000'))
                '''
                # 해당아이템에 대한 딕트-리스트가 존재하지 않을경우
                cur = int(l['item'])
                price = 0
                if l['buyout'] == 0:
                    price = int(l['bid'] / int(l['quantity']))
                else:
                    price = int(l['buyout'] / int(l['quantity'])) # 묶음 가격을 감안하지 못해서 추가합니다

                if temp_dict.get(cur) is None:
                    temp_name = ''
                    #temp_name = await get_item_name(conn, cur)
                    #print(temp_name)
                    temp_dict[cur] = {'item_name': temp_name, 'num': int(l['quantity']), 'min': price, 'min_seller': l['owner']}
                # 해당아이템 딕트가 이미 존재할 경우
                else:
                    temp_dict[cur]['num'] = temp_dict[cur]['num'] + l['quantity']
                    temp_dict[cur]['num'] = temp_dict[cur]['num'] + l['quantity']

                    if (int(temp_dict[cur]['min']) == 0) or (price < temp_dict[cur]['min']):
                        temp_dict[cur]['min'] = price
                        temp_dict[cur]['min_seller'] = l['owner']

                '''
                # 각 아이템의 리스트를 작성합니다
                if l['item'] in item_id_list:
                    #d = json.dumps(l, ensure_ascii = False) #ensure_ascii는 유니코드 출력의 한글 문제를 해결해줍니다
                    #i += 1
                    #print('{}\n{}'.format(l['item'], item_id_list.index(l['item'])))
                    item_name = item_list[item_id_list.index(l['item'])]
                    if result_dict_set[item_name].get('num') is not None:
                        #num = int(result_dict_set[item_name]['num']) + 1
                        result_dict_set[item_name]['num'] = result_dict_set[item_name]['num'] + l['quantity']
                    else:
                        result_dict_set[item_name]['num'] = l['quantity'] 
                        #num = 1

                    #print('{}\n{}\n{}\n\n'.format(l,item_name, result_dict_set))
                    #sellers.append(l['owner'])
                    price = l['buyout'] / int(l['quantity']) # 묶음 가격을 감안하지 못해서 추가합니다

                    # 간혹 즉구가없이 경매가만 올리는 유저가 있어 계산에 오류가 생기길래 추가했습니다
                    #if price == 0:
                    if l['buyout'] == 0:
                        price = l['bid'] / int(l['quantity'])

                    #if min == 0:
                    if result_dict_set[item_name].get('min') is None:
                        #min = int(price)
                        #min_seller = l['owner']
                        result_dict_set[item_name]['min'] = int(price)
                        result_dict_set[item_name]['min_seller'] = l['owner']
                    else:
                        #if int(price) < min:
                        if int(price) < result_dict_set[item_name]['min']:
                            #min = int(price) 
                            #min_seller = l['owner']
                            result_dict_set[item_name]['min'] = int(price)
                            result_dict_set[item_name]['min_seller'] = l['owner']

                    if max == 0:
                        max = int(price)
                    else:
                        if int(price) > max:
                            max = int(price) 

                    sum += price
                    
                    #result_dict_set[item_name] = {'min' : min, 'min_seller' : min_seller, 'num' : num}
                '''

                # 내가 경매에 부친 물건이 있는지 표시합니다
                '''
                if l['owner'] in name_list:
                    #print('헤헤헤')
                    mine = []
                    mine.append(get_item_name(l['item']))
                    mine.append(get_item_name(l['item']))
                    mine.append(l['owner'])
                    mine.append(int(l['buyout']/10000))
                    #print(get_item(l['item']))
                    my_item.append(mine)
                    '''


            #print(result_dict_set)
            #print(temp_dict)
            ## 각 item 반복작업 종료


            # arranged_auction db에 삽입 프로세스 by 만들어진 temp_dict를 통해
            #
            #

            #str_now = datetime.datetime.now().strftime('%H:%M-%m/%d/%y')

            print(f'\n## {server} arranged_auction db에현재 정리된 dict를 삽입하기 시작합니다')
            #print(temp_dict.keys())
            start_time = time.time()


            for id_ in temp_dict.keys():
                found = 0
                dict_ = temp_dict[id_]
                #print(dict_)
                
                #async for r in conn.execute(tbl_arranged_auction.select().where((tbl_arranged_auction.c.server==server))):
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
                    str_chain = ''
                    for i_ in range(0, 1439):
                        str_chain = str_chain + '0?'
                    str_chain = str_chain + str(dict_['min'])

                    await conn.execute(tbl_arranged_auction.insert().values(server=server,
                                                        item=id_,
                                                        num=dict_['num'],
                                                        min=dict_['min'],
                                                        min_seller=dict_['min_seller'],
                                                        min_chain=str_chain,
                                                        edited_time=str_now,
                                                        image=''))
                # 해당 튜플이 있을 경우
                else:
                    #먼저 str_chain 을 가져옵니다
                    async for sel_ in conn.execute(tbl_arranged_auction.select().where(
                        and_((tbl_arranged_auction.c.server==server),(tbl_arranged_auction.c.item==id_)))):
                        str_chain = sel_[5]
                        str_chain = str_chain.split('?', 1)[1] + '?' + str(dict_['min'])
                    await conn.execute(tbl_arranged_auction.update().where(and_((tbl_arranged_auction.c.server==server),(tbl_arranged_auction.c.item==id_))).values(num=dict_['num'],
                                                        min=dict_['min'],
                                                        min_seller=dict_['min_seller'],
                                                        min_chain=str_chain,
                                                        edited_time=str_now,
                                                        image=''))
                '''
                    await conn.execute(tbl_arranged_auction.update().values(server=server,
                                                        item=id_,
                                                        num=dict_['num'],
                                                        min=dict_['min'],
                                                        min_seller=dict_['min_seller'],
                                                        min_chain=str_chain,
                                                        edited_time=str_now,
                                                        image='']
                                                        '''


            '''
            print("\n** 총 {}개의 {}이(가) 올라와 있습니다".format(i, target_item_name))
            print("최소/최대가격은 각각 {} / {} 골드입니다".format(int(min/10000), int(max/10000)))
            print("평균가격은 {}골드입니다".format(int((sum/i)/10000)))
            print("{}".format(set(sellers)))
            '''

            if len(my_item) > 0:
                print('------------------------------------------------')
                print('** 내아이템들:')
                for l in my_item:
                    print(l)
        #return await deco_dictset(result_dict_set)
        end_time = time.time()
        elapsed_time = math.floor(end_time - start_time)
        elapsed_min = 0
        if(elapsed_time > 60):
            elapsed_min = math.floor(elapsed_time / 60)
        elapsed_time = math.floor(end_time - start_time)
        print(f'서버 {server}에 대한 삽입 정리 프로세스 종료')
        print(f'총 {elapsed_time} 초({elapsed_min}분)가 소요되었습니다')
        
        return 


# battle dev 로부터 아이템을 가져옵니다
async def get_item(id):
    # requests를 비동기형 aiohttp 의 clientssion get 으로 대치합니다
    #r = requests.get('https://kr.api.battle.net/wow/item/{}?locale={}&apikey={}'.format(id, locale, myapi))
    #js = json.loads(r.text)
    async with aiohttp.ClientSession() as sess:
        async with sess.get('https://kr.api.battle.net/wow/item/{}?locale={}&apikey={}'.format(id, locale, myapi)) as resp:
            js = json.loads(await resp.text())

    #print(js['name'])
    #일단 가져온 값중 이름만 취하기로 합니다
    # 데이터를 못가져오는 경우가 발생해 아래와 같은 루틴을 추가했습니다. 
    if js.get('status') is not None:
        if js['status'] == 'nok':
            return ''
    else:
        return js['name']

# 로컬 db에서 이름을 통해 id를 가져옵니다
async def get_item_id(conn, name):
    id = 0
    result = 0
    async for r in conn.execute(tbl_items.select().where(tbl_items.c.name==name)):
        id = r[0]
        result = 1

    '''
    # item이라는 변수가 없습니다
    #해당 아이템이 로컬 테이블에 없다면 받아온 후 로컬 테이블에 저정합니다
    if result == 0:
        print('### item no. {} 이 로컬에 없기에 battlenet dev를 통해 이름을 가져옵니다...'.format(int(item)))
        name = get_item(item) #item
        print(name)
        await conn.execute(tbl_items.insert().values(id=int(item), name=name))
    '''

    return id 

# 로컬 db에서 id를 통해 이름를 가져옵니다
async def get_item_name(conn, item_id):
    result = 0
    async for r in conn.execute(tbl_items.select().where(tbl_items.c.id==item_id)):
        name = r[1]
        result = 1

    #해당 아이템이 로컬 테이블에 없다면 받아온 후 로컬 테이블에 저정합니다
    if result == 0:
        print('### item no. {} 이 로컬에 없기에 battlenet dev를 통해 이름을 가져옵니다...'.format(int(item_id)))
        name = await get_item(item_id)
        print(name)
        await conn.execute(tbl_items.insert().values(id=int(item_id), name=name))

    return name 

# item에 대응하는 이미지 파일명을 가져옵니다 db가 다릅니다 wowinfo db에 이미
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
                '''
                ar = {'하늘 골렘': {'num': 10, 'min': 1379999900, 'min_seller': '밀림왕세나씨'}, 
                        '호화로운 모피': {'num': 158, 'min': 4000, 'min_seller': '우렝밀렵'}, 
                        '심해 가방': {'num': 173, 'min': 18560000, 'min_seller': '남미왕'}, 
                        '살아있는 강철': {'num': 77, 'min': 34900000, 'min_seller': '임리치'}, 
                        '사술매듭 가방': {'num': 300, 'min': 18000000, 'min_seller': '인중개박살'}, 
                        '유령무쇠 주괴': {'num': 25, 'min': 3505000, 'min_seller': 'Spit'}}
                '''

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
                async for image_ in conn.execute(tbl_images.select().where(tbl_images.c.item_name==name_)):
                    image_path = image_[1]
                async for tuple_ in conn.execute(tbl_arranged_auction.select().where(and_((tbl_arranged_auction.c.item==id_),(tbl_arranged_auction.c.server==server)))):
                    print('name_:{}'.format(name_))
                    dict_[name_] = {}
                    dict_[name_]['num'] = tuple_[2]
                    dict_[name_]['min'] = tuple_[3]
                    dict_[name_]['min_seller'] = tuple_[4]
                    dict_[name_]['min_chain'] = tuple_[5].split('?')
                    #print(dict_[name_]['min_chain'])
                    dict_[name_]['edited_time'] = tuple_[6]
                    dict_[name_]['image'] = image_path

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
