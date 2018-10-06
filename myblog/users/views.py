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
from .models import UserProfile
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required,user_passes_test

@receiver(post_save,sender=User)
def createProfile(sender,created,instance,**kwargs):
    if created:
        profile = UserProfile(user=instance)
        profile.save()

def checksuperuser(user):
    return user.is_superuser

# Create your views here.


def userregister(request):
    if request.method == 'POST':
         form = UserRegisterForm(request.POST,request.FILES)
         if form.is_valid():
             username = form.cleaned_data['username']
             password = form.cleaned_data['password']
             logoimage = form.cleaned_data['logoimage']
             birthday = form.cleaned_data['birthday']
             email = form.cleaned_data['email']
             mobile = form.cleaned_data['mobilephone']
             user = User.objects.create_user(username,'',password)
             user.userprofile.logoimage = logoimage
             user.userprofile.birthday = birthday
             user.userprofile.mobilephone = mobile
             user.userprofile.email = email
             user.userprofile.save()
             # form.save()
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
            cookie_content = ''

            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            result_info = ''
            try:
                # user = Users.objects.get(username=username)
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    result_info = 'success'
                else:
                    result_info = 'fail'
            except Exception as e:
                result_info = e
                # result_info = e

            response = HttpResponseRedirect(reverse('users:loginResult', kwargs={'info': result_info}))
            return response
    else:
        form = UserLoginForm()
    return render(request, 'users/userlogin.html',{'form':form})


def loginResult(request,info):
    if info == 'success':
        return HttpResponseRedirect(reverse('index'))
    else:
        content = info # '用户名或密码错误！'
        return render(request,'users/loginResult.html',{'result_info':content})


def userIndex(request,username):
    try:
        # user = Users.objects.get(username=username)
        user = User.objects.get(username=username)
        currentUser = request.user
        blogList = Blog.objects.filter(auther=user).filter(draft=False)
        content = {'username':username,
                   'curruser':currentUser,
                   'blogList':blogList
                   }
    except Exception as e:
        content = {'username':e}
    return render(request,'users/userindex.html',content)


def userinfo(request,username):
    try:
        # user = Users.objects.get(username=username)
        currentUser = request.user
        birthday = currentUser.userprofile.birthday
        email = currentUser.userprofile.email
        registertime = currentUser.userprofile.registertime
        content = {'username':username,
                   'registertime':registertime,
                   'birthday':birthday,
                   'email':email,
                   'curruser':currentUser
                   }
    except Exception as e:
        return render(request, 'users/pleaselogin.html')
    return render(request,'users/userinfo.html',content)


def logoff(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


# messagebox
def messagebox(request):
    try:
        currentUser = request.user
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
        currentUser = request.user
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
        currentUser = request.user
    except Users.DoesNotExist:
        return HttpResponseRedirect(reverse('users:pleaselogin'))
    except KeyError:
        return HttpResponseRedirect(reverse('users:pleaselogin'))
    currentUsername = currentUser.username
    if currentUser:
        followkey = generateKey(currentUsername,RedisKey['FOLLOWKEY'])
        fanskey = generateKey(followusername,RedisKey['FANSKEY'])
        pool = ConnectionPool(host='localhost', port='6379', db=0)
        redis = StrictRedis(connection_pool=pool)
        if redis.exists(followkey):
            if redis.sismember(followkey,followusername):
                return HttpResponseRedirect(reverse('blogs:content', kwargs={'blogId': request.session['currblogId']}))
            else:
                redis.sadd(followkey,followusername)
                redis.sadd(fanskey,currentUsername)
        else:
            redis.sadd(followkey, followusername)
            redis.sadd(fanskey, currentUsername)
        pool.disconnect()
    return HttpResponseRedirect(reverse('blogs:content',kwargs={'blogId':request.session['currblogId']}))

# 新旧user迁移功能
# 该功能仅供超级用户使用
@login_required
@user_passes_test(checksuperuser)
def migrateuser(request):
    oldusers = Users.objects.all()
    for olduser in oldusers:
        try:
            newuser = User.objects.create_user(olduser.username,'',olduser.password)
            newuser.userprofile.logoimage = olduser.logoimage
            newuser.userprofile.birthday = olduser.birthday
            newuser.userprofile.mobilephone = olduser.mobilephone
            newuser.userprofile.email = olduser.email
            newuser.userprofile.save()
            # Users.delete(username=olduser.username)
            result_info = 'success'
        except ValidationError:
            newuser = User.objects.get_by_natural_key(olduser.username)
            newuser.set_password(olduser.password)
        except Exception as e:
            result_info = e
    return render(request,'users/migrateuser.html',{'result_info':result_info})
