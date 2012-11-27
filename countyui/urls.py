from django.conf.urls import *
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^.*', TemplateView.as_view(template_name='index.html'), name='ui'),
)
