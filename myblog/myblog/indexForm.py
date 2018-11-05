# -*- coding=utf-8 -*-
from django import forms
from haystack.forms import SearchForm

class mysearchForm(forms.Form):
    searchKeyword = forms.CharField(label=u'搜索',max_length=40)