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


class OpenAIAPILog(Base):
    __tablename__ = "openai_api_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    input_json = Column(String)
    output_json = Column(String)


engine = sqla.create_engine(f"{config.settings['db_path']}")
SessionMaker = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


class BotDB:
    def __init__(self):
        self.session = SessionMaker()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.rollback()

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


