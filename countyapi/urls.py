from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^day/?$', 'countyapi.views.day_summary'),
    url(r'^rows/?$', 'countyapi.views.rows_summary'),
)
