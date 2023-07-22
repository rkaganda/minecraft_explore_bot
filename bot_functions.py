import javascript.proxy
from javascript import require
from scipy.spatial import KDTree
import logging

import config
from db import BotDB
import db

Vec3 = require('vec3')
pathfinder = require('mineflayer-pathfinder')


logger = logging.getLogger('bot_functions')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=config.settings['bot_log_path'], encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))


def get_block_type_by_name(block_name: str) -> int:
    bot_db = BotDB()

    block_type = bot_db.session.query(db.BlockDisplayNameIdMapping.id).filter(
        db.BlockDisplayNameIdMapping.display_name.ilike(block_name)
    ).scalar()

    if block_type is None:
        raise NoBlockTypeForName(block_name)

    return block_type


def get_closest_block_location(origin_location: Vec3, block_type: int) -> Vec3:
    logger.debug(f"bot_functions: get_closest_block_location origin_location={origin_location}")
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


class NoBlockTypeForName(Exception):
    """"Raised when corresponding block type can't be found for given name
    """

    def __init__(self, block_name):
        super().__init__(f"No block_type found for block name {block_name}.")


def dig_block_by_location(bot: javascript.proxy.Proxy, block_location: Vec3):
    bot.chat(f"digging block at {block_location}")
    goal_block = bot.blockAt(block_location)
    bot.dig(goal_block)


def go_to_location(bot: javascript.proxy.Proxy, location: Vec3, distance_from: int):
    bot.chat(f"going to {location}")
    bot.loadPlugin(pathfinder.pathfinder)

    # travel to the location
    bot.pathfinder.setGoal(
        pathfinder.goals.GoalNear(location.x, location.y, location.z, distance_from))


def observe_local_blocks(bot: javascript.proxy.Proxy):
    scan_range = 4
    bot_location = bot.entity.position

    scan_points = [Vec3(bot_location.x + x, bot_location.y + y, bot_location.z + z)
                   for x in range(-scan_range, scan_range + 1)
                   for y in range(-scan_range, scan_range + 1)
                   for z in range(-scan_range, scan_range + 1)]

    bot_db = BotDB()

    for point in scan_points:
        block = bot.blockAt(point)
        bot_db.update_block(block)
        bot_db.commit()
        bot_db.close()


