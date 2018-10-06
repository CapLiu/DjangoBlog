# -*- coding=utf-8 -*-
from django.shortcuts import render
from users.models import Users,InfoMessage
from blogs.models import Blog
from .indexForm import searchForm
# from dwebsocket import require_websocket,accept_websocket
# 从redis中将每篇博客的阅读数回写到数据库中
from redis import StrictRedis,ConnectionPool
from .myutil import generateKey
from .settings import RedisKey
import uuid
from django.contrib.auth import authenticate
from django.contrib.auth.models import User,AnonymousUser
from django.contrib.auth import get_user


def index(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = get_user(request)
    username = request.user.username
    blogList = Blog.objects.filter(draft=False).order_by('title')
    pool = ConnectionPool(host='localhost', port='6379', db=0)
    redis = StrictRedis(connection_pool=pool)
    searchform = searchForm()
    # get all unread message count by redis
    messagekey = generateKey(username,RedisKey['UNREADMSGKEY'])
    if redis.exists(messagekey):
        msgcount = redis.llen(messagekey)
    else:
        msgcount = 0
    pool.disconnect()
    content = { 'blog_list':blogList,
                'curruser':user,
                'searchform':searchform,
                'msgcount':msgcount
               }
    return render(request, 'myblog/index.html', content)


def searchResult(request):
    try:
        username = request.session['username']
        user = Users.objects.get(username=username)
    except KeyError:
        user = Users.objects.get(username='anony')
        request.session['username'] = 'anony'
    except Users.DoesNotExist:
        user = Users.objects.get(username='anony')
        request.session['username'] = 'anony'
    if request.method == 'GET':
        form = searchForm(request.GET)
        if form.is_valid():
            blogList = Blog.objects.filter(content__contains=form.cleaned_data['searchContext'])
    else:
        form = searchForm()
        blogList = Blog.objects.filter(draft=False).order_by('title')
    content = {'blog_list': blogList,
               'curruser': user,
               'searchform':form
            }
    return render(request, 'myblog/index.html', content)
