import sqlalchemy as sqla
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import javascript
from javascript import require

import logging
import datetime
from typing import Tuple, List

import config

logger = logging.getLogger('db')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=config.settings['db_log_path'], encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

Base = declarative_base()
Vec3 = require('vec3')
Block = require('prismarine-block')(require('prismarine-registry')(config.settings['minecraft_version']))


class WorldBlock(Base):
    __tablename__ = "world_blocks"
    x = Column(Integer, primary_key=True)
    y = Column(Integer, primary_key=True)
    z = Column(Integer, primary_key=True)
    block_type = Column(Integer, index=True)


class MinecraftNameIdMapping(Base):
    __tablename__ = "item_name_id_mappings"
    name = Column(String, primary_key=True)
    id = Column(Integer, nullable=False)


class OpenAIAPILog(Base):
    __tablename__ = "openai_api_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    input_json = Column(String)
    output_json = Column(String)


class BotVersionAttributes(Base):
    __tablename__ = "bot_version_attributes"
    attribute = Column(String, primary_key=True)
    value = Column(String, nullable=False)


engine = sqla.create_engine(f"{config.settings['db_path']}")
SessionMaker = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


class BotMinecraftVersionMismatch(Exception):
    def __init__(self, db_minecraft_version, bot_minecraft_version):
        self.message = \
            f"DB minecraft version does not match Bot minecraft version {db_minecraft_version}!={bot_minecraft_version}"
        super().__init__(self.message)


def init_db():
    session = SessionMaker()

    minecraft_version_attribute = BotVersionAttributes(
        attribute='minecraft_version',
        value=config.settings['minecraft_version'],
    )
    session.add(minecraft_version_attribute)

    # populate mcData
    mc_data = require('minecraft-data')(config.settings['minecraft_version'])

    for idx in mc_data.items:
        name_item_mapping = MinecraftNameIdMapping(
            name=mc_data.items[idx].name,
            id=mc_data.items[idx].id,
        )
        session.add(name_item_mapping)

    session.commit()
    session.close()


class BotDB:
    def __init__(self):
        session = SessionMaker()

        db_minecraft_version = session.query(
            BotVersionAttributes.value
        ).filter(BotVersionAttributes.attribute == 'minecraft_version').scalar()

        if db_minecraft_version is None:
            init_db()
        else:
            if db_minecraft_version != config.settings['minecraft_version']:
                raise BotMinecraftVersionMismatch(db_minecraft_version, config.settings['minecraft_version'])

        self.session = SessionMaker()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()

    def get_block_loc_by_type(self, block_type: int) -> List[Vec3]:
        blocks = self.session.query(Block).filter(Block.block_type == block_type).all()

        if blocks is not None:
            block_locations = [Vec3(block.x, block.y, block.z) for block in blocks]
        else:
            block_locations = []

        return block_locations

    def update_block(self, block: Block):
        world_block = WorldBlock(
            x=block.position.x,
            y=block.position.y,
            z=block.position.z,
            block_type=block.type
        )
        self.session.merge(world_block)
        self.session.flush()
        self.session.commit()

    def store_openai_log(
            self,
            input_str: str,
            output_str: str
    ) -> OpenAIAPILog:
        openai_log = OpenAIAPILog(
            input_json=input_str,
            output_json=output_str,
        )
        self.session.add(openai_log)
        self.session.flush()

        return openai_log


