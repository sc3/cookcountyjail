from django.http import HttpResponse
import json

def day_summary(request):
    """ Summarize inmate population by day. """
    context = {}

    # @TODO: Summarize by day

    response = json.dumps(context)
    callback = request.GET.get('callback')
    if callback:
        response = "%s(%s)" % (callback, response)

    return HttpResponse(response, content_type="application/json")
