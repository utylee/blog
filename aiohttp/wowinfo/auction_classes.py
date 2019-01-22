'''
import asyncio
import sqlalchemy as sa
from aiopg.sa import create_engine
from auction import get_item_set, get_item_id
from sqlalchemy import select
from sqlalchemy.sql import and_, or_, not_
from db_tableinfo import *
import math
'''


class Set:
    def __init__(self, setname):
        self.setname = setname 
        self.conn = 0;
    def fork(self):
        if self.setname == '기본구성':
            return DefaultSet(self.setname)
        else:
            return NormalSet(self.setname)
    async def get_decoed_item_set(self, server):
        pass
    async def update_itemset(self, itemset_, pos_, name_):
        pass
class NormalSet(Set):
    async def update_itemset(self, itemset_, pos_, name_):
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_itemset_(itemset_, pos_, name_))
    async def update_itemset_(self, itemset_, pos_, name_):
        async with create_engine(user='postgres',
                                database='auction_db',
                                host='192.168.0.211',
                                password='sksmsqnwk11') as engine:
            async with engine.acquire() as conn:
                itemset_l = await get_item_set(conn, itemset_)
                temp_l = []
                for _ in itemset_l:
                    l_ = _.split('?')
                    if l_[0] == pos_:
                        l_[1] = name_
                    temp_l.append('?'.join(l_))
                ret_str = ','.join(temp_l)
                print(f'indiv_update: ret_str: {ret_str}')

                # itemset 테이블을 업데이트해줍니다
                await conn.execute(tbl_item_set.update().where(tbl_item_set.c.set_name==itemset_)
                                    .values(itemname_list=ret_str))

    async def get_decoed_item_set(self, server):
        dict_ = {}
        async with create_engine(user='postgres',
                                database='auction_db',
                                host='192.168.0.211',
                                password='sksmsqnwk11') as engine:
            async with engine.acquire() as conn:
                itemlist = await get_item_set(conn, self.setname)
                #for name_ in itemlist:
                #itemlist to dict
                for _ in itemlist:
                    l_ = _.split('?')
                    num_ = l_[0]
                    name_ = l_[1]
                    dict_[num_] = {}
                    dict_[num_]['name'] = name_ 

                    id_ = await get_item_id(conn, name_) 
                    image_path = ''
                    async for it_ in conn.execute(tbl_items.select().where(tbl_items.c.id==id_)):
                        img_url = it_[2]
                        #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{img_}.jpg'
                    async for tuple_ in conn.execute(tbl_arranged_auction.select().where(and_((tbl_arranged_auction.c.item==id_),(tbl_arranged_auction.c.server==server)))):
                        #print('name_:{}'.format(name_))
                        #dict_[name_] = {}
                        dict_[num_]['num'] = tuple_[2]
                        dict_[num_]['min'] = tuple_[3]
                        dict_[num_]['min_seller'] = tuple_[4]
                        dict_[num_]['min_chain'] = tuple_[5].split('?')
                        #print(dict_[name_]['min_chain'])
                        dict_[num_]['edited_time'] = tuple_[6]
                        fame = tuple_[9]
                        if(fame is None):
                            fame = 0
                        fame += 1
                        
                        #dict_[name_]['edited_timestamp'] = int(tuple_[7])#timestamp는 웹에서 사용할 일이 없으므로 빼고 반납합니다
                        dict_[num_]['image'] = img_url

                        # 골드,실버,카퍼 를 분리해줍니다
                        price = int(tuple_[3])

                        if price < 10000:
                            dict_[num_]['gold'] = 0
                        else:
                            dict_[num_]['gold'] = math.floor(price / 10000)

                        price = price - dict_[num_]['gold'] * 10000
                        if price < 100:
                            dict_[num_]['silver'] = 0
                        else:
                            dict_[num_]['silver'] = math.floor(price / 100)

                        dict_[num_]['copper'] = price - dict_[num_]['silver'] * 100
                    # fame 을 1 증가시켜줍니다
                    print(f'fame ++1 (id: {id_}, {name_})')
                    await conn.execute(tbl_arranged_auction.update().where(and_((tbl_arranged_auction.c.item==id_),(tbl_arranged_auction.c.server==server))).values(fame=fame))

        return dict_

class DefaultSet(Set):
    async def update_itemset(self, itemset_, pos_, name_):
        #업데이트하지 않습니다
        return
    async def get_decoed_item_set(self, server):
        print('fetch with NO fame ++1')
        dict_ = {}
        async with create_engine(user='postgres',
                                database='auction_db',
                                host='192.168.0.211',
                                password='sksmsqnwk11') as engine:
            async with engine.acquire() as conn:
                itemlist = await get_item_set(conn, self.setname)
                #for name_ in itemlist:
                #itemlist to dict
                for _ in itemlist:
                    l_ = _.split('?')
                    num_ = l_[0]
                    name_ = l_[1]
                    dict_[num_] = {}
                    dict_[num_]['name'] = name_ 

                    id_ = await get_item_id(conn, name_) 
                    image_path = ''
                    async for it_ in conn.execute(tbl_items.select().where(tbl_items.c.id==id_)):
                        img_url = it_[2]
                        #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{img_}.jpg'
                    async for tuple_ in conn.execute(tbl_arranged_auction.select().where(and_((tbl_arranged_auction.c.item==id_),(tbl_arranged_auction.c.server==server)))):
                        #print('name_:{}'.format(name_))
                        #dict_[name_] = {}
                        dict_[num_]['num'] = tuple_[2]
                        dict_[num_]['min'] = tuple_[3]
                        dict_[num_]['min_seller'] = tuple_[4]
                        dict_[num_]['min_chain'] = tuple_[5].split('?')
                        #print(dict_[name_]['min_chain'])
                        dict_[num_]['edited_time'] = tuple_[6]
                        fame = tuple_[9]
                        if(fame is None):
                            fame = 0
                        fame += 1
                        
                        #dict_[name_]['edited_timestamp'] = int(tuple_[7])#timestamp는 웹에서 사용할 일이 없으므로 빼고 반납합니다
                        dict_[num_]['image'] = img_url

                        # 골드,실버,카퍼 를 분리해줍니다
                        price = int(tuple_[3])

                        if price < 10000:
                            dict_[num_]['gold'] = 0
                        else:
                            dict_[num_]['gold'] = math.floor(price / 10000)

                        price = price - dict_[num_]['gold'] * 10000
                        if price < 100:
                            dict_[num_]['silver'] = 0
                        else:
                            dict_[num_]['silver'] = math.floor(price / 100)

                        dict_[num_]['copper'] = price - dict_[num_]['silver'] * 100
                    # 기본구성 set이므로 fame 을 증가시키지 않습니다

        return dict_
