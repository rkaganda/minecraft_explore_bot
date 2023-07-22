import javascript.proxy
from javascript import require
import logging

import bot_functions
import config

Vec3 = require('vec3')

logger = logging.getLogger('bot_tasks')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=config.settings['bot_log_path'], encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def mine_block(bot: javascript.proxy.Proxy, bot_tasks: list, block_name):
    try:
        # get block type by name
        block_type = bot_functions.get_block_type_by_name(block_name)
    except bot_functions.NoBlockTypeForName:
        bot.chat(f"don't know block_name {block_name}")
        return

    # get the closest location of block by type
    block_location = bot_functions.get_closest_block_location(bot.entity.position, block_type)

    logger.debug(f"mine_block block_location={block_location}")

    bot_tasks.extend([{
        "function": bot_functions.go_to_location,
        "arguments": {"location": block_location, "distance_from": 1}
    }, {
        "function": bot_functions.dig_block_by_location,
        "arguments": {"block_location": block_location}
    }])

    # path to block
    bot_functions.go_to_location(bot=bot, location=block_location, distance_from=1)



