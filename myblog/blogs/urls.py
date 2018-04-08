from django.conf.urls import url
from . import views
from django.conf.urls import include
from users import urls as userurls



app_name='blogs'
urlpatterns = [
    url(r'^(?P<blogId>[0-9]*)$', views.content, name='content'),
    url(r'^addblog/$', views.addBlog, name='addblog'),
    url(r'^addblogResult/(?P<info>.*)$', views.addBlogResult, name='addblogResult'),
    url(r'^saveDraft/$',views.saveDraft,name='saveDraft'),
    url(r'^saveComment/$',views.saveComment,name='saveComment'),
    url(r'^thumbup/$',views.thumbup,name='thumbup'),
    # blog manage
    url(r'^articleList/$',views.articlelist,name='articlelist'),
    url(r'^blogmanage$',views.blogmanage,name='blogmanage'),
    url(r'^deleteblog/(?P<blogId>.*)$',views.deleteblog,name='deleteBlog'),
    url(r'^editblog/(?P<blogId>.*)$',views.editblog,name='editBlog'),
    url(r'^commentmanage$',views.commentmanage,name='commentmanage'),
    url(r'^deletecomment/(?P<commentId>.*)$',views.deletecomment,name='deleteComment'),
    url(r'^draftmanage$',views.draftmanage,name='draftmanage'),


]