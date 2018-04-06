# -*- coding=utf-8 -*-
from django.db import models
from users.models import Users
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils import timezone

# Create your models here.
class Category(models.Model):
    categoryname = models.CharField(max_length=8,unique=True)
    blogcount = models.IntegerField()

    def __unicode__(self):
        return self.categoryname


class Blog(models.Model):
    title = models.CharField(max_length=32,verbose_name=u'标题')
    auther = models.ForeignKey(Users,default='',on_delete=models.CASCADE)
    category = models.ForeignKey(Category,null=True,on_delete=models.CASCADE)
    content = RichTextUploadingField(verbose_name=u'内容')
    createdate = models.DateTimeField('Create time',default=timezone.now())
    modifydate = models.DateTimeField('Modify time',default=timezone.now())
    readcount = models.IntegerField(default=0)
    # Add comment count
    commentcount = models.IntegerField(default=0,null=True,blank=True)
    draft = models.BooleanField(default=True)

    @classmethod
    def create(cls,title,authername,category,content,createdate,modifydate):
        blog = cls(title=title,auther=authername,category=category,content=content,createdate=createdate,modifydate=modifydate)
        return blog

    def __unicode__(self):
        return self.title


class Comment(models.Model):
    attachedblog = models.ForeignKey(Blog,on_delete=models.CASCADE)
    content = models.TextField()
    auther = models.ForeignKey(Users,default='',on_delete=models.CASCADE)
    createtime = models.DateTimeField('Comment Create time')

    @classmethod
    def create(cls,attachedblog,content,authername,createtime):
        comment = cls(attachedblog=attachedblog,auther=authername,content=content,createtime=createtime)
        return comment

    def __unicode__(self):
        return self.content


