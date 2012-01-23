"""
Utilities for decrypting and parsing a FoxyCart datafeed.
"""
from xml.dom.minidom import parseString
from datetime import datetime
 
# Thanks, Wikipedia: http://en.wikipedia.org/wiki/RC4#Implementation
class ARC4:
    def __init__(self, key = None):
        self.state = range(256) # Initialize state array with values 0 .. 255
        self.x = self.y = 0 # Our indexes. x, y instead of i, j
 
        if key is not None:
            self.init(key)
 
    # KSA
    def init(self, key):
        for i in range(256):
            self.x = (ord(key[i % len(key)]) + self.state[i] + self.x) & 0xFF
            self.state[i], self.state[self.x] = self.state[self.x], self.state[i]
        self.x = 0
 
    # PRGA
    def crypt(self, input):
        output = [None]*len(input)
        for i in xrange(len(input)):
            self.x = (self.x + 1) & 0xFF
            self.y = (self.state[self.x] + self.y) & 0xFF
            self.state[self.x], self.state[self.y] = self.state[self.y], self.state[self.x]
            r = self.state[(self.state[self.x] + self.state[self.y]) & 0xFF]
            output[i] = chr(ord(input[i]) ^ r)
        return ''.join(output)
 
 
class FoxyData:
  DateFmt = '%Y-%m-%d'
  DateTimeFmt = '%Y-%m-%d %H:%M:%S'
 
  class Transaction:
    def __init__(self, node):
      def extract_kv_node(node, key_name):
        el = node.getElementsByTagName(key_name)
        return len(el) > 0 and el[0].firstChild.data or ''
 
      self.id = extract_kv_node(node, 'id')
      self.date = datetime.strptime(
       extract_kv_node(node, 'transaction_date'), FoxyData.DateTimeFmt)
      self.customer_id = extract_kv_node(node, 'customer_id')
 
      self.attributes = attrs = {}
      self.items = items = attrs['items'] = []
 
      self.custom_fields = attrs['custom_fields'] = {}
      for custom_field in node.getElementsByTagName('custom_field'):
        self.custom_fields[extract_kv_node(custom_field, 'custom_field_name')] = \
         extract_kv_node(custom_field, 'custom_field_value')
 
      self.transaction_details = attrs['detail'] = []
      for details in node.getElementsByTagName('transaction_detail'):
        item = {'product_code': extract_kv_node(details, 'product_code')}
 
        for key in ['subscription_startdate', 'next_transaction_date']:
          date_str = extract_kv_node(details, key)
          try:
            item[key] = datetime.strptime(date_str, FoxyData.DateFmt)
          except ValueError:
            item[key] = date_str
 
        detail = item['detail'] = {}
        for detail_opt in details.getElementsByTagName('transaction_detail_option'):
          detail[extract_kv_node(detail_opt, 'product_option_name')] = \
           extract_kv_node(detail_opt, 'product_option_value')
 
        items.append(item)
 
  def __init__(self, markup):
    self.markup = markup
    self.doc = parseString(self.markup)
    self.transactions = []
 
    for transaction in self.doc.getElementsByTagName('transaction'):
      self.transactions.append(FoxyData.Transaction(transaction))
 
  def __str__(self):
    return str(self.markup)
 
 
  @classmethod
  def from_str(self, data_str):
    return FoxyData(data_str)
 
  """
  Given a string containing RC4-crypted FoxyCart datafeed XML and the
  cryptographic key, decrypt the contents and create a FoxyData object
  containing all of the Transactions in the data feed.
  """
  @classmethod
  def from_crypted_str(self, data_str, crypt_key):
    a = ARC4(crypt_key)
    return FoxyData.from_str(a.crypt(data_str))
 
  @classmethod
  def decrypt_str(self, data_str, crypt_key):
    a = ARC4(crypt_key)
    return a.crypt(data_str)
 
  def __len__(self):
    return len(self.transactions)
