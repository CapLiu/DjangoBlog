from django.shortcuts import render
from django.views import View
from esengine.searchForm import esbasesearchForm
from esengine.searchForm import eschoicesearchForm
from esengine.searchForm import esadvancesearchForm
from esengine.esenginecore import esengine
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
# Create your views here.


class esbaseSearchView(View):

    def __init__(self,indexname,doctype,model,searchfield,updatefield,templatename,resultsperpage = 10):
        self.indexname = indexname
        self.doctype = doctype
        self.model = model
        self.searchfield = searchfield
        self.updatefield = updatefield
        self.templatename = templatename
        self.keyword = ''
        self.resultsperpage = resultsperpage

    def search(self,request):
        searchresults = []
        self.form = esbasesearchForm(request.GET)
        if self.form.is_valid():
            self.keyword = self.form.cleaned_data['searchKeyword']
            engine = esengine(self.indexname,self.doctype,self.model)
            resultcount,searchresults = engine.basicsearch(self.indexname,self.doctype,self.searchfield,self.keyword)
        return resultcount, searchresults

    def __call__(self, request):
        self.request = request
        return self.create_response()


    def buildpage(self,request,results):
        # 引入分页机制
        paginator = Paginator(results, self.resultsperpage)
        page = request.GET.get('page')
        try:
            searchresult = paginator.page(page)
        except PageNotAnInteger:
            searchresult = paginator.page(1)
        except EmptyPage:
            searchresult = paginator.page(paginator.num_pages)
        return searchresult

    def create_response(self):
        resultcount, searchresults = self.search(self.request)
        page_result = self.buildpage(self.request,searchresults)
        content = {'resultcount':resultcount,
                   'searchResult':page_result,
                   'searchform':self.form,
                   'searchKeyword':self.keyword
                   }
        content.update(**self.extradata())
        return render(self.request,self.templatename,content)

    def extradata(self):
        return {}


class esAdvanceSearchView(View):

    def __init__(self,indexname,doctype,model,templatename,includelist,excludelist,datefield,resultsperpage = 10):
        self.indexname = indexname
        self.doctype = doctype
        self.model = model
        self.templatename = templatename
        self.keyword = ''
        self.includelist = includelist
        self.excludelist = excludelist
        self.datefield = datefield
        self.resultsperpage = resultsperpage

    def buildform(self,request):
        kwargs = {}
        #kwargs['includelist'] = [{'title':u'标题'},{'content':u'正文'}]
        #kwargs['excludelist'] = [{'title': u'标题'}, {'content': u'正文'}]
        kwargs['includelist'] = self.includelist
        kwargs['excludelist'] = self.excludelist
        self.form = esadvancesearchForm(request.GET,**kwargs)
        self.simpleform = esbasesearchForm(request.GET)

    def __call__(self, request):
        self.request = request
        return self.create_response()

    def search(self,request):
        if self.form.is_valid():
            engine = esengine(self.indexname, self.doctype, self.model)
            includekeywords = self.form.cleaned_data['includeKeyword']
            excludekeywords = self.form.cleaned_data['excludeKeyword']
            startdate = self.form.cleaned_data['startdate']
            enddate = self.form.cleaned_data['enddate']
            includefields = []
            excludefields = []
            for searchrange in self.form.cleaned_data['includerange']:
                includefields.append(self.form.searchfields[searchrange])
            for searchrange in self.form.cleaned_data['excluderange']:
                excludefields.append(self.form.searchfields[searchrange])
            totalcount,result = engine.advancesearch(self.indexname,self.doctype,includefields,
                                                     includekeywords,excludefields,excludekeywords,
                                                     self.datefield,startdate,enddate)
            print(result)
            return totalcount,result
        else:
            return 0,{}

    def buildpage(self,request,results):
        # 引入分页机制
        paginator = Paginator(results, self.resultsperpage)
        page = request.GET.get('page')
        try:
            searchresult = paginator.page(page)
        except PageNotAnInteger:
            searchresult = paginator.page(1)
        except EmptyPage:
            searchresult = paginator.page(paginator.num_pages)
        return searchresult

    def create_response(self):
        self.buildform(self.request)
        resultcount, searchresults = self.search(self.request)
        print(resultcount)
        if resultcount>0:
            page_result = self.buildpage(self.request, searchresults)
            content = {
                'simplesearchform':self.simpleform,
                'resultcount': resultcount,
                'searchResult': page_result
            }
        else:
            page_result = searchresults
            content = {
                'searchform': self.form,
            }
        content.update(**self.extradata())
        return render(self.request,self.templatename,content)

    def extradata(self):
        return {}


class esChoiceSearchView(View):

    def __init__(self,indexname,doctype,model,searchfield,updatefield,templatename,multichoice=False,resultsperpage = 10):
        self.indexname = indexname
        self.doctype = doctype
        self.model = model
        self.searchfield = searchfield
        self.updatefield = updatefield
        self.templatename = templatename
        self.keyword = ''
        self.resultsperpage = resultsperpage
        self.searchrange = None
        self.multichoice = multichoice

    def search(self,request):
        kwargs = {}
        kwargs['searchlist'] = [{'title':u'标题'},{'content':u'正文'}]
        kwargs['multichoice'] = self.multichoice
        resultcount = 0
        searchresults = []
        self.form = eschoicesearchForm(request.GET,**kwargs)

        if self.form.is_valid():
            self.keyword = self.form.cleaned_data['searchKeyword']
            engine = esengine(self.indexname,self.doctype,self.model)
            if self.multichoice:
                searchfield = []
                for searchrange in self.form.cleaned_data['searchrange']:
                    searchfield.append(self.form.searchfields[searchrange])
                resultcount, searchresults = engine.multifieldsearch(self.indexname, self.doctype,
                                                                     searchfield, self.keyword)
                self.searchrange = self.form.cleaned_data['searchrange']
                print(self.searchrange)
            else:
                for key in self.form.searchfields:
                    if key == self.form.cleaned_data['searchrange']:
                        resultcount,searchresults = engine.multifieldsearch(self.indexname,self.doctype,self.form.searchfields[key],self.keyword)
                        self.searchrange = key
                        break
        else:
            print('form is not valid')
        return resultcount, searchresults

    def __call__(self, request):
        self.request = request
        return self.create_response()


    def buildpage(self,request,results):
        # 引入分页机制
        paginator = Paginator(results, self.resultsperpage)
        page = request.GET.get('page')
        try:
            searchresult = paginator.page(page)
        except PageNotAnInteger:
            searchresult = paginator.page(1)
        except EmptyPage:
            searchresult = paginator.page(paginator.num_pages)
        return searchresult

    def create_response(self):
        resultcount,searchresults = self.search(self.request)
        if type(self.searchrange) == list:
            total_searchrange = ''
        else:
            total_searchrange = self.searchrange
        for singlerange in self.searchrange:
            if total_searchrange != '':
                total_searchrange += '&'
            searchrange = 'searchrange=%s' % singlerange
            total_searchrange += searchrange
        print(total_searchrange)
        page_result = self.buildpage(self.request,searchresults)
        content = {'resultcount':resultcount,
                   'searchResult':page_result,
                   'searchform':self.form,
                   'searchKeyword':self.keyword,
                   'searchRange':total_searchrange
                   }
        content.update(**self.extradata())
        return render(self.request,self.templatename,content)

    def extradata(self):
        return {}