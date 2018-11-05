# -*- coding=utf-8 -*-

from redis import StrictRedis,ConnectionPool
from .settings import RedisKey
from blogs.models import Blog

def generateKey(pkey,keykind):
    return str(pkey) + '_' + str(keykind)


def getmsgcount(username):
    pool = ConnectionPool(host='localhost', port='6379', db=0)
    redis = StrictRedis(connection_pool=pool)
    # get all unread message count by redis
    messagekey = generateKey(username, RedisKey['UNREADMSGKEY'])
    if redis.exists(messagekey):
        msgcount = redis.llen(messagekey)
    else:
        msgcount = 0
    pool.disconnect()
    return msgcount




