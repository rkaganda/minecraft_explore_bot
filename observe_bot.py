from javascript import require, On, Once, AsyncTask, once, off
import math
import logging

import config
import db
import openai
from db import BotDB
from bot_tasks import BotTask

logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=config.settings['bot_log_path'], encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

BOT_USERNAME = config.settings['bot_name']

mineflayer = require('mineflayer')
Vec3 = require('vec3')
pathfinder = require('mineflayer-pathfinder')

bot = mineflayer.createBot({
    'host': config.settings['server_ip'],
    'port': config.settings['server_port'],
    'username': BOT_USERNAME,
    'hideErrors': False})

bot.loadPlugin(pathfinder.pathfinder)

mcData = require('minecraft-data')(bot.version)
movements = pathfinder.Movements(bot, mcData)

db.init_db()
last_location = None


@Once(bot, 'login')
def login(this, *args):
    try:
        global last_location
        bot.chat(f'{BOT_USERNAME} spawned')
        logger.info(f'{BOT_USERNAME} spawned')
        last_location = bot.entity.position
    except Exception as e:
        logger.exception("bot:login")
        raise e


def euclidean_distance_3d(point1, point2):
    return math.sqrt((point2.x-point1.x)**2 + (point2.y-point1.y)**2 + (point2.z-point1.z)**2)


@On(bot, 'chat')
def handle_msg(this, sender, message, *args):
    try:
        if sender and (sender != BOT_USERNAME):
            bot.chat(f'heard - {message}')
            logger.info(f'heard - {message}')
            if 'come' in message:
                player = bot.players[sender]
                target = player.entity
                if not target:
                    bot.chat("can't see target")
                    return
                pos = target.position
                bot.pathfinder.setMovements(movements)
                bot.pathfinder.setGoal(pathfinder.goals.GoalNear(pos.x, pos.y, pos.z, 1))
            elif message == 'stop':
                off(bot, 'chat', handle_msg)
            else:
                bot_task = BotTask(bot)
                bot.chat(bot_task.handle_user_request(message))
    except Exception as e:
        logger.exception("bot:chat")
        raise e


@On(bot, 'move')
def observe_local_blocks(*args):
    try:
        global last_location
        global Vec3
        # scan range
        scan_range = 4
        move_threshold = 2

        bot_location = bot.entity.position
        if bot_location is not None:
            distance_traveled = round(abs(euclidean_distance_3d(bot_location, last_location)))
            if distance_traveled > move_threshold:
                scan_points = [Vec3(bot_location.x + x, bot_location.y + y, bot_location.z + z)
                               for x in range(-scan_range, scan_range + 1)
                               for y in range(-scan_range, scan_range + 1)
                               for z in range(-scan_range, scan_range + 1)]

                db = BotDB()

                for point in scan_points:
                    block = bot.blockAt(point)
                    db.update_block(block)
                    db.commit()
                    db.close()
                last_location = bot.entity.position
        else:
            pass
    except Exception as e:
        logger.exception("bot:move")
        raise e


