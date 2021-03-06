# -*- coding=utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from .models import Blog,Comment,Category
from django.urls import reverse
from django.core.exceptions import ValidationError
import datetime
from .blogForm import BlogForm
# Publish message to auther when new comment added.
from users.models import InfoMessage
from redis import StrictRedis,ConnectionPool
from myblog.myutil import generateKey
from myblog.settings import RedisKey
from django.contrib.auth.models import User
from haystack.forms import SearchForm

from blogsearchengine.engine import searchengine
from esengine.esenginecore import esengine
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver


#@receiver(post_save,sender=Blog)
#def updateIndex(sender,**kwargs):
#    engine = searchengine(Blog,'content',indexname='myblogindex')
#    engine.updateindex()
# updateIndex(self,indexname, doctype, model, updatefield):
@receiver(post_save,sender=Blog)
def updateEsIndex(sender,**kwargs):
    es = esengine('blog','blog_content',Blog)
    es.updateIndex('blog','blog_content',Blog,'content')



def getUserDataInfo(username):
    blogList =  Blog.objects.filter(auther=User.objects.get(username=username)).filter(draft=False)
    followkey = generateKey(username, RedisKey['FOLLOWKEY'])
    fanskey = generateKey(username, RedisKey['FANSKEY'])
    followcount = 0
    fanscount = 0
    blogCount = 0
    commentCount = 0
    pool = ConnectionPool(host='localhost', port='6379', db=0)
    redis = StrictRedis(connection_pool=pool)
    if redis.exists(followkey):
        followcount = redis.scard(followkey)
    if redis.exists(fanskey):
        fanscount = redis.scard(fanskey)

    for blog in blogList:
        blogCount = blogCount + 1
        commentCount = commentCount + blog.commentcount
    messagekey = generateKey(username, RedisKey['UNREADMSGKEY'])
    if redis.exists(messagekey):
        msgcount = redis.llen(messagekey)
    else:
        msgcount = 0
    pool.disconnect()
    userdataInfo = {'followcount':followcount,
                    'fanscount':fanscount,
                    'blogcount':blogCount,
                    'commentcount':commentCount,
                    'msgcount':msgcount}
    return userdataInfo

# Create your views here.

def content(request,blogId):
    pool = ConnectionPool(host='localhost',port='6379',db=0)
    redis = StrictRedis(connection_pool=pool,decode_responses=True)
    currentusername = request.user.username
    blog = Blog.objects.get(id=blogId)
    title_key = generateKey(blogId,RedisKey['TITLEKEY'])
    readcount_key = generateKey(blogId,RedisKey['READCOUNTKEY'])

    if redis.exists(title_key):
        blog_title = redis.get(title_key).decode()
    else:
        redis.set(title_key, blog.title)
        blog_title = redis.get(title_key).decode()

    blog_content = blog.content

    countOfThumb = 0
    blogthumb_key = generateKey(blogId, RedisKey['THUMBCOUNTKEY'])
    if redis.exists(blogthumb_key):
        countOfThumb = redis.get(blogthumb_key).decode()

    userthumb_key = generateKey(currentusername, RedisKey['THUMBUPKEY'])
    thumbflag = 'F'
    if redis.exists(userthumb_key):
        if redis.sismember(userthumb_key, blogId):
            thumbflag = 'T'

    pool.disconnect()
    comment = Comment.objects.filter(attachedblog=blog)
    request.session['currblogId'] = blogId
    # blog_title = blog.title
    # blog_content = blog.content


    blogContent = {
                   'blog_title':blog_title,
                   'content':blog_content,
                   'comment_list':comment,
                   'countOfThumb':countOfThumb,
                   'thumbupflag':thumbflag,
                   'auther':blog.auther,
                   'curruser':request.user
                   }
    userdataInfo = getUserDataInfo(blog.auther.username)
    blogContent = {**blogContent,**userdataInfo}


    # blog.readcount+=1
    # blog.save()
    readblog_key = generateKey(currentusername, RedisKey['READBLOGKEY'])
    readblogIdlist = []
    response = render(request, 'blogs/content.html', blogContent)
    if readblog_key in request.COOKIES:
        readblogIdlist = request.COOKIES.get(readblog_key).split(',')
        if blogId not in readblogIdlist:
            if redis.exists(readcount_key):
                redis.incr(readcount_key)
            else:
                redis.set(readcount_key, blog.readcount)
                redis.incr(readcount_key)
    else:
        if redis.exists(readcount_key):
            redis.incr(readcount_key)
        else:
            redis.set(readcount_key, blog.readcount)
            redis.incr(readcount_key)
    blog.readcount = redis.get(readcount_key).decode()
    blog.save()
    # 添加cookie
    readblogIdlist.append(blogId)
    readblogIdStr = ','.join(readblogIdlist)
    response.set_cookie(readblog_key, readblogIdStr, 60)

    return response



