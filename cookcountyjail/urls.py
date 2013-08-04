from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.simple import direct_to_template

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^api/', include('countyapi.urls')),
                       url(r'^favicon\.ico', direct_to_template, {'template': 'favicon.ico',
                                                                  'mimetype': 'image/vnd.microsoft.icon'}),
                       url(r'^$|^index\.html$', direct_to_template, {'template': 'index.html'}),
                       url(r'^robots\.txt', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'}),
                       url(r'^admin/', include(admin.site.urls))
                       )
