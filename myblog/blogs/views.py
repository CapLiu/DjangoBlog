# -*- coding=utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from .models import Blog,Comment,Category,Users
from django.urls import reverse
from django.core.exceptions import ValidationError
import datetime
from .blogForm import BlogForm
# Publish message to auther when new comment added.
from users.models import InfoMessage
from redis import StrictRedis,ConnectionPool


# Create your views here.

def content(request,blogId):
    pool = ConnectionPool(host='localhost',port='6379',db=0)
    redis = StrictRedis(connection_pool=pool)
    blog = Blog.objects.get(id=blogId)
    title_key = blogId + '_title'
    content_key = blogId + '_content'
    readcount_key = blogId + '_readcount'
    if redis.exists(title_key):
        blog_title = redis.get(title_key)
    else:
        redis.set(title_key, blog.title)
        blog_title = redis.get(title_key)
    if redis.exists(content_key):
        blog_content = redis.get(content_key)
    else:
        redis.set(content_key, blog.content)
        blog_content = redis.get(content_key)
    if redis.exists(readcount_key):
        redis.incr(readcount_key)
    else:
        redis.set(readcount_key, blog.readcount)
        redis.incr(readcount_key)
    pool.disconnect()
    comment = Comment.objects.filter(attachedblog=blog)
    request.session['currblogId'] = blogId
    # blog_title = blog.title
    # blog_content = blog.content
    blogContent = {
                   'blog_title':blog_title,
                   'content':blog_content,
                   'comment_list':comment
                   }
    # blog.readcount+=1
    # blog.save()
    return render(request,'blogs/content.html',blogContent)


# def saveBlog(request):
#     blog_title = request.POST['blogtitle']
#     blog_category = request.POST['category']
#     blog_content = request.POST['blogcontent']
#     auther = Users.objects.get(username=request.session['username'])
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
        auther = Users.objects.get(username=request.session['username'])
    except KeyError:
        auther = Users.objects.get(username='anony')
    try:
        mycomment = Comment.create(blog,comment_content,auther,datetime.datetime.now())
        blogId = request.session['currblogId']
        pool = ConnectionPool(host='localhost', port='6379', db=0)
        redis = StrictRedis(connection_pool=pool)
        commentcount_key = blogId + '_commentcount'
        if redis.exists(commentcount_key):
            redis.incr(commentcount_key)
        else:
            redis.set(commentcount_key,blog.commentcount)
            redis.incr(commentcount_key)
        # blog.commentcount = blog.commentcount + 1
        # blog.save()
        mycomment.save()
        # Publish message to auther when new comment added.
        blogAuther = blog.auther
        message_content = auther.username + u'评论了博客'+blog.title
        infoMessage = InfoMessage.create(blogAuther,message_content)
        infoMessage.save()
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
        if request.session.has_key('currentblogId'):
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
                    newBlog.auther = Users.objects.get(username=request.session['username'])
                    newBlog.draft = False
                    category = Category.objects.get(categoryname=newBlog.category)
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
                newBlog.auther = Users.objects.get(username=request.session['username'])
                newBlog.draft = False
                category = Category.objects.get(categoryname=newBlog.category)
                category.blogcount = category.blogcount + 1
                category.save()
                newBlog.save()
                result_info = 'Success'
            del request.session['currentblogId']
        return HttpResponseRedirect(reverse('blogs:addblogResult', kwargs={'info': result_info}))
    else:
        if request.session['username'] != 'anony':
            form = BlogForm()
        else:
            return render(request, 'blogs/failedoperation.html')
    return render(request, 'blogs/addblog.html', {'form':form})


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
                    newBlog.auther = Users.objects.get(username=request.session['username'])
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
                newBlog.auther = Users.objects.get(username=request.session['username'])
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
    if request.session['username'] == 'anony':
        return render(request, 'blogs/failedoperation.html')
    else:
        blogList = Blog.objects.filter(auther=request.session['username'])
    return render(request,'blogs/articleList.html',{'blogList':blogList})

def blogmanage(request):
    if request.session['username'] == 'anony':
        return render(request, 'blogs/failedoperation.html')
    else:
        blogList = Blog.objects.filter(auther=request.session['username'])
    return render(request, 'blogs/blogmanage.html', {'blogList': blogList})


def deleteblog(request,blogId):
    blog = Blog.objects.get(id=blogId)
    if blog.auther.username == request.session['username']:
        blog.delete()
        title_key = blogId + '_title'
        content_key = blogId + '_content'
        readcount_key = blogId + '_readcount'
        commentcount_key = blogId + '_commentcount'
        clearRedis([title_key, content_key, readcount_key,commentcount_key])
        blogList = Blog.objects.filter(auther=request.session['username'])
    else:
        return render(request, 'blogs/failedoperation.html')
    return HttpResponseRedirect(reverse('blogs:blogmanage'))


def editblog(request,blogId):
    tmpBlog = Blog.objects.get(id=blogId)
    request.session['currentblogId'] = blogId
    form = BlogForm()
    blogContent = {}
    if tmpBlog.auther.username == request.session['username']:
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
    blogList = Blog.objects.filter(auther=request.session['username'])
    commentList = []
    for blog in blogList:
        commentList.append(Comment.objects.filter(attachedblog=blog))
    return render(request,'blogs/commentmanage.html',{'commentList':commentList})


def deletecomment(request,commentId):
    comment = Comment.objects.get(id=commentId)
    attachedBlog = comment.attachedblog
    if attachedBlog.auther.username == request.session['username']:
        comment.delete()
        attachedBlog.commentcount -= 1
        attachedBlog.save()
    else:
        return render(request, 'blogs/failedoperation.html')
    return HttpResponseRedirect(reverse('blogs:commentmanage'))


def draftmanage(request):
    blogList = Blog.objects.filter(auther=request.session['username']).filter(draft=True)
    return render(request, 'blogs/draftmanage.html', {'blogList': blogList})

