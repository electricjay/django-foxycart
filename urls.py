from django.conf.urls.defaults import *

urlpatterns = patterns('foxycart.views',
                       url(r'^xmlfeed/$', 'foxyfeed'),
                       url(r'^xmlcapture/$', 'capture_foxyfeed'),
                       )
