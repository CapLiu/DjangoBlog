from django.shortcuts import render
from django.views import View
from blogsearchengine.searchForm import enginebasesearchForm,enginechoicesearchForm
from blogsearchengine.engine import searchengine
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
# Create your views here.


class baseSearchView(View):

    def __init__(self,modelname,searchfield,updatefield,indexname,templatename,resultsperpage = 10):
        self.modelname = modelname
        self.searchfield = searchfield
        self.updatefield = updatefield
        self.templatename = templatename
        self.indexname = indexname
        self.keyword = ''
        self.resultsperpage = resultsperpage

    def search(self,request):
        searchresults = []
        correct_dict = {}
        self.form = enginebasesearchForm(request.GET)
        if self.form.is_valid():
            self.keyword = self.form.cleaned_data['searchKeyword']
            print('keyword data is' + self.keyword)
            engine = searchengine(self.modelname, self.updatefield, indexname=self.indexname)
            searchresults, correct_dict = engine.search(self.searchfield, self.keyword)
        return searchresults, correct_dict

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
        searchresults,correct_dict = self.search(self.request)
        page_result = self.buildpage(self.request,searchresults)
        content = {'correct':correct_dict,
                   'searchResult':page_result,
                   'searchform':self.form,
                   'searchKeyword':self.keyword
                   }
        content.update(**self.extradata())
        return render(self.request,self.templatename,content)

    def extradata(self):
        return {}


class choiceSearchView(View):
    def __init__(self,modelname,searchfield,updatefield,indexname,templatename,resultsperpage = 10):
        self.modelname = modelname
        self.searchfield = searchfield
        self.updatefield = updatefield
        self.templatename = templatename
        self.indexname = indexname
        self.keyword = ''
        self.searchrange = ''
        self.resultsperpage = resultsperpage
        #self.searchfield = searchfield

    def __call__(self, request):
        self.request = request
        return self.create_response()

    def search(self,request):
        print(self.searchfield)
        searchresults = []
        correct_dict = {}
        kwargs = {}
        kwargs['searchlist'] = self.searchfield
        # [{'content': u'全文'}, {'title': u'标题'}]
        self.form = enginechoicesearchForm(request.GET,**kwargs)
        if self.form.is_valid():
            self.keyword = self.form.cleaned_data['searchKeyword']
            print('keyword data is' + self.keyword)
            engine = searchengine(self.modelname, self.updatefield, indexname=self.indexname)
            #print('form searchfield'+self.form.searchfields)
            for key in self.form.searchfields:
                if key == self.form.cleaned_data['searchrange']:
                    searchresults, correct_dict = engine.search(self.form.searchfields[key], self.keyword)
                    self.searchrange = key
                    break
        return searchresults, correct_dict

    def create_response(self):
        searchresults,correct_dict = self.search(self.request)
        page_result = self.buildpage(self.request,searchresults)
        content = {'correct':correct_dict,
                   'searchResult':page_result,
                   'searchform':self.form,
                   'searchKeyword':self.keyword,
                   'searchRange':self.searchrange
                   }
        content.update(**self.extradata())
        return render(self.request,self.templatename,content)

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

    def extradata(self):
        return {}