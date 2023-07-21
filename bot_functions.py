import javascript.proxy
from javascript import require
from db import BotDB
import db
from scipy.spatial import KDTree

Vec3 = require('vec3')


def get_block_type_by_name(block_name: str) -> int:
    bot_db = BotDB()

    block_type = bot_db.session.query(db.BlockDisplayNameIdMapping.id).filter(
        db.BlockDisplayNameIdMapping.display_name.ilike(block_name)
    ).scalar()

    if block_type is None:
        raise NoBlockTypeForName(block_name)

    return block_type


def get_closest_block_location(origin_location: Vec3, block_type: int) -> Vec3:
    bot_db = BotDB()
    block_locations = list()
    closest_location = None

    world_locations = bot_db.session.query(db.WorldBlock.x, db.WorldBlock.y, db.WorldBlock.z).where(
        db.WorldBlock.block_type == block_type
    ).all()

    if world_locations is not None:
        for world_location in world_locations:
            block_locations.append([world_location.x, world_location.y, world_location.z])

        kdtree = KDTree(block_locations)
        distance, index = kdtree.query(x=[origin_location.x, origin_location.y, origin_location.z], k=1)
        closest_location = block_locations[index]

    return Vec3(closest_location[0], closest_location[1], closest_location[2])


class BotTasks:
    def __init__(self):
        self.bot_function_queue = list()


class NoBlockTypeForName(Exception):
    """"Raised when corresponding block type can't be found for given name
    """

    def __init__(self, block_name):
        super().__init__(f"No block_type found for block name {block_name}.")


def mine_block(origin_location: Vec3, bot_tasks: BotTasks, block_name):
    pass
    # get block type by name
    block_type = get_block_type_by_name(block_name)
    # get the closest location of block by type
    block_location = get_closest_block_location(origin_location, block_type)
    # path to block
    # dig block
    # pick up


def dig_block_by_location(block_location: Vec3):
    pass

