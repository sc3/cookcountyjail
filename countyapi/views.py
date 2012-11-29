from django.http import HttpResponse
import json
from countyapi.models import CountyInmate

def rows_summary(request):
    response = json.dumps({
        'rows': CountyInmate.objects.count(),
    })
    return HttpResponse(response, content_type="application/json")


def day_summary(request):
    """ Summarize inmate population by day. """
    context = {}

    # @TODO: Summarize by day

    response = json.dumps(context)
    callback = request.GET.get('callback')
    if callback:
        response = "%s(%s)" % (callback, response)
    return HttpResponse(response, content_type="application/json")

