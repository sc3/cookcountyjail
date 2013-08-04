from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.simple import direct_to_template

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', direct_to_template, {'template': 'index.html'}),
                       url(r'^robots.txt', direct_to_template, {'template': 'robots.txt', 'mimetype':'text/plain'}),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^api/', include('countyapi.urls')))
