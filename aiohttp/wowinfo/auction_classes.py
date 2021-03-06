import sys
import math
import asyncio
import sqlalchemy as sa
from aiopg.sa import create_engine
from sqlalchemy import select
from sqlalchemy.sql import and_, or_, not_
#from auction import get_item_set, get_item_id
import auction as auc
import db_tableinfo as db
import logging
#from test import log_path

# db_proc에서 사용되느냐 wowinfo에서 사용되느냐에 따라 log 설정을 바뀌되록 합니다
if(sys.argv[0][-10:] == 'db_proc.py'):
    log = logging.getLogger('dbproc')
elif(sys.argv[0][-14:] == 'test_master.py'):
    from test_master import log_path
    log = logging.getLogger(log_path)
else:
    from test import log_path
    log = logging.getLogger(log_path)

class Set:
    def __init__(self, setname):
        self.setname = setname 
        self.conn = 0;
    def fork(self):
        if self.setname == '기본구성':
            return DefaultSet(self.setname)
        else:
            return NormalSet(self.setname)
    async def get_only_itemset(self, engine, user):
        dict_ = {}
        fame = 0
        async with engine.acquire() as conn:
            #itemlist = await auc.get_item_set(conn, self.setname)
            code, itemlist = await auc.get_item_set(conn, user, self.setname)
            #for name_ in itemlist:
            #itemlist to dict
            for _ in itemlist:
                l_ = _.split('?')
                num_ = l_[0]
                name_ = l_[1]
                dict_[num_] = {}
                dict_[num_]['num'] = num_
                dict_[num_]['item'] = name_
        return code, dict_

    async def get_decoed_item_set(self, engine, server):
        pass
    async def update_itemset(self, engine, user, itemset_, pos_, name_, fullstr=''):
        pass
class NormalSet(Set):
    async def update_itemset(self, engine, user, itemset_, pos_, name_, fullstr=''):
        log.info('came into NormalSet::update_itemset')
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_itemset_(engine, user, itemset_, pos_, name_, fullstr))
    async def update_itemset_(self, engine, user, itemset_, pos_, name_, fullstr):
        async with engine.acquire() as conn:
            b_create = 0
            code, itemset_l = await auc.get_item_set(conn, user, itemset_)
            temp_l = []
            if(not len(itemset_l)):
                b_create = 1
                itemset_l = fullstr.split(',')
                i = 0
                for _ in itemset_l:
                    temp_l.append('?'.join([str(i), _]))
                    i += 1
            else:
                for _ in itemset_l:
                    l_ = _.split('?')
                    if l_[0] == pos_:
                        l_[1] = name_
                    temp_l.append('?'.join(l_))
            ret_str = ','.join(temp_l)
            log.info(f'indiv_update: ret_str: {ret_str}')

        if(not b_create):
            # itemset 테이블을 업데이트해줍니다
            await conn.execute(db.tbl_item_set.update().where(db.tbl_item_set.c.set_name==itemset_)
                                .values(itemname_list=ret_str))
        else: 
            # 해당 셋이 삭제되었으므로 itemset 을 그대로 만들어줍니다
            code = auc.randomstring(5) 
            await conn.execute(db.tbl_item_set.insert().values(set_name=itemset_,
                                                    itemname_list=ret_str,
                                                    edited_time='',
                                                    set_code=code, 
                                                    user=user))

    async def get_decoed_item_set(self, engine, server):
        dict_ = {}
        fame = 0
        async with engine.acquire() as conn:
            itemlist = await auc.get_item_set(conn, self.setname)
            #for name_ in itemlist:
            #itemlist to dict
            for _ in itemlist:
                l_ = _.split('?')
                num_ = l_[0]
                name_ = l_[1]
                dict_[num_] = {}
                dict_[num_]['name'] = name_ 

                id_ = await auc.get_item_id(conn, name_) 
                image_path = ''
                async for it_ in conn.execute(db.tbl_items.select().where(db.tbl_items.c.id==id_)):
                    img_url = it_[2]
                    #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{img_}.jpg'
                async for tuple_ in conn.execute(db.tbl_arranged_auction.select().where(and_((db.tbl_arranged_auction.c.item==id_),(db.tbl_arranged_auction.c.server==server)))):
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
                #print(f'fame ++1({fame}) (id: {id_}, {name_})')
                log.info(f'fame ++1({fame}) (id: {id_}, {name_})')
                # fame 증가시키는 프로세스를 별도 task로 실행시켜 multitasking을 구현합니다.
                # 사용자 응답시간이 많이 빨라집니다. 1회 업데이트에 0.1초씩 걸리더군요. rpi3b+에서..
                await self.increase_fame(engine, server, id_, fame)
                #await conn.execute(db.tbl_arranged_auction.update().where(and_((db.tbl_arranged_auction.c.item==id_),(db.tbl_arranged_auction.c.server==server))).values(fame=fame))

        return dict_

    async def increase_fame(self, engine, srv, id_, fame):
        loop = asyncio.get_event_loop()
        loop.create_task(self.increase_fame_(engine, srv, id_, fame))

    async def increase_fame_(self, engine, srv, id_, fame):
        async with engine.acquire() as conn:
            await conn.execute(db.tbl_arranged_auction.update().where(and_((db.tbl_arranged_auction.c.item==id_),(db.tbl_arranged_auction.c.server==srv))).values(fame=fame))


class DefaultSet(Set):
    async def update_itemset(self, engine, user, itemset_, pos_, name_, fullstr=''):
        #업데이트하지 않습니다
        log.info('came into Defaultset::update_itemset')
        return
    async def get_decoed_item_set(self, engine, server):
        print('fetch with NO fame ')
        log.info('fetch with NO fame ')
        dict_ = {}
        fame = 0
        async with engine.acquire() as conn:
            itemlist = await auc.get_item_set(conn, self.setname)
            #for name_ in itemlist:
            #itemlist to dict
            log.info(f'서버:{server}')
            for _ in itemlist:
                l_ = _.split('?')
                num_ = l_[0]
                name_ = l_[1]
                dict_[num_] = {}
                dict_[num_]['name'] = name_ 

                id_ = await auc.get_item_id(conn, name_) 
                image_path = ''
                async for it_ in conn.execute(db.tbl_items.select().where(db.tbl_items.c.id==id_)):
                    img_url = it_[2]
                    #img_url = f'https://wow.zamimg.com/images/wow/icons/large/{img_}.jpg'
                async for tuple_ in conn.execute(db.tbl_arranged_auction.select().where(and_((db.tbl_arranged_auction.c.item==id_),(db.tbl_arranged_auction.c.server==server)))):
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
