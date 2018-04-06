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

def index(request):
    try:
        username = request.session['username']
        user = Users.objects.get(username=username)
    except KeyError:
        user = Users.objects.get(username='anony')
        if 'username' not in request.session:
            request.session['username'] = str(uuid.uuid1())
    except Users.DoesNotExist:
        user = Users.objects.get(username='anony')
        if request.session['username'] == '':
            request.session['username'] = str(uuid.uuid1())
    username = request.session['username']
    blogList = Blog.objects.filter(draft=False).order_by('title')
    # 从redis中将每篇博客的阅读数回写到数据库中
    pool = ConnectionPool(host='localhost', port='6379', db=0)
    redis = StrictRedis(connection_pool=pool)
    for blog in blogList:
        readcount_key = generateKey(blog.id,RedisKey['READCOUNTKEY'])
        commentcount_key = generateKey(blog.id,RedisKey['COMMENTCOUNTKEY'])
        if redis.exists(readcount_key):
            blog.readcount = redis.get(readcount_key).decode()
            blog.save()
        else:
            redis.set(readcount_key,blog.readcount)
        if redis.exists(commentcount_key):
            blog.commentcount = redis.get(commentcount_key)
            blog.save()
        else:
            redis.set(commentcount_key,blog.commentcount)
    pool.disconnect()

    searchform = searchForm()
    # get all unread message count by redis
    messagekey = generateKey(username,RedisKey['UNREADMSGKEY'])
    if redis.exists(messagekey):
        msgcount = redis.llen(messagekey)
    else:
        msgcount = 0
    pool.disconnect()
    # unreadmeg =  InfoMessage.objects.filter(attachUser=user).filter(isRead=False)
    # username = request.session.get('username')
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