# def saveBlog(request):
#     blog_title = request.POST['blogtitle']
#     blog_category = request.POST['category']
#     blog_content = request.POST['blogcontent']
#     auther = Users.objects.get(username=request.user.username)
#     category = Category.objects.get(categoryname=blog_category)
#     result_info = ''
#     try:
#         myblog = Blog.create(blog_title,auther,category,blog_content,datetime.datetime.now(),datetime.datetime.now())
#         myblog.save()
#         category.blogcount = category.blogcount+1
#         category.save()
#         result_info = 'Success'
#     except ValidationError as e:
#         result_info = 'Fail'
#     return HttpResponseRedirect(reverse('blogs:addblogResult', kwargs={'info': result_info}))




def saveComment(request):
    comment_content = request.POST['blogcomment']
    blog = Blog.objects.get(pk=request.session['currblogId'])
    result_info = ''
    try:
        auther = User.objects.get(username=request.user.username)
    except:
        auther = User.objects.get(username='anony')
    try:
        mycomment = Comment.create(blog,comment_content,auther,datetime.datetime.now())
        blogId = request.session['currblogId']
        pool = ConnectionPool(host='localhost', port='6379', db=0)
        redis = StrictRedis(connection_pool=pool,decode_responses=True)
        commentcount_key = generateKey(blogId,RedisKey['COMMENTCOUNTKEY'])
        if redis.exists(commentcount_key):
            redis.incr(commentcount_key)
        else:
            redis.set(commentcount_key,blog.commentcount)
            redis.incr(commentcount_key)
        # blog.commentcount = blog.commentcount + 1
        # blog.save()
        mycomment.save()
        blog.commentcount = redis.get(commentcount_key)
        blog.save()
        # Publish message to auther when new comment added(with redis)
        messagekey = generateKey(blog.auther.username,RedisKey['UNREADMSGKEY'])
        message_content = auther.username + u'评论了博客' + blog.title + u'于' + str(datetime.datetime.now())
        redis.lpush(messagekey,message_content)
        result_info = 'Success'
    except ValidationError as e:
        result_info = 'Fail'

    return HttpResponseRedirect(reverse('blogs:content',kwargs={'blogId':request.session['currblogId']}))

def clearRedis(keys):
    pool = ConnectionPool(host='localhost', port='6379', db=0)
    redis = StrictRedis(connection_pool=pool)
    for key in keys:
        if redis.exists(key):
            redis.delete(key)
    pool.disconnect()

def addBlog(request):
    if request.method == 'POST':
        if 'currentblogId' in request.session:
            blogId = request.session['currentblogId']
            tmpBlog = Blog.objects.get(id=blogId)
            if tmpBlog:
                form = BlogForm(request.POST,instance=tmpBlog)
                tmpBlog = form.save(commit=False)
                tmpBlog.draft = False
                tmpBlog.save()
                result_info = 'Success'
            else:
                form = BlogForm(request.POST)
                if form.is_valid():
                    newBlog = form.save(commit=False)
                    newBlog.auther = User.objects.get(username=request.user.username)
                    newBlog.draft = False
                    category = Category.objects.get(categoryname=newBlog.category.categoryname)
                    category.blogcount = category.blogcount+1
                    category.save()
                    newBlog.save()
                    result_info = 'Success'
                    # 当编辑已有博客时，删除redis中内容
            title_key = blogId + '_title'
            content_key = blogId + '_content'
            clearRedis([title_key, content_key])
            del request.session['currentblogId']
        else:
            form = BlogForm(request.POST)
            if form.is_valid():
                newBlog = form.save(commit=False)
                newBlog.auther = User.objects.get(username=request.user.username)
                newBlog.draft = False
                category = Category.objects.get(categoryname=newBlog.category.categoryname)
                category.blogcount = category.blogcount + 1
                category.save()
                newBlog.save()
                result_info = 'Success'
            if 'currentblogId' in request.session:
            # if request.session.has_key('currentblogId'):
                del request.session['currentblogId']
        return HttpResponseRedirect(reverse('blogs:addblogResult', kwargs={'info': result_info}))
    else:
        if request.user.username != 'anony':
            form = BlogForm()
        else:
            return render(request, 'blogs/failedoperation.html')
    return render(request, 'blogs/addblog.html', context={'form':form})


def addBlogResult(request,info):
    tipMessage=''
    if info == 'Success':
        tipMessage = '博文已成功发表！'
    else:
        tipMessage = info
    parameters = {'info':tipMessage}
    return render(request, 'blogs/addblogResult.html', parameters)


