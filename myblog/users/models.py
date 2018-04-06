# -*- coding=utf-8 -*-
from django.db import models
import datetime
from django.utils import timezone
import PIL
# Create your models here.
class Users(models.Model):
    username = models.CharField(max_length=8,primary_key=True,unique=True,verbose_name=u'用户名')
    password = models.CharField(max_length=16,verbose_name=u'密码')
    logoimage = models.ImageField(upload_to='logoimages',null=True,blank=True,verbose_name=u'头像')
    # new field
    birthday = models.DateTimeField(null=True,blank=True,verbose_name=u'生日')
    email = models.CharField(max_length=255,null=True,blank=True,verbose_name=u'电子邮件')
    mobilephone = models.CharField(max_length=11,null=True,blank=True,verbose_name=u'手机号码')
    # new field end
    registertime = models.DateTimeField(default=timezone.now())

    @classmethod
    def create(cls,username,password,birthday,email,mobilephone):
        user = cls(username=username,password=password,birthday=birthday,
                   email=email,mobilephone=mobilephone,registertime=datetime.datetime.now())
        return user

    def __unicode__(self):
        return self.username


class InfoMessage(models.Model):
    attachUser = models.ForeignKey(Users,default='',on_delete=models.CASCADE)
    content = models.CharField(max_length=128)
    isRead = models.BooleanField(default=False)
    publishtime = models.DateField(auto_now=True)

    @classmethod
    def create(cls,attachUser,content):
        info = cls(attachUser=attachUser,content=content)
        return info
