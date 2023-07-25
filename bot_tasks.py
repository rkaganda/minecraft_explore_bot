import javascript.proxy
from javascript import require
import logging

import bot_functions
import config

Vec3 = require('vec3')
mcData = require('minecraft-data')(config.settings['minecraft_version'])

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


def display_inventory(bot: javascript.proxy.Proxy, bot_tasks: list):
    inventory = bot_functions.get_inventory_items(bot=bot)

    named_inventory = {}
    for item_id, count in inventory.items():
        if item_id in mcData.items:
            named_inventory[f"{mcData.items[item_id].name} {item_id}"] = count
    bot.chat(f"{named_inventory}")


def craft_item(bot: javascript.proxy.Proxy, bot_tasks: list, item_name: str):
    try:
        # get item id
        item_id = bot_functions.get_item_id_by_name(item_name)
    except bot_functions.NoItemIdForName:
        bot.chat(f"don't know item_name {item_name}")
        return

    # get inventory items
    inventory_items = bot_functions.get_inventory_items(bot)

    # check recipies for missing items
    missing_recipe_items = bot_functions.get_recipe_missing_items(item_id=item_id, inventory_items=inventory_items)
    logger.debug(f"missing items for {item_name}: {missing_recipe_items}")

    # get id for crafting table
    table_type = bot_functions.get_block_type_by_name("crafting_table")
    table_location = bot_functions.get_closest_block_location(
        origin_location=bot.entity.position, block_type=table_type)

    valid_recipe_idx = None
    for recipe_idx, recipe_map in enumerate(missing_recipe_items):
        if len(recipe_map['missing'].keys()) == 0:  # if there are no missing items
            if (not recipe_map['requires_table']) or (recipe_map['requires_table'] and table_location is not None):
                valid_recipe_idx = recipe_idx
            break

    if valid_recipe_idx is not None:
        bot_tasks.extend([{
            "function": bot_functions.craft_item_with_recipe,
            "arguments": {
                "item_id": item_id,
                "recipe_idx": valid_recipe_idx,
                "count": 1,
                "table_location": table_location
            }}])
    else:
        bot.chat(f"no valid recipie found for {item_name}")





