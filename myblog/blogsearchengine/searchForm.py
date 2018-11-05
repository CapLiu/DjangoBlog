# -*- coding=utf-8 -*-
from django import forms

class enginesearchForm(forms.Form):
    CHOICES = (('1', u'标题'), ('2', u'全文'), ('3', u'全部'))
    searchKeyword = forms.CharField(label=u'搜索', max_length=40)
    searchrange = forms.ChoiceField(label='', widget=forms.RadioSelect, choices=CHOICES,initial=2)

