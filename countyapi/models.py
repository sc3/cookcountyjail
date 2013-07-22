from django.db import models

class CountyInmate(models.Model):
    """
    Model that represents a Cook County Jail inmate.
    """
    jail_id = models.CharField(max_length=15, primary_key=True)
    url = models.CharField(max_length=255)
    race = models.CharField(max_length=4, null=True, blank=True)
    last_seen_date = models.DateTimeField(auto_now=True)
    booking_date = models.DateTimeField(null=True)
    discharge_date_earliest = models.DateTimeField(null=True)
    discharge_date_latest = models.DateTimeField(null=True)
    gender = models.CharField(max_length=1, null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    age_at_booking = models.IntegerField(null=True, blank=True)
    bail_status = models.CharField(max_length=50, null=True)
    bail_amount = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.jail_id

    class Meta:
        ordering = ['-jail_id']


class CourtDate(models.Model):
    """
    Model that represents an inmate's next court date.
    """
    inmate = models.ForeignKey('CountyInmate', related_name='court_dates')
    location = models.ForeignKey('CourtLocation', related_name='court_dates')
    date = models.DateField()

    class Meta:
        ordering = ['date']


class CourtLocation(models.Model):
    """
    Model that represents a unique court location (court house and room).
    """
    location = models.TextField()
    location_name = models.CharField(max_length=20, null=True)
    branch_name = models.CharField(max_length=60, null=True)
    room_number = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=30, null=True)
    state = models.CharField(max_length=3, null=True)
    zip_code = models.IntegerField(null=True, blank=True)


class HousingHistory(models.Model):
    """
    Model that represents an inmate's housing location on a given date.
    """
    inmate = models.ForeignKey('CountyInmate', related_name='housing_history')
    housing_location = models.ForeignKey('HousingLocation', related_name='housing_history')
    housing_date_discovered = models.DateField(null=True)


class HousingLocation(models.Model):
    """
    Model that represents a housing unit in the jail.
    """
    housing_location = models.CharField(max_length=40, primary_key=True)
    division = models.CharField(max_length=4)
    sub_division = models.CharField(max_length=20)
    sub_division_location = models.CharField(max_length=20)
    in_jail = models.NullBooleanField()
    in_program = models.CharField(max_length=60)

    def __unicode__(self):
        return self.housing_location


class ChargesHistory(models.Model):
    inmate = models.ForeignKey('CountyInmate', related_name='charges_history')
    charges = models.TextField(null=True)
    charges_citation = models.TextField(null=True)
    date_seen = models.DateField(null=True)


class InmateSummaries(models.Model):
    """
    Model that displays count of inmates in system by date
    """
    date = models.DateField(null=False)
    current_inmate_count = models.IntegerField(null=False, blank=False)
