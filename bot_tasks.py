from javascript import require
import json
from typing import Any

import openai
import config
from db import BotDB
import db as db


mcData = require('minecraft-data')(config.settings['minecraft_version'])
Vec3 = require('vec3')


class BotTask:
    def __init__(self, bot):
        self.bot = bot
        self.db = BotDB()

    def handle_user_request(self, message):
        response, response_type = openai.query_functions_functions(self.db, message)
        if response_type == 'function_call':
            if 'arguments' in response:
                function_args = response['arguments']
                function_args = json.loads(function_args)
            else:
                function_args = {}
            function_args['message'] = message
            function_call = response['name']
            method = getattr(self, function_call, None)  # load the function
            return method(**function_args)  # call the function with the arguments provided
        else:
            return response

    def get_item_id(self, item: str) -> int:
        # check db for displayName -> db mapping
        item_ids = self.db.session.query(db.BlockDisplayNameIdMapping.id).filter(
            db.BlockDisplayNameIdMapping.display_name.ilike(item)
        ).all()

        if item_ids is None:  # if there are no matching displayNames
            # TODO openai prompt to attempt to guess name
            pass
        if len(item_ids) > 0:  # if multiple displayNames (item is ambiguous) ask user for clarification
            # TODO openai function that asks users to clarify item
            item_ids = item_ids[0].id  # TODO CHANGE
            # item_names = self.db.session.query(db.BlockDisplayNameIdMapping.id).filter(
            #     db.BlockDisplayNameIdMapping.display_name.ilike(item)
            # ).all()
        else:
            return item_ids[0].id

        return item_ids

    def find_item_location(self, item_id: int) -> list[dict[str, Any]]:
        item_world_locations = []

        # TODO check inventory for item id
        bot = self.bot
        # TODO check db for locations of item id
        world_locations = self.db.session.query(db.WorldBlock.x, db.WorldBlock.y, db.WorldBlock.z).where(
            db.WorldBlock.block_type == item_id
        ).all()

        if world_locations is not None:
            for world_location in world_locations:
                item_world_locations.append(Vec3(world_location.x, world_location.y, world_location.z))

        return item_world_locations

    def deliver_items(self, items: list, location: str, message):
        item_retrieval_results = {}

        for item in items:  # for each item
            item_retrieval_results[item] = dict()
            item_retrieval_results[item]['id'] = self.get_item_id(item)  # get id of item

            if item_retrieval_results[item]['id'] is not None:  # if we have an idea for the item
                item_retrieval_results[item]['locations'] = self.find_item_location(item_retrieval_results[item]['id'])
                # TODO if item location is None create task to *craft item
            else:
                pass
                # TODO create path plan and place items in inventory
        print(str(item_retrieval_results))

        return str(item_retrieval_results) # TODO temp st response


