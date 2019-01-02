import sqlalchemy as sa
from aiopg.sa import create_engine

metadata = sa.MetaData()

# auction db 접속정보입니다
'''
    async with create_engine(user='postgres',
                            database='auction_db',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
'''
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



# wowinfo db 접속정보입니다
'''
    async with create_engine(user='postgres',
                            database='wowinfo',
                            host='192.168.0.211',
                            password='sksmsqnwk11') as engine:
'''
# image file name 테이블입니다
tbl_images = sa.Table('image_info', metadata,
        sa.Column('item_name', sa.String(128), primary_key=True),
        sa.Column('file_name', sa.String(255)))
# arranged_auction 테이블입니다
tbl_arranged_auction = sa.Table('arranged_auction', metadata,
        sa.Column('server', sa.String(128)),
        sa.Column('item', sa.Numeric),
        sa.Column('num', sa.BigInteger),
        sa.Column('min', sa.BigInteger),
        sa.Column('min_seller', sa.String(128)),
        sa.Column('min_chain', sa.Text),
        sa.Column('edited_time', sa.String(128)),
        sa.Column('image', sa.String(255)))
# itemset 테이블입니다
tbl_item_set = sa.Table('item_set', metadata,
        sa.Column('set_name', sa.String(128)),
        sa.Column('itemname_list', sa.String(512)),
        sa.Column('edited_time', sa.String(128)))

