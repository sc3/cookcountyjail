"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from countyapi.models import CountyInmate
import json

class APITest(TestCase):
    def test_post_create(self):
        """
        Test inmate creation via POST
        """
        c = Client()

        # Did the response work?
        response = c.post('/api/1.0/countyinmate/', \
                json.dumps({'booking_date': '2012-01-01', 'race': 'X'}), \
                content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # Did the inmate record get created?
        inmates = CountyInmate.objects.filter(race='X')
        self.assertEqual(len(inmates), 1)
        self.assertEqual(inmates[0].booking_date.isoformat(), '2012-01-01T00:00:00')

    def test_whitelist_ip(self):
        """
        Tests IP whitelisting for POST/PUT/DELETE operations. They should all
        return 401 Unauthorized HTTP responses.
        """
        inmate = CountyInmate()
        inmate.jail_id = 1
        inmate.save()

        c = Client()
        response = c.post('/api/1.0/countyinmate/', \
                json.dumps({'booking_date': '2012-01-01', 'race': 'X'}), \
                content_type='application/json', REMOTE_ADDR='127.0.0.2')
        self.assertEqual(response.status_code, 401)

        response = c.put('/api/1.0/countyinmate/1/', \
                json.dumps({'booking_date': '2012-01-01', 'race': 'X'}), \
                content_type='application/json', REMOTE_ADDR='127.0.0.2')
        self.assertEqual(response.status_code, 401)

        response = c.delete('/api/1.0/countyinmate/1/', \
                content_type='application/json', REMOTE_ADDR='127.0.0.2')
        self.assertEqual(response.status_code, 401)
