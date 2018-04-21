# -*- coding=utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from .models import Users
from django.urls import reverse
from PIL import Image
from django.core.exceptions import ValidationError
from django.contrib.sessions.backends.db import SessionStore
from myblog.settings import MEDIA_ROOT
from .userForm import UserRegisterForm,UserLoginForm
from blogs.models import Blog
from .models import InfoMessage
from redis import StrictRedis,ConnectionPool
from myblog.myutil import generateKey
from myblog.settings import RedisKey

# Create your views here.


def userregister(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            result_info = 'success'
            return HttpResponseRedirect(reverse('users:registerResult', kwargs={'info': result_info}))
    else:
        form = UserRegisterForm()
    return render(request,'users/userregister.html',{'form':form})


def registerResult(request,info):
    if info == 'success':
        content = '注册成功！'
    else:
        content = info
    return render(request,'users/registerResult.html',{'result_info':content})


def userlogin(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            result_info = ''
            try:
                user = Users.objects.get(username=username)
                tmpPassword = user.password
                if tmpPassword == password:
                    result_info = 'success'
                    request.session['username'] = username
                else:
                    result_info = 'fail'
            except Exception as e:
                result_info = 'fail'
            return HttpResponseRedirect(reverse('users:loginResult', kwargs={'info': result_info}))
    else:
        form = UserLoginForm()
    return render(request, 'users/userlogin.html',{'form':form})


def loginResult(request,info):
    if info == 'success':
        content = '登录成功！'
        username = request.session['username']
        return HttpResponseRedirect(reverse('index'))
    else:
        content = '用户名或密码错误！'
        return render(request,'users/loginResult.html',{'result_info':content})


def userIndex(request,username):
    try:
        user = Users.objects.get(username=username)
        currentUser = Users.objects.get(username=request.session['username'])
        blogList = Blog.objects.filter(auther=username).filter(draft=False)
        content = {'username':username,
                   'currentUser':currentUser,
                   'blogList':blogList
                   }
    except Exception as e:
        content = {'username':e}
    return render(request,'users/userindex.html',content)


def userinfo(request,username):
    try:
        user = Users.objects.get(username=username)
        currentUser = Users.objects.get(username=request.session['username'])
        birthday = user.birthday
        email = user.email
        registertime = user.registertime
        content = {'username':username,
                   'registertime':registertime,
                   'birthday':birthday,
                   'email':email,
                   'currentUser':currentUser
                   }
    except Exception as e:
        return render(request, 'users/pleaselogin.html')
    return render(request,'users/userinfo.html',content)


def logoff(request):
    try:
        del request.session['username']
    except KeyError:
        pass
    return HttpResponseRedirect(reverse('index'))


# messagebox
def messagebox(request):
    try:
        currentUser = Users.objects.get(username=request.session['username'])
        pool = ConnectionPool(host='localhost', port='6379', db=0)
        redis = StrictRedis(connection_pool=pool)
        messagekey = generateKey(currentUser.username,RedisKey['UNREADMSGKEY'])
        if redis.exists(messagekey):
            infos = redis.lrange(messagekey,0,redis.llen(messagekey)-1)
            msginfos = []
            for msg in infos:
                msg = msg.decode()
                msginfos.append(msg)
            messages = {'infos': msginfos}
        else:
            messages = {}
        # infos = InfoMessage.objects.filter(attachUser=currentUser)

    except Exception as e:
        messages = {}
    return render(request,'users/messagebox.html',messages)

def setreaded(request):
    try:
        currentUser = Users.objects.get(username=request.session['username'])
        messagekey = generateKey(currentUser.username, RedisKey['UNREADMSGKEY'])
        pool = ConnectionPool(host='localhost', port='6379', db=0)
        redis = StrictRedis(connection_pool=pool)
        if redis.exists(messagekey):
            redis.delete(messagekey)
    except Exception as e:
        pass
    return HttpResponseRedirect(reverse('users:messagebox'))

# 关注与粉丝
def follow(request,followusername):
    try:
        currentUser = Users.objects.get(username=request.session['username'])
    except Users.DoesNotExist:
        return HttpResponseRedirect(reverse('users:pleaselogin'))
    except KeyError:
        return HttpResponseRedirect(reverse('users:pleaselogin'))
    currentUsername = request.session['username']
    if currentUser:
        followkey = generateKey(currentUsername,RedisKey['FOLLOWKEY'])
        fanskey = generateKey(followusername,RedisKey['FANSKEY'])
        pool = ConnectionPool(host='localhost', port='6379', db=0)
        redis = StrictRedis(connection_pool=pool)
        if redis.exists(followkey):
            if redis.sismember(followkey,followusername):
                return HttpResponse('hasfollow')
            else:
                redis.sadd(followkey,followusername)
                redis.sadd(fanskey,currentUsername)
        else:
            redis.sadd(followkey, followusername)
            redis.sadd(fanskey, currentUsername)
        pool.disconnect()
    return HttpResponse('follow')