# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CountyInmate'
        db.create_table('countyapi_countyinmate', (
            ('jail_id', self.gf('django.db.models.fields.CharField')(max_length=15, primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('race', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('last_seen_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('booking_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('discharge_date_earliest', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('discharge_date_latest', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('weight', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('age_at_booking', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('bail_status', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('bail_amount', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('housing_location', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
            ('charges', self.gf('django.db.models.fields.TextField')(null=True)),
            ('charges_citation', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('countyapi', ['CountyInmate'])

        # Adding model 'CourtDate'
        db.create_table('countyapi_courtdate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('inmate', self.gf('django.db.models.fields.related.ForeignKey')(related_name='court_dates', to=orm['countyapi.CountyInmate'])),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='court_dates', to=orm['countyapi.CourtLocation'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('countyapi', ['CourtDate'])

        # Adding model 'CourtLocation'
        db.create_table('countyapi_courtlocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('countyapi', ['CourtLocation'])

        # Adding model 'InmateRecordCount'
        db.create_table('countyapi_inmaterecordcount', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('record_count', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('countyapi', ['InmateRecordCount'])


    def backwards(self, orm):
        # Deleting model 'CountyInmate'
        db.delete_table('countyapi_countyinmate')

        # Deleting model 'CourtDate'
        db.delete_table('countyapi_courtdate')

        # Deleting model 'CourtLocation'
        db.delete_table('countyapi_courtlocation')

        # Deleting model 'InmateRecordCount'
        db.delete_table('countyapi_inmaterecordcount')


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
        'countyapi.inmaterecordcount': {
            'Meta': {'object_name': 'InmateRecordCount'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'record_count': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['countyapi']