import random
import requests
import json
import logging
import datetime
import yaml

import config
from db import BotDB

logger = logging.getLogger('openai')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=config.settings['discord_log_path'], encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

openai_prompts = dict()

with open("openai.yaml", 'r') as stream:
    try:
        openai_prompts = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        logger.debug(exc)
        raise exc


def query_chat_message(db: BotDB, chat_message: str):
    chat_message_system = openai_prompts['chat_message_system']

    message_chain = [{
        "role": "system",
        "content": f"{chat_message_system}"
    }, {
        "role": "user",
        "content": openai_prompts['chat_message_prompt'].format(chat_message=chat_message)
    }]

    json_data = {
        "model": config.settings['openapi_model'],
        "messages": message_chain,
        "temperature": openai_prompts['chat_message_temperature']
    }

    attempt_count = 0
    response = None

    while attempt_count < config.settings['attempt_limit']:
        print(f"start attempt_count={attempt_count}")
        r = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': 'Bearer {}'.format(config.settings['openapi_token'])},
            json=json_data
        )
        openai_log = db.store_openai_log(
            input_str=json.dumps(json_data),
            output_str=f"{r.content}"
        )
        db.commit()

        response = json.loads(r.content)
        if 'choices' in response:
            response = f"{response['choices'][0]['message']['content']}"
            attempt_count = config.settings['attempt_limit']
        else:
            try:
                if response['error']['type'] == 'server_error' and \
                        response['error']['type'] == 'context_length_exceeded':
                    attempt_count = attempt_count + 1
                elif response['error']['type'] == 'server_error':
                    attempt_count = attempt_count + 1
                else:
                    attempt_count = config.settings['attempt_limit']
            except KeyError:
                attempt_count = config.settings['attempt_limit']
            logger.error(f"Invalid OpenAI API id={openai_log.id} timestamp={openai_log.timestamp}")

    return response
