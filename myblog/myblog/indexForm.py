# -*- coding=utf-8 -*-
from django import forms

class searchForm(forms.Form):
    searchContext = forms.CharField(label=u'搜索',max_length=40)