from mock import Mock, call
from countyapi.charges import Charges

class TestCharges:

    """ 
        Tests Charges class. Things to check:

        - if the raw charge is empty, don't create anything
        - if the raw charge isn't empty and there's no past charge, add it
        - if the raw charge is different than the current one, add a new charge
        - if the raw charge is the same as the current one, don't create anything

        Resources to fake:

        - inmate_details
            - inmate_details.charges()
        - django_inmate
            - inmate.charges_history.all()
            - inmate.charges_history.latest('foo')
            - inmate.charges_history.create(bar, baz)
        - django_charge
            - charge.charges
            - charge.charges_citation
            - charge.date_seen
        - monitor
            - monitor.debug()

    """

    def test_empty_raw_charge_has_no_result(self):

        fake_inmate_details = Mock()
        fake_inmate_details.charges.return_value = ''

        fake_django_inmate = Mock()
        fake_django_inmate.charges_history.all.return_value = ['']
        fake_django_inmate.charges_history.latest.return_value = ''

        fake_monitor = Mock()

        charge_under_test = Charges(fake_django_inmate, fake_inmate_details, fake_monitor)
        charge_under_test.save()

        assert not fake_django_inmate.charges_history.create.called


    def test_same_raw_charge_has_no_result(self):

        fake_inmate_details = Mock()
        fake_inmate_details.charges.return_value = \
                '720 ILCS 5 12-3.2(a)(2) [10418\r\n\t  DOMESTIC BTRY/PHYSICAL CONTACT'

        fake_current_charge = Mock()
        fake_current_charge.charges = 'DOMESTIC BTRY/PHYSICAL CONTACT'
        fake_current_charge.charges_citation = '720 ILCS 5 12-3.2(a)(2) [10418'

        fake_django_inmate = Mock()
        fake_django_inmate.charges_history.all.return_value = [fake_current_charge]
        fake_django_inmate.charges_history.latest.return_value = fake_current_charge

        fake_monitor = Mock()

        charge_under_test = Charges(fake_django_inmate, fake_inmate_details, fake_monitor)
        charge_under_test.save()
        
        assert not fake_django_inmate.charges_history.create.called


    def test_no_past_charge_results_in_new_charge(self):

        fake_inmate_details = Mock()
        fake_inmate_details.charges.return_value = \
                '720 ILCS 5 12-3.2(a)(2) [10418\r\n\t  DOMESTIC BTRY/PHYSICAL CONTACT'

        fake_django_inmate = Mock()
        fake_django_inmate.charges_history.all.return_value = []

        fake_monitor = Mock()        

        charge_under_test = Charges(fake_django_inmate, fake_inmate_details, fake_monitor)
        charge_under_test.save()

        assert fake_django_inmate.charges_history.create.called


    def test_different_raw_charge_results_in_new_charge(self):

        fake_inmate_details = Mock()
        fake_inmate_details.charges.return_value = \
                '720 ILCS 5 12-3.2(a)(2) [10418\r\n\t  DOMESTIC BTRY/PHYSICAL CONTACT'

        fake_current_charge = Mock()
        fake_current_charge.charges = 'THEFT CONTROL INTENT'
        fake_current_charge.charges_citation = '720 ILCS 5 16-1(a)(1)(A) [1114'
        
        fake_django_inmate = Mock()
        fake_django_inmate.charges_history.all.return_value = [fake_current_charge]
        fake_django_inmate.charges_history.latest.return_value = fake_current_charge

        fake_monitor = Mock()

        charge_under_test = Charges(fake_django_inmate, fake_inmate_details, fake_monitor)
        charge_under_test.save()

        fake_django_inmate.charges_history.create.assert_called_with(
            charges='DOMESTIC BTRY/PHYSICAL CONTACT', 
            charges_citation='720 ILCS 5 12-3.2(a)(2) [10418')


