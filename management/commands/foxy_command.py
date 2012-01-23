"""
A tool that allows you to send commands to the foxycart api
"""

# Copyright (C) 2012 Jay Cox <jaycox@linear3d.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import urllib2
import urllib
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# It should be noted that this code is succeptable to man in the middle attacks due
# to sending the https request via urllib2 which does not verify certificates.
# Certificate verification should be added as described here:
# http://thejosephturner.com/blog/2011/03/19/https-certificate-verification-in-python-with-urllib2/

# foxycart commands from the .72 API
# see http://wiki.foxycart.com/v/0.7.2/api
foxy_commands = [
    # Store Methods
    { 'command':'store_template_cache',
      'help':'This method will use our "automagicache" automatic template caching programmatically. On success, the store\'s template will be updated, and the corresponding URL will also be saved.',
      'required_arguments':[{'name':'template_type',
                          'info':'Accepts cart, checkout, receipt, html_email, email'
                          }],
      'optional_arguments':[{'name':'template_url',
                          'info':'A complete, well-formed URL, such as http://example.tld/path/to/template.ext. If omitted, the existing URL stored in the admin (for the template_type as passed in) will be used.'},
                         {'name':'email_subject',
                          'info':'A text string to be used for email receipts. Only valid if template_type is html_email or email.'},
                         {'name':'send_html_email',
                          'info':'Accepts a 1 or 0. To use text only email receipts, send a 0. To have both text and html emails sent, set to 1. Note that this corresponds to the radio button in the admin. If this is a 1, you should have a html_email template configured.'}
                         ]}, 
    { 'command':'store_includes_get',
      'help':'Returns the FoxyCart javascript (and other required javascript or CSS files) for the store\'s version of FoxyCart. This is also available in the admin under the "sample code" section.  WARNING: This call should not be run on every pageload on your site. If you use this, cache it locally so you can serve your pages quickly and without needing to make an external request to the FoxyCart API. For the performance of our entire system, we may have to deny access for any stores that make excessive calls to this method.',
      'required_arguments':[],
      'optional_arguments':[{'name':'javascript_library',
                          'info':'Accepts none and jquery. If you\'re already loading jQuery elsewhere in your site, you can set this to none and the code returned will not include jQuery. Note that the foxycart.js files do require jQuery.'},
                         {'name':'cart_type',
                          'info':'Accepts none, colorbox. This parameter determines how the cart will function by default. If you don\'t want the default Colorbox-powered cart, set this to none.'}]
      }, 
    { 'command':'attribute_save',
      'help':'This API method allows you to attach name/value pairs to customer, transaction, or subscription records. These values can then be used for filtering, so you could attach fulfillment status to transactions in FoxyCart, then query against the data directly in FoxyCart',
      'required_arguments':[{'name':'name',
                          'info':''},
                         {'name':'value',
                          'info':''},
                         {'name':'type',
                          'info':'Accepts transaction, customer, subscription'},
                         {'name':'identifier',
                          'info':' Accepts a valid transaction_id, customer_id, sub_token, sub_token_url (depending on what was passed in as the type)'}],
      'optional_arguments':[{'name':'append',
                          'info':'Accepts 0 (default), 1. If 1, the value will be appended to the existing value for any matched name attributes. If 0 or left blank, all <attribute> nodes will be replaced with the value set.'}]
      }, 
    { 'command':'attribute_list',
      'help':'',
      'required_arguments':[{'name':'type',
                          'info':'Accepts transaction, customer, subscription'},
                         {'name':'identifier',
                          'info':'Accepts a valid transaction_id, customer_id, sub_token, sub_token_url (depending on what w\
as passed in as the type)'}],
      'optional_arguments':[]
      }, 
    { 'command':'attribute_delete',
      'help':'deletes the specified attribute.',
      'required_arguments':[{'name':'type',
                          'info':'Accepts transaction, customer, subscription'},
                         {'name':'identifier',
                          'info':'Accepts a valid transaction_id, customer_id, sub_token, sub_token_url (depending on what w\
as passed in as the type)'}],
      'optional_arguments':[{'name':'name',
                          'info':'If passed in, all attribute values for this named/value pair will be deleted. If name is not passed in, all is required.'},
                         {'name':'all',
                          'info':'Accepts 0 (default), 1. If 1 is passed in, all attributes (ie. all names) will be removed for the specified record. If all is not set to 1, a name value will be required. If both all and a name are passed in, the all will take precedence.'}]
      }, 
    { 'command':'category_list',
      'help':'returns XML with id, code, description, and product_delivery_type for all categories.',
      'required_arguments':[],
      'optional_arguments':[]
      }, 
    { 'command':'downloadable_list',
      'help':'returns XML with id, category_id, category_code, product_name, product_code, product_price, file_size, and upload_date for all downloadables.',
      'required_arguments':[],
      'optional_arguments':[]
      }, 
    # Customer Methods
    { 'command':'customer_get',
      'help':'Requires either customer_id or customer_email to be passed.  Cannot be used to retrieve guest customer accounts',
      'required_arguments':[],
      'optional_arguments':[{'name':'customer_id',
                          'info':''},
                         {'name':'customer_email',
                          'info':''}]
      }, 
    { 'command':'customer_save',
      'help':'Requires either customer_id or customer_email to be passed.  customer_password or customer_password_hash is required for a customer_save action if the customer record is a new record (but is not required for updating an existing record).  customer_password_salt may be required depending on your store\'s password hashing settings.  customer_country should be considered required, and must be a valid 2 character ISO country code. If a customer_country isn\'t provided, the store\'s country (pulled from the store settings) will be used instead.',
      'required_arguments':[],
      'optional_arguments':[{'name':'customer_id',
                          'info':''},
                         {'name':'customer_email',
                          'info':''},
                         {'name':'customer_password',
                          'info':''},
                         {'name':'cusstomer_password_hash',
                          'info':''},
                         {'name':'customer_password_salt',
                          'info':''},
                         {'name':'customer_country',
                          'info':''}
                         ]
      }, 
    { 'command':'customer_list',
      'help':'Use an asterisk (*) when filtering to do partial matches.',
      'required_arguments':[],
      'optional_arguments':[{'name':'customer_id_filter',
                          'info':''},
                         {'name':'customer_email_filter',
                          'info':''},
                         {'name':'customer_first_name_filter',
                          'info':''},
                         {'name':'customer_last_name_filter',
                          'info':''},
                         {'name':'customer_state_filter',
                          'info':''}]
      }, 
    { 'command':'customer_address_get',
      'help':'Only applicable for stores using multi-ship.  Requires customer_id or customer_email',
      'required_arguments':[],
      'optional_arguments':[{'name':'customer_id',
                          'info':''},
                         {'name':'customer_email',
                          'info':''}]
      }, 
    { 'command':'customer_address_save',
      'help':'Only applicable for stores using multi-ship.  Requires customer_id or customer_email',
      'required_arguments':[],
      'optional_arguments':[{'name':'customer_id',
                          'info':''},
                         {'name':'customer_email',
                          'info':''}]
      },
    # Transaction Methods
    { 'command':'transaction_get',
      'help':'',
      'required_arguments':[{'name':'transaction_id',
                          'info':''}],
      'optional_arguments':[]
      }, 
    { 'command':'transaction_list',
      'help':'Use an asterisk (*) when filtering to do partial matches.',
      'required_arguments':[],
      'optional_arguments':[{'name':'transaction_date_filter_begin',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'transaction_date_filter_end',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'is_test_filter',
                          'info':' (0 or 1)'},
                         {'name':'hide_transaction_filter',
                          'info':' (0 or 1)'},
                         {'name':'data_is_fed_filter',
                          'info':' (0 or 1)'},
                         {'name':'id_filter',
                          'info':''},
                         {'name':'order_total_filter',
                          'info':''},
                         {'name':'coupon_code_filter',
                          'info':''},
                         {'name':'customer_id_filter',
                          'info':''},
                         {'name':'customer_email_filter',
                          'info':''},
                         {'name':'customer_first_name_filter',
                          'info':''},
                         {'name':'customer_last_name_filter',
                          'info':''},
                         {'name':'customer_state_filter',
                          'info':''},
                         {'name':'shipping_state_filter',
                          'info':''},
                         {'name':'customer_ip_filter',
                          'info':''},
                         {'name':'product_code_filter',
                          'info':''},
                         {'name':'product_name_filter',
                          'info':''},
                         {'name':'product_option_name_filter',
                          'info':''},
                         {'name':'product_option_value_filter',
                          'info':''},
                         {'name':'custom_field_name_filter',
                          'info':''},
                         {'name':'custom_field_value_filter',
                          'info':'allow filtering based on transaction (not product) custom fields (as entered on the checkout).'}]
      }, 
    { 'command':'transaction_modify',
      'help':'Changing this bit has no impact on anything other than the value of this bit. (ie. It does not tell FoxyCart to refeed the datafeed to your endpoint)',
      'required_arguments':[],
      'optional_arguments':[{'name':'data_is_fed',
                          'info':'(0 or 1)'},
                         {'name':'hide_transaction',
                          'info':'(0 or 1)'}]
      }, 
    { 'command':'transaction_datafeed',
      'help':'Triggers a refeed of the transaction datafeed for the specified transaction.',
      'required_arguments':[{'name':'transaction_id',
                          'info':''}],
      'optional_arguments':[]
      }, 
    # Subscriptions API
    { 'command':'subscription_get',
      'help':'',
      'required_arguments':[{'name':'sub_token',
                          'info':'either the token by itself or the complete sub_token URL'}],
      'optional_arguments':[]
      }, 
    { 'command':'subscription_cancel',
      'help':'Sets the sub_enddate to the next day, effectively canceling the subscription. This way the subscription cancellation will still be included in the Subscription XML Datafeed. To deactivate a subscription immediately you can use the subscription_modify method.',
      'required_arguments':[{'name':'sub_token',
                          'info':'either the token by itself or the complete sub_token URL'}],
      'optional_arguments':[]
      }, 
    { 'command':'subscription_modify',
      'help':'',
      'required_arguments':[{'name':'sub_token',
                          'info':'either the token by itself or the complete sub_token URL'}],
      'optional_arguments':[{'name':'start_date',
                          'info':'(YYYY-MM-DD) (The start_date is somewhat historical, and indicates the very first date a subscription processed.)'},
                         {'name':'end_date',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'next_transaction_date',
                          'info':'(YYYY-MM-DD) (The next_transaction_date is reset with every subscription processing, whether successful or erroring.)'},
                         {'name':'frequency',
                          'info':''},
                         {'name':'past_due_amount',
                          'info':'decimal'},
                         {'name':'is_active',
                          'info':'(0, 1)'},
                         {'name':'transaction_template',
                          'info':''}]
      }, 
    { 'command':'subscription_list',
      'help':'Use an asterisk (*) when filtering to do partial matches.',
      'required_arguments':[],
      'optional_arguments':[{'name':'is_active_filter',
                          'info':''},
                         {'name':'frequency_filter',
                          'info':''},
                         {'name':'past_due_amount_filter',
                          'info':'(if you include this filter and give it a value (such as 1) it will return subscriptions with past due amounts greater than 0)'},
                         {'name':'start_date_filter_begin',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'start_date_filter_end',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'next_transaction_date_filter_begin',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'next_transaction_date_filter_end',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'end_date_filter_begin',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'end_date_filter_end',
                          'info':'(YYYY-MM-DD)'},
                         {'name':'paypal_profile_id_filter',
                          'info':'(for PayPal Express Checkout recurring payments) You can enter "all" to view all subscriptions with a PayPal Profile ID'},
                         {'name':'last_transaction_id_filter',
                          'info':''},
                         {'name':'customer_id_filter',
                          'info':''},
                         {'name':'customer_email_filter',
                          'info':''},
                         {'name':'customer_first_name_filter',
                          'info':''},
                         {'name':'customer_last_name_filter',
                          'info':''},
                         {'name':'product_code_filter',
                          'info':''},
                         {'name':'product_name_filter',
                          'info':''},
                         {'name':'product_option_name_filter',
                          'info':''},
                         {'name':'product_option_value_filter',
                          'info':''},
                         {'name':'custom_field_name_filter',
                          'info':'allow filtering based on subscription\'s transaction (not product) custom fields (as entered on the checkout).'},
                         {'name':'custom_field_value_filter',
                          'info':'allow filtering based on subscription\'s transaction (not product) custom fields (as entered on the checkout).'}]
      }, 
    { 'command':'subscription_datafeed',
      'help':'Passing the subscription_datafeed as the api_action to the API endpoint will immediately re-feed the Subscription XML Datafeed to your already configured XML datafeed endpoint',
      'required_arguments':[],
      'optional_arguments':[]
      }
    ]

