from django.conf.urls import patterns, include, url
from django.contrib import admin
import countyapi.urls

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^data/', include(countyapi.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
