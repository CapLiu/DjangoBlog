# -*- coding=utf-8 -*-
from django import forms

class enginebasesearchForm(forms.Form):
    searchKeyword = forms.CharField(label=u'搜索',max_length=40)
    def __init__(self,*args,**kwargs):
        super(enginebasesearchForm,self).__init__(*args,**kwargs)

class enginechoicesearchForm(forms.Form):
    def __init__(self,*args,**kwargs):
        self.searchfields = {}
        searchlist = kwargs.pop('searchlist', False)
        self.CHOICES = self.__buildSearchrange(searchlist)
        super(enginechoicesearchForm, self).__init__(*args, **kwargs)
        self.fields['searchrange'] = forms.ChoiceField(label='',widget=forms.RadioSelect,choices=self.CHOICES,initial=1)
        self.fields['searchKeyword'] = forms.CharField(label=u'搜索',max_length=40)
        # searchlist should be below style:
        # [{title:u'标题'},{content:u'全文'},{username:u'用户'},...,{xx:u'xx']
        # [u'aa',u'bb',u'cc']


    def __buildSearchrange(self,searchlist):
        print(searchlist)
        searchrange = []
        i = 1
        for choice in searchlist:
            if type(choice) == str:
                subrange = []
                subrange.append(str(i))
                subrange.append(choice)
                i = i + 1
                searchrange.append(subrange)
            elif type(choice) == dict:
                for key in choice:
                    subrange = []
                    subrange.append(str(i))
                    subrange.append(choice[key])
                    self.searchfields[str(i)] = key
                    i = i + 1
                    searchrange.append(subrange)
        return searchrange
