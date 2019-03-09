# -*- coding=utf-8 -*-
from django.shortcuts import render
from users.models import Users,InfoMessage
from blogs.models import Blog
# 从redis中将每篇博客的阅读数回写到数据库中
from redis import StrictRedis,ConnectionPool
from .myutil import generateKey,getmsgcount
from .settings import RedisKey
import uuid
from django.contrib.auth import authenticate
from django.contrib.auth.models import User,AnonymousUser
from django.contrib.auth import get_user
from haystack.forms import SearchForm
from haystack.views import SearchView
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery
from blogsearchengine.engine import searchengine
# 引入分页
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger

# 使用searchengine进行搜索
#from .indexForm import mysearchForm
#from blogsearchengine.searchForm import enginechoicesearchForm
#from blogsearchengine.searchForm import enginebasesearchForm

from esengine.searchForm import eschoicesearchForm

from django import forms


def index(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = get_user(request)
    username = request.user.username
    blogList = Blog.objects.filter(draft=False).order_by('title')
    # 引入分页机制
    paginator = Paginator(blogList, 10)
    page = request.GET.get('page')
    try:
        blogs = paginator.page(page)
    except PageNotAnInteger:
        blogs = paginator.page(1)
    except EmptyPage:
        blogs = paginator.page(paginator.num_pages)

    pool = ConnectionPool(host='localhost', port='6379', db=0)
    redis = StrictRedis(connection_pool=pool)
    kwargs = {}
    kwargs['searchlist'] = [{'title': u'标题'}, {'content': u'正文'}]
    kwargs['multichoice'] = True
    # searchform = enginechoicesearchForm(**kwargs)
    searchform = eschoicesearchForm(**kwargs)
    # get all unread message count by redis
    messagekey = generateKey(username,RedisKey['UNREADMSGKEY'])
    if redis.exists(messagekey):
        msgcount = redis.llen(messagekey)
    else:
        msgcount = 0
    pool.disconnect()
    content = { 'blog_list':blogs,
                'curruser':user,
                'searchform':searchform,
                'msgcount':msgcount,
               }
    return render(request, 'myblog/index.html', content)


# Create own searchview
class blogSearchView(SearchView):

    def extra_context(self):
        context = super(blogSearchView,self).extra_context()
        searchform = SearchForm()
        context['searchform'] = searchform

        return context




def newsearchView(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = get_user(request)
    username = request.user.username
    searchForm = SearchForm()
    if request.method == 'GET':
        keyword = request.GET['q']
        all_result = SearchQuerySet().filter(content=AutoQuery(keyword))
        content = {'searchResult':all_result,
                   'curruser':user,
                   'msgcount':getmsgcount(username),
                   'searchform':searchForm,
                   'query':keyword}
    else:
        content = {
                   'curruser': user,
                   'msgcount': getmsgcount(username),
                   'searchform': searchForm
                }
    return render(request,'myblog/newsearch.html',content)


def searchengineview(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = get_user(request)
    username = request.user.username
    kwargs = {}
    kwargs['searchlist'] = [u'标题',u'全文',u'用户']
    searchForm = enginechoicesearchForm(**kwargs)
    if request.method == 'GET':
        keycode = request.GET['searchKeyword']
        engine = searchengine(Blog, 'content', indexname='myblogindex')
        option = request.GET['searchrange']
        correct_dict = {}
        if option == '1':
            searchresult,correct_dict = engine.search('title',keycode)
        elif option == '2':
            searchresult,correct_dict = engine.search('content', keycode)
        else:
            searchresult,correct_dict = engine.search('username',keycode)

        content = {
            'searchResult':searchresult,
            'curruser':user,
            'msgcount':getmsgcount(username),
            'searchform':searchForm,
            'correct':correct_dict
        }
    else:
        content = {
                   'curruser': user,
                   'msgcount': getmsgcount(username),
                   'searchform': searchForm
                }
    return render(request,'myblog/searchengine.html',content)