def saveDraft(request):
    if request.method == 'POST':
        blogId = request.session.get('currentblogId','-1')
        if blogId!='-1':
            try:
                tmpBlog = Blog.objects.get(id=blogId)
                form = BlogForm(request.POST, instance=tmpBlog)
                tmpBlog = form.save(commit=False)
                tmpBlog.draft = True
                tmpBlog.save()
                result_info = u'文章已保存于草稿箱中。'
                return HttpResponse(result_info)
            except Blog.DoesNotExist:
                form = BlogForm(request.POST)
                if form.is_valid():
                    newBlog = form.save(commit=False)
                    newBlog.auther = Users.objects.get(username=request.user.username)
                    category = Category.objects.get(categoryname=newBlog.category)
                    category.blogcount = category.blogcount+1
                    category.save()
                    newBlog.save()
                    request.session['currentblogId'] = newBlog.id
                    result_info = u'文章已保存于草稿箱中。'
                    return HttpResponse(result_info)
                return HttpResponse('test')
        else:
            form = BlogForm(request.POST)
            if form.is_valid():
                newBlog = form.save(commit=False)
                newBlog.auther = Users.objects.get(username=request.user.username)
                category = Category.objects.get(categoryname=newBlog.category)
                category.blogcount = category.blogcount + 1
                category.save()
                newBlog.save()
                request.session['currentblogId'] = newBlog.id
                result_info = u'文章已保存于草稿箱中。'
                return HttpResponse(result_info)
            else:
                return HttpResponse('test')
    else:
        return HttpResponse('test')


def articlelist(request):
    if request.user.username == 'anony':
        return render(request, 'blogs/failedoperation.html')
    else:
        blogList = Blog.objects.filter(auther=request.user)
    return render(request,'blogs/articleList.html',{'blogList':blogList,
                                                    'curruser':request.user})

def blogmanage(request):
    if request.user.username == 'anony':
        return render(request, 'blogs/failedoperation.html')
    else:
        blogList = Blog.objects.filter(auther=request.user)
    return render(request, 'blogs/blogmanage.html', {'blogList': blogList,
                                                     'curruser': request.user})


def deleteblog(request,blogId):
    blog = Blog.objects.get(id=blogId)
    if blog.auther.username == request.user.username:
        blog.delete()
        title_key = blogId + '_title'
        content_key = blogId + '_content'
        readcount_key = blogId + '_readcount'
        commentcount_key = blogId + '_commentcount'
        clearRedis([title_key, content_key, readcount_key,commentcount_key])
        blogList = Blog.objects.filter(auther=request.user)
    else:
        return render(request, 'blogs/failedoperation.html')
    return HttpResponseRedirect(reverse('blogs:blogmanage'))


def editblog(request,blogId):
    tmpBlog = Blog.objects.get(id=blogId)
    request.session['currentblogId'] = blogId
    form = BlogForm()
    blogContent = {}
    if tmpBlog.auther.username == request.user.username:
        blogContent = {
            'title':tmpBlog.title,
            'category':tmpBlog.category,
            'content':tmpBlog.content,
            'form':form
        }
    else:
        return render(request, 'blogs/failedoperation.html')
    return render(request, 'blogs/addblog.html', blogContent)



def commentmanage(request):
    blogList = Blog.objects.filter(auther=request.user)
    commentList = []
    for blog in blogList:
        commentList.append(Comment.objects.filter(attachedblog=blog))
    return render(request,'blogs/commentmanage.html',{'commentList':commentList,
                                                      'curruser': request.user})


def deletecomment(request,commentId):
    comment = Comment.objects.get(id=commentId)
    attachedBlog = comment.attachedblog
    if attachedBlog.auther.username == request.user.username:
        comment.delete()
        attachedBlog.commentcount -= 1
        attachedBlog.save()
    else:
        return render(request, 'blogs/failedoperation.html')
    return HttpResponseRedirect(reverse('blogs:commentmanage'))


def draftmanage(request):
    blogList = Blog.objects.filter(auther=request.user).filter(draft=True)
    return render(request, 'blogs/draftmanage.html', {'blogList': blogList,
                                                      'curruser': request.user})

# 点赞功能
def thumbup(request):
    try:
        currentUser = request.user
    except KeyError:
        return render(request,'users/pleaselogin.html')
    except Users.DoesNotExist:
        return render(request, 'users/pleaselogin.html')
    blogId = request.session['currblogId']
    blog = Blog.objects.get(pk=blogId)
    auther = blog.auther.username
    userthumb_key = generateKey(currentUser.username,RedisKey['THUMBUPKEY'])
    blogthumb_key = generateKey(blogId,RedisKey['THUMBCOUNTKEY'])
    pool = ConnectionPool(host='localhost', port='6379', db=0)
    redis = StrictRedis(connection_pool=pool,decode_responses=True)
    title = ''
    countOfThumb = 0

    messagekey = generateKey(auther, RedisKey['UNREADMSGKEY'])
    # 每个读者不能给同一篇文章多次点赞
    if redis.sismember(userthumb_key,blogId):
        pass
    else:
        redis.sadd(userthumb_key, blogId)
        if redis.exists(blogthumb_key):
            redis.incr(blogthumb_key)
        else:
            redis.set(blogthumb_key,countOfThumb)
            redis.incr(blogthumb_key)
        message_content = currentUser.username + u'点赞了博客' + blog.title + u'于' + str(datetime.datetime.now())
        redis.lpush(messagekey, message_content)

    pool.disconnect()
    return HttpResponseRedirect(reverse('blogs:content', kwargs={'blogId': request.session['currblogId']}))



