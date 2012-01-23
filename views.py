"""
Example Django view for receiving and decrypting datafeed.
"""
 
import os
import sys
import codecs
 
import urllib
from django.http import *
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
 
from foxyutils import FoxyData

@csrf_exempt
def foxyfeed(request):
  if request.POST and 'FoxyData' in request.POST:
    try:
      # IMPORTANT: unquote_plus is necessary for the non-ASCII binary that
      # FoxyCart sends.
      data = FoxyData.from_crypted_str(urllib.unquote_plus(request.POST['FoxyData']), settings.FOXYCART_DATAFEED_KEY)
      for transaction in data.transactions:
        # Your code goes here
        # Make sure we don't have a duplicate transaction id
        # Verify the pricing of the products
        # Add the order to the database
        pass
 
      return HttpResponse('foxy')
 
    except Exception, e:
	  # Something went wrong, handle the error...
      raise
 
  return HttpResponseForbidden('Unauthorized request.')  # No FoxyData?  Not a POST?  We don't speak that.

@csrf_exempt
def capture_foxyfeed(request):
  capture_name = "test1"
  save_request_object = True
  allow_overwrite = False
  capture_dir =  os.path.join(os.path.dirname(__file__), "fixtures")
  if save_request_object:
    capture_file_path = os.path.join(capture_dir, capture_name + '.request')
    f = open(capture_file_path, 'w')
    f.write(request.__repr__())
    f.close()
  if request.method == 'POST' and 'FoxyData' in request.POST:
    encrypted_file_path = os.path.join(capture_dir, capture_name + '.encrypted')
    plaintext_file_path = os.path.join(capture_dir, capture_name + '.plaintext')
    if not allow_overwrite:
      if os.path.exists(encrypted_file_path):
          return HttpResponseForbidden('Error: data already captured.')

    f = codecs.open(encrypted_file_path, encoding='utf-8', mode="w")
    data = request.POST['FoxyData']
    f.write(data)
    f.close()
    f = codecs.open(plaintext_file_path, encoding='utf-8', mode="w")
    f.write(FoxyData.decrypt_str(urllib.unquote_plus(data), settings.FOXYCART_DATAFEED_KEY))
    return HttpResponse('foxy')
 
  return HttpResponseForbidden('Unauthorized request.')
