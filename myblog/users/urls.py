from django.conf.urls import url,include
from . import views
from myblog.views import index
from blogs import views as blogViews

app_name='users'

extra_patterns = [url(r'^articlelist/$',blogViews.articlelist,name='articlelist'),]

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^userregister/$',views.userregister,name='userregister'),
    url(r'^userlogin/$',views.userlogin,name='userlogin'),
    url(r'^loginResult/(?P<info>.*)$',views.loginResult,name='loginResult'),
    url(r'^registerResult/(?P<info>.*)$',views.registerResult,name='registerResult'),
    url(r'^logoff/$',views.logoff,name='logoff'),
    url(r'^userindex/(?P<username>.*)$',views.userIndex,name='userIndex'),
    url(r'^userinfo/(?P<username>.*)$',views.userinfo,name='userinfo'),
    url(r'^messagebox/$',views.messagebox,name='messagebox'),
    url(r'^setreaded/$',views.setreaded,name='setreaded'),
    url(r'^follow/(?P<followusername>.*)$',views.follow,name='follow'),
    url(r'^migrateuser/$',views.migrateuser,name='migrateuser')
]