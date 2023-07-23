import random
import requests
import json
import logging
import datetime
import yaml
from typing import Any

import config
from db import BotDB

logger = logging.getLogger('openai')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=config.settings['openai_log_path'], encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

openai_prompts = dict()

with open("openai.yaml", 'r') as stream:
    try:
        openai_prompts = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        logger.debug(exc)
        raise exc


def do_openai_query(db: BotDB, json_data: dict) -> Any:
    attempt_count = 0
    response = None

    while attempt_count < config.settings['attempt_limit']:
        r = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': 'Bearer {}'.format(config.settings['openapi_token'])},
            json=json_data
        )
        logger.debug(json.dumps(json_data))
        logger.debug(r.json())
        openai_log = db.store_openai_log(
            input_str=json.dumps(json_data),
            output_str=json.dumps(r.json())
        )
        db.commit()

        response = r.json()
        if 'choices' in response:
            response = response['choices'][0]['message']
            attempt_count = config.settings['attempt_limit']
        else:
            try:
                if response['error']['type'] == 'server_error' and \
                        response['error']['type'] == 'context_length_exceeded':
                    attempt_count = config.settings['attempt_limit']
                elif response['error']['type'] == 'server_error':
                    attempt_count = attempt_count + 1
                else:
                    attempt_count = config.settings['attempt_limit']
            except KeyError:
                attempt_count = config.settings['attempt_limit']
            logger.error(f"Invalid OpenAI API id={openai_log.id} timestamp={openai_log.timestamp}")
            response = None

    return response


def query_functions_functions(db: BotDB, chat_message: str):
    chat_message_system = openai_prompts['minecraft_functions_system']

    message_chain = [{
        "role": "system",
        "content": f"{chat_message_system}"
    }, {
        "role": "user",
        "content": chat_message
    }]

    json_data = {
        "model": f"{config.settings['openapi_model']}-0613",
        "messages": message_chain,
        "functions": openai_prompts['minecraft_functions']
    }

    response_type = None
    response = do_openai_query(db, json_data)

    if response is not None:
        if response['content'] is None:
            response = response['function_call']
            response_type = 'function_call'
        else:
            response = response['content']
            response_type = 'chat'

    return response, response_type





