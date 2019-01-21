from auction import *

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
class NormalSet(Set):
    async def get_decoed_item_set(self, server):
        dict_ = {}
        async with create_engine(user='postgres',
                                database='auction_db',
                                host='192.168.0.211',
                                password='sksmsqnwk11') as engine:
            async with engine.acquire() as conn:
                itemlist = await get_item_set(conn, self.setname)
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
                        fame = tuple_[9]
                        if(fame is None):
                            fame = 0
                        fame += 1
                        
                        #dict_[name_]['edited_timestamp'] = int(tuple_[7])#timestamp는 웹에서 사용할 일이 없으므로 빼고 반납합니다
                        dict_[name_]['image'] = img_url

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
                    # fame 을 1 증가시켜줍니다
                    print(f'fame ++1 (id: {id_}, {name_})')
                    await conn.execute(tbl_arranged_auction.update().where(and_((tbl_arranged_auction.c.item==id_),(tbl_arranged_auction.c.server==server))).values(fame=fame))

        return dict_

class DefaultSet(Set):
    async def get_decoed_item_set(self, server):
        print('오냐고')
        dict_ = {}
        async with create_engine(user='postgres',
                                database='auction_db',
                                host='192.168.0.211',
                                password='sksmsqnwk11') as engine:
            async with engine.acquire() as conn:
                itemlist = await get_item_set(conn, self.setname)
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
                        fame = tuple_[9]
                        
                        #dict_[name_]['edited_timestamp'] = int(tuple_[7])#timestamp는 웹에서 사용할 일이 없으므로 빼고 반납합니다
                        dict_[name_]['image'] = img_url

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
                    # 기본구성 set이므로 fame 을 증가시키지 않습니다

        return dict_
