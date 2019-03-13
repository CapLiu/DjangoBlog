"""myblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include
from . import views
from .views import blogSearchView
from blogsearchengine.views import baseSearchView,choiceSearchView
from blogs.models import Blog
from esengine.views import esbaseSearchView,esChoiceSearchView,esAdvanceSearchView



urlpatterns = [
    url(r'^$',views.index,name='index'),
    url(r'^ckeditor/',include('ckeditor_uploader.urls')),
    url(r'^users/',include('users.urls')),
    url(r'^blogs/',include('blogs.urls')),
    url(r'^admin/', admin.site.urls),
    #url(r'^search/', views.newsearchView,name='blogSearch'),
    #url(r'^search/$',blogSearchView(),name='blogSearch')
    #url(r'^search/$',views.searchengineview,name='blogSearch')
    #url(r'^search/$',choiceSearchView(modelname=Blog,
    #                                        searchfield=[{'content':u'全文'},{'title':u'标题'}],
    #                                        updatefield='content',
    #                                        templatename='myblog/normalsearchengine.html',
    #                                        indexname='myblogindex',resultsperpage=3),name='blogSearch')
    url(r'^simpleSearch/$',esbaseSearchView(indexname='blog',
                                            doctype='blog_content',
                                            model=Blog,
                                            searchfield='content',
                                            updatefield='content',
                                            templatename='myblog/essearch.html'),name='simpleSearch'),
    url(r'^choiceSearch/$',esChoiceSearchView(indexname='blog',
                                      doctype='blog_content',
                                      model=Blog,
                                      searchfield='content',
                                      updatefield='content',
                                      templatename='myblog/essearch.html',
                                      multichoice=True,
                                        resultsperpage=3
                                      ),name='choiceSearch'),
    url(r'^advanceSearch/$', esAdvanceSearchView(indexname='blog',
                                         doctype='blog_content',
                                         model=Blog,
                                         templatename='myblog/advancesearch.html',
                                         includelist=[{'title':u'标题'},{'content':u'正文'}],
                                         excludelist=[{'title':u'标题'},{'content':u'正文'}],
                                         resultsperpage=3,
                                         datefield='createdate'
                                         ), name='advanceSearch')

]

