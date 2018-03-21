# -*- coding=utf-8 -*-
from django.shortcuts import render
from users.models import Users,InfoMessage
from blogs.models import Blog
from .indexForm import searchForm
from dwebsocket import require_websocket,accept_websocket
# 从redis中将每篇博客的阅读数回写到数据库中
from redis import StrictRedis,ConnectionPool

def index(request):
    try:
        username = request.session['username']
        user = Users.objects.get(username=username)
    except KeyError:
        user = Users.objects.get(username='anony')
        request.session['username'] = 'anony'
    except Users.DoesNotExist:
        user = Users.objects.get(username='anony')
        request.session['username'] = 'anony'
    blogList = Blog.objects.filter(draft=False).order_by('title')
    # 从redis中将每篇博客的阅读数回写到数据库中
    pool = ConnectionPool(host='localhost', port='6379', db=0)
    redis = StrictRedis(connection_pool=pool)
    for blog in blogList:
        readcount_key = str(blog.id)+'_readcount'
        if redis.exists(readcount_key):
            blog.readcount = redis.get(readcount_key)
            blog.save()


    searchform = searchForm()
    # get all unread message count
    unreadmeg =  InfoMessage.objects.filter(attachUser=user).filter(isRead=False)
    # username = request.session.get('username')
    content = { 'blog_list':blogList,
                'curruser':user,
                'searchform':searchform,
                'msgcount':len(unreadmeg)
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


# reply tip
@accept_websocket
def replyTip(request):
    if request.is_websocket():
        pass
    pass