class Command(BaseCommand):
    args = 'command [help] [option=value]...'
    help = 'Sends a command to the foxycart api'
    def send_foxy_command(self, action, data = {}):
        data["api_token"] = settings.FOXYCART_DATAFEED_KEY
        data["api_action"] = action
        encoded_data = urllib.urlencode( data )
        response = urllib2.urlopen(settings.FOXYCART_API_URL + '/api', encoded_data)
        html = response.read()
        return html

    def find_command(self, command):
        for c in foxy_commands:
            if c['command'] == command:
                return c
        return None

    def command_accepts_argument(self, command, arg):
        for a in command['required_arguments']:
            if a['name'] == arg:
                return True
        for a in command['optional_arguments']:
            if a['name'] == arg:
                return True
        return False

    def args_to_dictionary(self, args):
        d = {}
        for item in args:
            l = item.split('=', 1)
            if len(l) != 2:
                self.stdout.write("Error in arguments: arguments must be in the form of argument=value")
            else:
                d[l[0]] = l[1]
        return d

    def print_help_for_command(self, command):
        self.stdout.write("foxy_command: {0}\n".format(command["command"]))
        self.stdout.write("    {0}\n".format(command["help"]))
        if command['required_arguments']:
            self.stdout.write("      Required arguments:\n")
            for a in command['required_arguments']:
                self.stdout.write("        {0} : {1}\n".format(a["name"], a["info"]))
        if command['optional_arguments']:
            self.stdout.write("      Optional arguments:\n")
            for a in command['optional_arguments']:
                self.stdout.write("        {0} : {1}\n".format(a["name"], a["info"]))

    def handle(self, *args, **options):
        if len(args) == 0 or args[0] == 'help':
            self.stdout.write("Usage: foxy_command command [help | command options]\n")
            self.stdout.write("  Available commands (Foxycart API .72):\n")
            for command in foxy_commands:
                self.stdout.write("    {0}\n".format(command["command"]))
            return

        command = self.find_command(args[0])

        if not command:
            self.stdout.write("command '{0}' not found.\n".format(args[0]))
            return

        
        if len(args) == 2 and args[1] == 'help':
            self.print_help_for_command(command)
            return

        args_d = self.args_to_dictionary(args[1:])

        # Check that we have all required fields
        for a in command['required_arguments']:
            if not a['name'] in args_d:
                self.stdout.write("required argument '{0}' must be supplied.\n".format(a['name']))
                return
                
        # Check that all arguments are valid for the command
        for a in args_d:
            if not self.command_accepts_argument(command, a):
                self.stdout.write("Unknown argument '{0}'\n".format(a))
                return
        try:
            response = self.send_foxy_command(command['command'], args_d)
        except Exception, e:
            self.stdout.write(e.__str__())
            raise CommandError("Error sending command to foxycart server")
        self.stdout.write(response)
        # Should parse the XML and figure out if it was successfull or an error
