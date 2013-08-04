from django.core import serializers
from django.http import HttpResponse

from models import CountyInmate


def data_json(request):
    objects = CountyInmate.objects.all()
    return HttpResponse(serializers.serialize('json', objects[:5000]),
                        content_type="application/json")

def api_index(request):
    return HttpResponse('Currently we are on version <a href="/api/1.0?format=json">1.0 of the API</a>. Have a look at the schemes and do not forget to append a format paramater to the urls. To create complex queries read about <a href="https://docs.djangoproject.com/en/dev/ref/models/querysets/">Django queries</a> and <a href="http://django-tastypie.readthedocs.org/en/latest/">Tastypie</a>. Also a have a look at the <a href="https://github.com/sc3/cookcountyjail/wiki/API-guide">Api Guide</a> for a reference on how it all translates to this project in specific. The API is changing at a high rate and the examples might be behind the current version.')
