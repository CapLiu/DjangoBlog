# -*- coding=utf-8 -*-
from django import forms
import datetime

class esbasesearchForm(forms.Form):
    searchKeyword = forms.CharField(label=u'搜索',max_length=40)
    def __init__(self,*args,**kwargs):
        super(esbasesearchForm,self).__init__(*args,**kwargs)


class esadvancesearchForm(forms.Form):
    def __init__(self,*args,**kwargs):
        self.searchfields = {}
        includelist = kwargs.pop('includelist',[])
        excludelist = kwargs.pop('excludelist',[])
        startyear = kwargs.pop('startyear','1900')
        endyear = kwargs.pop('endyear','2050')
        yearrange = range(int(startyear),int(endyear))
        super(esadvancesearchForm, self).__init__(*args, **kwargs)
        self.includeChoice = self.__buildSearchrange(includelist)
        self.excludeChoice = self.__buildSearchrange(excludelist)
        self.fields['includeKeyword'] = forms.CharField(label=u'包含以下关键词，以逗号分割',max_length=40,required=False)
        self.fields['includerange'] = forms.MultipleChoiceField(label='', widget=forms.CheckboxSelectMultiple,
                                                               choices=self.includeChoice, initial=1,required=False)
        self.fields['includemethod'] = forms.ChoiceField(label='',widget=forms.RadioSelect,choices=[['1',u'与'],['2',u'或']],initial='1')
        self.fields['excludeKeyword'] = forms.CharField(label=u'排除以下关键词，以逗号分割',max_length=40,required=False)
        self.fields['excluderange'] = forms.MultipleChoiceField(label='',widget=forms.CheckboxSelectMultiple,
                                                                choices=self.excludeChoice,initial=1,required=False)
        self.fields['startdate'] = forms.DateField(label=u'起始时间',widget=forms.SelectDateWidget(years=yearrange),initial=datetime.date.today)
        self.fields['enddate'] = forms.DateField(label=u'终止时间',widget=forms.SelectDateWidget(years=yearrange),initial=datetime.date.today)


    def __buildSearchrange(self,searchlist):
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


class eschoicesearchForm(forms.Form):
    def __init__(self,*args,**kwargs):
        self.searchfields = {}
        searchlist = kwargs.pop('searchlist', False)
        multichoice = kwargs.pop('multichoice',False)
        self.CHOICES = self.__buildSearchrange(searchlist)
        super(eschoicesearchForm, self).__init__(*args, **kwargs)
        if multichoice:
            self.fields['searchrange'] = forms.MultipleChoiceField(label='',widget=forms.CheckboxSelectMultiple,choices=self.CHOICES,initial=1)
        else:
            self.fields['searchrange'] = forms.ChoiceField(label='', widget=forms.RadioSelect, choices=self.CHOICES,initial=1)
        self.fields['searchKeyword'] = forms.CharField(label=u'搜索',max_length=40)
        # searchlist should be below style:
        # [{title:u'标题'},{content:u'全文'},{username:u'用户'},...,{xx:u'xx']
        # [u'aa',u'bb',u'cc']

    def __buildSearchrange(self,searchlist):
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
