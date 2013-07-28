# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
#from countyapi.management.commands.utils import process_housing_location
import logging

class Migration(DataMigration):

    def forwards(self, orm):
        log = logging.getLogger('main')
        # Query all inmates with an empty hosing_history
        for inmate in orm.CountyInmate.objects.all().exclude(housing_history__isnull=False): # Iterate through each one
            housing_location, created_location = orm.HousingLocation.objects.get_or_create(housing_location=inmate.housing_location) # create a new housing_location record on the latest table with the inmates housing location
            #process_housing_location(housing_location) # process it as any other location
            housing_history, new_history = inmate.housing_history.get_or_create(housing_location=housing_location) # New housing_history record with the inmate's housing location
            housing_history.housing_date = inmate.last_seen_date.date() # set the date to the latest possible day that inmate was moved there 
            # save it all 
            housing_location.save()
            housing_history.save()
            inmate.save()
        # Minor Audit to make sure all matches, might want to comment out with a huge database
        for inmate in orm.CountyInmate.objects.all():
            history_count = len(inmate.housing_history.all()) # Used for indexing because housing history doesn't support negative indexing ex: list[-1]
            if history_count > 0:
                # if the inmate has a housing_history but the latest one is not the same as the inmate's housing_location then there is trouble
                if inmate.housing_history.all()[history_count - 1].housing_location.housing_location != inmate.housing_location: 
                    if inmate.housing_location == None or inmate.housing_location == '':
                        # Happens when proccess_housing_location sets None locations to unknown and the inmate's scraper keeps is as None or some as ''
                        log.debug("Conflicting housing location: %s and history location: %s with inmate: %s. Possibly because housing location is 'None'" % (inmate.housing_location, inmate.housing_history.all()[history_count -1].housing_location.housing_location, inmate.jail_id)) 
                    else:
                        # there is a bigger issue 
                        log.debug("Unknown case with conflicting housing location: %s and history location: %s with inmate: %s." % (inmate.housing_location, inmate.housing_history.all()[history_count -1].housing_location.housing_location, inmate.jail_id))
    def backwards(self, orm):
        "Write your backwards methods here."
        log = logging.getLogger('main')
        for inmate in orm.CountyInmate.objects.all():
            history_count = len(inmate.housing_history.all()) 
            if history_count > 0:
                inmate.housing_location = inmate.housing_history.all()[history_count -1 ].housing_location.housing_location
                inmate.save()

    models = {
        'countyapi.countyinmate': {
            'Meta': {'ordering': "['-jail_id']", 'object_name': 'CountyInmate'},
            'age_at_booking': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'bail_amount': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'bail_status': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'booking_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'charges': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'charges_citation': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'discharge_date_earliest': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'discharge_date_latest': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'housing_location': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'jail_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'primary_key': 'True'}),
            'last_seen_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'race': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'countyapi.courtdate': {
            'Meta': {'ordering': "['date']", 'object_name': 'CourtDate'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inmate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'court_dates'", 'to': "orm['countyapi.CountyInmate']"}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'court_dates'", 'to': "orm['countyapi.CourtLocation']"})
        },
        'countyapi.courtlocation': {
            'Meta': {'object_name': 'CourtLocation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.TextField', [], {})
        },
        'countyapi.housinghistory': {
            'Meta': {'object_name': 'HousingHistory'},
            'housing_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'housing_location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'housing_history'", 'to': "orm['countyapi.HousingLocation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inmate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'housing_history'", 'to': "orm['countyapi.CountyInmate']"})
        },
        'countyapi.housinglocation': {
            'Meta': {'object_name': 'HousingLocation'},
            'division': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'housing_location': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'}),
            'in_jail': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'in_program': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'sub_division': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'sub_division_location': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['countyapi']
    symmetrical = True
