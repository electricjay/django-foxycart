"""
Unit test for foxycart.py.
"""
 
import os
import sys
import codecs
import urllib

from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings
import unittest

from foxyutils import *
import views
 
class Constants:
  pass
 
class FoxyDataVectorTest(unittest.TestCase):
  def _get_test_data(self, filename):
    f = codecs.open(os.path.join(os.path.dirname(__file__), "fixtures", filename),
                    encoding='UTF-8', mode="r")
    data = f.read()
    f.close()
    return data

  def _test_it_hard(self, vector):
    self.assertEqual(1, len(vector), 'expected one transaction')
 
    tx = vector.transactions[0]
    self.assertEqual('616', tx.id)
    self.assert_(tx.date)
    self.assertEqual("2007-05-04 20:53:57", tx.date.strftime(FoxyData.DateTimeFmt))
    self.assertEqual('122', tx.customer_id)
 
    self.assertEqual(1, len(tx.items), 'expected one item')
    self.assertEqual(2, len(tx.custom_fields), 'expected 2 custom fields')
    self.assert_('My_Cool_Text' in tx.custom_fields.keys(), 'missing custom field')
    self.assertEqual('Value123', tx.custom_fields['My_Cool_Text'], 'missing custom field value')
 
 
    self.assert_('Another_Custom_Field' in tx.custom_fields.keys(), 'missing custom field')
    self.assertEqual('10', tx.custom_fields['Another_Custom_Field'], 'missing custom field value')
 
    item = tx.items.pop()

    self.assertEqual('abc123', item['product_code'])
 
    detail = item['detail']
    self.assertEqual(1, len(detail))
    self.assertEqual('blue', detail['color'])
 
    self.assert_(item['subscription_startdate'])
    self.assertEqual('2007-07-07', item['subscription_startdate'].strftime(FoxyData.DateFmt), 'subscription date error')
    self.assert_(item['next_transaction_date'])
    self.assertEqual('2007-08-07', item['next_transaction_date'].strftime(FoxyData.DateFmt), 'transaction date error')
 
# These methods test the parsing of the prepackaged test data: "testdata.xml"
  def test_from_str(self):
    vector = FoxyData.from_str(self._get_test_data("testdata.xml"))
    self._test_it_hard(vector)
 
  def test_from_crypted_str(self):
    crypted_str = ARC4(Constants.SECRET_KEY).crypt(self._get_test_data("testdata.xml"))
    vector = FoxyData.from_crypted_str(crypted_str, Constants.SECRET_KEY)
    self._test_it_hard(vector)
 
  # The following methods contain the tests that excersise your views code
  # You will need to provide captured data from the foxycart feed in order 
  # to test properly.  See the capture_foxyfeed view for data capture.
  def test_sucessfull_order(self):
    self.assertFalse(True,
                     "Update the test_successfull_order method with your testdata")
    crypted_data = self._get_test_data("yourtestdata.encrypted")
    c = Client()
    response = c.post('/foxycart/xmlfeed/', { "FoxyData" : crypted_data })
    self.assertEqual(response.content, "foxy", "View for xmlfeed did not return foxy")
    # This would be a good place to check that the order got properly added to the
    # database

  def test_duplicated_order(self):
    self.assertFalse(True,
                     "Update the test_duplicated_order method with your testdata")
    crypted_data = self._get_test_data("yourtestdata.encrypted")
    c = Client()
    response = c.post('/foxycart/xmlfeed/', { "FoxyData" : crypted_data })
    self.assertEqual(response.content, "foxy", "View for xmlfeed did not return foxy")
    response = c.post('/foxycart/xmlfeed/', { "FoxyData" : crypted_data })
    self.assertNotEqual(response.content, "foxy", "Duplicated order was accepted when it should have been rejected")

  def test_corrupted_order(self):
    # Edit the data from your successfull_order test to give it errors.
    # suggested errors to add: wrong price, bad product ID
    self.assertFalse(True,
                     "Update the test_corrupted_order method with your testdata")
    self.assertNotEqual("", settings.FOXYCART_DATAFEED_KEY, "FOXYCART_DATAFEED_KEY is not set - should be set in settings.py")
    data = self._get_test_data("yourcorruptedorder.plaintext")
    crypted_data = ARC4(settings.FOXYCART_DATAFEED_KEY).crypt(data)
    c = Client()
    response = c.post('/foxycart/xmlfeed/', { "FoxyData" : 
                                              urllib.quote_plus(crypted_data) })
    self.assertNotEqual(response.content, "foxy",
                        "View for xmlfeed returned foxy for corrupted data")


Constants.SECRET_KEY = 'abc123akp8ak7898a,.aoeueaouaoeuaoeu'
 
if __name__ == '__main__':
  unittest.main()
