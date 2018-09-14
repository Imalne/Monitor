from django.contrib import admin
from django.urls import path,re_path

from . import views
urlpatterns = [
    # re_path('index/$',views.monitor),
    re_path('index2/$',views.monitor2),
    re_path('list/$',views.stream),
    # re_path('^newFrame/$',views.newFrame),
    re_path('^signup/$',views.signUp),
    re_path('^login/$',views.login),
    re_path('^recordInfo/$',views.infoStream),
    re_path('^upimg/$',views.analysisImg),
    re_path('^chpswd/$',views.passwordChange),
    re_path('^logout/$',views.logout),
    re_path('^userpage/$',views.personPage),
    re_path('^delete/face/$',views.deleteFace),
    re_path('^delete/record/$',views.deleteRecord),
    re_path('^super/$',views.superpage),
    re_path('^adduser/$',views.addUser),
    re_path('^chrange/$',views.rangeChange),
]