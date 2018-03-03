# -*- coding=utf-8 -*-
from django.shortcuts import render
from users.models import Users,InfoMessage
from blogs.models import Blog
from .indexForm import searchForm
from dwebsocket import require_websocket,accept_websocket

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