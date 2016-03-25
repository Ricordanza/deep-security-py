# standard library
import datetime

# 3rd party libraries

# project libraries
import core

class Manager(core.CoreApi):
  def __init__(self,
      hostname='app.deepsecurity.trendmicro.com',
      port='4119',
      tenant=None,
      username=None,
      password=None,
      ignore_ssl_validation=False
      ):
    core.CoreApi.__init__(self)
    self._hostname = None
    self._port = port
    self._tenant = tenant
    self._username = username
    self._password = password
    self.ignore_ssl_validation = ignore_ssl_validation
    self.hostname = hostname

  def __del__(self):
    """
    Try to gracefully clean up the session
    """
    try:
      self.sign_out()
    except Exception, err: pass

  def __str__(self):
    """
    Return a better string representation
    """
    return "Manager <{}:{}>".format(self.hostname, self.port)

  # *******************************************************************
  # properties
  # *******************************************************************
  @property
  def hostname(self): return self._hostname
  
  @hostname.setter
  def hostname(self, value):
    if value == 'app.deepsecurity.trendmicro.com': # Deep Security as a Service
      self.port = 443
    self._hostname = value
    self._set_endpoints()
  
  @property
  def port(self): return self._port

  @port.setter
  def port(self, value):
    self._port = int(value)
    self._set_endpoints()

  @property
  def tenant(self): return self._tenant

  @tenant.setter
  def tenant(self, value):
    self._tenant = value
    self._reset_session()

  @property
  def username(self): return self._username
  
  @username.setter
  def username(self, value):
    self._username = value
    self._reset_session()

  @property
  def password(self): return self._password

  @password.setter
  def password(self, value):
    self._password = value
    self._reset_session()

  # *******************************************************************
  # methods
  # *******************************************************************
  def _set_endpoints(self):
    """
    Set the API endpoints based on the current configuration
    """
    self._rest_api_endpoint = "https://{}:{}/rest".format(self.hostname, self.port)
    self._soap_api_endpoint = "https://{}:{}/webservice/Manager".format(self.hostname, self.port)

  def _reset_session(self):
    """
    Reset the current session due to a credentials change
    """
    self.sign_out()
    self.sign_in()
  
  def sign_in(self):
    """
    Sign in to the Deep Security APIs
    """
    # first the SOAP API
    soap_call = self._get_request_format()
    soap_call['data'] = {
      'username': self.username,
      'password': self.password,
      }
    if self.tenant:
      soap_call['call'] = 'authenticateTenant'
      soap_call['data']['tenantName'] = self.tenant
    else:
      soap_call['call'] = 'authenticate'

    response = self._request(soap_call, auth_required=False)
    if response and response['data']: self._sessions[self.API_TYPE_SOAP] = response['data']

    # then the REST API
    rest_call = self._get_request_format(api=self.API_TYPE_REST)
    rest_call['data'] = {
      'dsCredentials':
          {
            'userName': self.username,
            'password': self.password,
          }
    }
    if self.tenant:
      rest_call['call'] = 'authentication/login'
      rest_call['data']['dsCredentials']['tenantName'] = self.tenant
    else:
      rest_call['call'] = 'authentication/login/primary'

    response = self._request(rest_call, auth_required=False)
    if response and response['raw']: self._sessions[self.API_TYPE_REST] = response['raw']

    if self._sessions[self.API_TYPE_REST] and self._sessions[self.API_TYPE_SOAP]:
      return True
    else:
      return False

  def sign_out(self):
    """
    Sign out to the Deep Security APIs
    """
    # first the SOAP API
    soap_call = self._get_request_format(call='endSession')
    if self._sessions[self.API_TYPE_SOAP]:
      response = self._request(soap_call)
      if response and response['status'] == 200: self._sessions[self.API_TYPE_SOAP] = None

    # then the REST API
    rest_call = self._get_request_format(api=self.API_TYPE_REST, call='authentication/logout')
    if self._sessions[self.API_TYPE_REST]:
      response = self._request(rest_call)
      if response and response['status'] == 200: self._sessions[self.API_TYPE_REST] = None

    if self._sessions[self.API_TYPE_REST] and self._sessions[self.API_TYPE_SOAP]:
      return True
    else:
      return False
  
  def get_time(self):
    """
    Get the current time as set on the Manager
    """
    result = None
    soap_call = self._get_request_format(call='getManagerTime')
    response = self._request(soap_call, auth_required=False)
    if response['status'] == 200 and response['data'].has_key('#text'):
      result = datetime.datetime.strptime(response['data']['#text'], "%Y-%m-%dT%H:%M:%S.%fZ")
  
    return result
  