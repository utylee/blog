import asyncio
import requests
import json
import pycurl

import sqlalchemy as sa
from aiopg.sa import create_engine

metadata = sa.MetaData()

# 경매장 테이블입니다
tbl_auctions = sa.Table('auctions', metadata,
        sa.Column('item_name', sa.String(255)),
        sa.Column('auc', sa.Integer, primary_key=True),
        sa.Column('item', sa.Integer),
        sa.Column('owner', sa.String(255)),
        sa.Column('owner_realm', sa.String(255)),
        sa.Column('bid', sa.Integer),
        sa.Column('buyout', sa.Integer),
        sa.Column('quantity', sa.Integer),
        sa.Column('timeleft', sa.String(255)),
        sa.Column('datetime', sa.String(255)))

# item name을 저장한 테이블입니다
tbl_items = sa.Table('items', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255)))

myapi = 'm5u8gdp6qmhbjkhbht3ax9byp62wench'
server = '아즈샤라'
locale = 'ko_KR'
name_list = ['부자인생', '부자인셍', '부쟈인생', '부쟈인섕','부자인솅','부자인생의소환수','부자인셈']
my_item = []


async def proc(item_list):
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
            load = json.loads(requests.get(url).text)
            js = load['files'][0]['url']

            print('주소:{} \n로부터 json 덤프 파일을 다운로드합니다...\n'.format(js))
            #get_item(95416) #하늘골렘

            # 받아온 json에 옥션 json 파일의 주소를 포함한 리스폰스를 보내줍니다. 해당 주소를 curl로 바이트다운받습니다.
            #requests로 웹페이지로 읽어오니 속도가 너무 느려 이 방법을 사용해보기로 합니다
            c = pycurl.Curl()

            with open("auction.json", "wb") as f:
                c.setopt(c.URL, js)
                c.setopt(c.WRITEDATA, f)
                c.perform()
                c.close()

            print('.다운로드 완료!')

            print('.파싱을 시작합니다')
            with open("auction.json", "r") as f:
                js = json.load(f)
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


            target_item_id = await get_item_id(conn, target_item_name)

            item_id_list = []
            for ll in item_list:
                id_ = await get_item_id(conn, ll)
                item_id_list.append(id_)

            # 저장된 파일을 읽은 후 한줄씩 탐색합니다
            golems = []
            sellers = []
            num = 0
            i = 0
            price = 0
            min = 0
            max = 0
            avg = 0
            sum = 0

            total = len(js['auctions'])
            print('총 {} 개의 경매 아이템이 등록되어있습니다'.format(total))

            for l in js['auctions']:
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
                num += 1

                #하늘골렘 아이템의 리스트를 작성합니다
                # 각 아이템의 리스트를 작성합니다
                if l['item'] in item_id_list:
                #if l['item'] == target_item_id:     #하늘골렘
                #if l['item'] == 95416:     #하늘골렘
                #if l['item'] == 114821:     #사술매듭 가방
                    d = json.dumps(l, ensure_ascii = False) #ensure_ascii는 유니코드 출력의 한글 문제를 해결해줍니다
                    #print(l)
                    #print(d)
                    i += 1
                    sellers.append(l['owner'])
                    price = l['buyout']

                    # 간혹 즉구가없이 경매가만 올리는 유저가 있어 계산에 오류가 생기길래 추가했습니다
                    if price == 0:
                        price = l['bid']

                    if min == 0:
                        min = int(price)
                    else:
                        if int(price) < min:
                            min = int(price) 

                    if max == 0:
                        max = int(price)
                    else:
                        if int(price) > max:
                            max = int(price) 

                    sum += price

                # 내가 경매에 부친 물건이 있는지 표시합니다
                if l['owner'] in name_list:
                    #print('헤헤헤')
                    mine = []
                    mine.append(get_item_name(l['item']))
                    mine.append(l['owner'])
                    mine.append(int(l['buyout']/10000))
                    #print(get_item(l['item']))
                    my_item.append(mine)



            print("\n** 총 {}개의 {}이(가) 올라와 있습니다".format(i, target_item_name))
            print("최소/최대가격은 각각 {} / {} 골드입니다".format(int(min/10000), int(max/10000)))
            print("평균가격은 {}골드입니다".format(int((sum/i)/10000)))
            print("{}".format(set(sellers)))

            if len(my_item) > 0:
                print('------------------------------------------------')
                print('** 내아이템들:')
                for l in my_item:
                    print(l)


# battle dev 로부터 아이템을 가져옵니다
def get_item(id):
    #https://kr.api.battle.net/wow/item/18803?locale=ko_KR&apikey=m5u8gdp6qmhbjkhbht3ax9byp62wench
    r = requests.get('https://kr.api.battle.net/wow/item/{}?locale={}&apikey={}'.format(id, locale, myapi))
    js = json.loads(r.text)
    #print(js['name'])
    #일단 가져온 값중 이름만 취하기로 합니다
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
        name = r[0]
        result = 1

    #해당 아이템이 로컬 테이블에 없다면 받아온 후 로컬 테이블에 저정합니다
    if result == 0:
        print('### item no. {} 이 로컬에 없기에 battlenet dev를 통해 이름을 가져옵니다...'.format(int(item_id)))
        name = get_item(item_id)
        print(name)
        await conn.execute(tbl_items.insert().values(id=int(item_id), name=name))

    return name 

