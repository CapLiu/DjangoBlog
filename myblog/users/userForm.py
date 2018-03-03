#-*- coding=utf-8 -*-
from django import forms
from django.forms import ModelForm
from .models import Users


class UserLoginForm(forms.Form):
    username = forms.CharField(label=u'用户名',max_length=40,required=True)
    password = forms.CharField(label=u'密码',widget=forms.PasswordInput,required=True)

class UserRegisterForm(ModelForm):
    class Meta:
        model = Users
        fields = ['username','password','logoimage',
                  'birthday','email','mobilephone']