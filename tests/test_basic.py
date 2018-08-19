import pytest
import responses
from unittest import mock

import e24py

import hmac, hashlib, base64
import os
import json
import requests

from email.utils import formatdate


@pytest.fixture()
def session_setup(request):
    """Session setup and teardown"""
    def finalizer():
        e24py.E24sess.default_session = None
    request.addfinalizer(finalizer)
    
    return e24py.E24sess('dc1', set_default=False)
         
@pytest.fixture()
def api_checksum_mock():
    """Mocks checksum in the authority request header."""
    
    def _api_call_mock(method, endpoint, url, data=None):
        if data:
            rawauth = "{}\n{}\n{}\n{}\n{}".format(method, endpoint, formatdate(usegmt=True), url, json.dumps(data))
        else:
            rawauth = "{}\n{}\n{}\n{}\n".format(method, endpoint, formatdate(usegmt=True), url)

        rawauth = hmac.new(bytes(e24py.sess.APISECRET, 'utf-8'), bytes(rawauth, 'utf-8'), hashlib.sha256).digest()
        authstring = (base64.b64encode(rawauth))
        complete = bytes(e24py.sess.APIKEY, 'utf-8') + b':' + authstring
        
        return complete
    return _api_call_mock
    
    

class Test_session_initialization():
    """Tests e24py.E24sess initialization and proper e24py.E24sess.default_session setting."""
   
    def test_E24_constructor(self, session_setup):

        assert type(session_setup) is e24py.E24sess
        assert type(session_setup.session) is requests.Session
        assert type(session_setup.objects) is dict

        with pytest.raises(KeyError):
            test_inst = e24py.E24sess('jkh432k4g32kg4')
            test_inst2 = e24py.E24sess('')
            

    def test_E24_default_session(self, session_setup):
        #we already have a non default session set up

        assert not e24py.E24sess.default_session
        
        test_inst_2 = e24py.E24sess('dc1', set_default=True)

        assert e24py.E24sess.default_session == test_inst_2

        test_inst_3 = e24py.E24sess('dc1', set_default=True)

        assert e24py.E24sess.default_session == test_inst_3

        test_inst_4 = e24py.E24sess('dc1', set_default=False)

        assert e24py.E24sess.default_session == test_inst_3
    

@mock.patch("e24py.sess.APIKEY", "access_key")
@mock.patch("e24py.sess.APISECRET", "secret_key")
class Test_Api_call():
    """Tests e24py.E24sess.api_request and request_dispatch  method."""
    @responses.activate
    def test_authorization_get(self, session_setup, api_checksum_mock):
        

        responses.add(responses.GET, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines", json={'success': True}, status=200)
        complete = api_checksum_mock("GET", "eu-poland-1poznan.api.e24cloud.com", "/v2/virtual-machines")
        r = session_setup.api_request('GET', '/v2/virtual-machines')
        

        assert r.json() == {'success': True}
        assert r.status_code == 200
        assert r.request.headers['Authorization'] == complete


    @responses.activate
    def test_authorization_put(self, session_setup, api_checksum_mock):
        data = {'success': True}
        
        responses.add(responses.PUT, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines/testid/resize", json={'success': True}, status=200)
        complete = api_checksum_mock("PUT", "eu-poland-1poznan.api.e24cloud.com", "/v2/virtual-machines/testid/resize", data)
        r = session_setup.api_request('PUT', '/v2/virtual-machines/testid/resize', data)
        

        assert r.json() == {'success': True}
        assert r.status_code == 200
        assert r.request.headers['Authorization'] == complete
    
    @responses.activate
    def test_authorization_delete(self, session_setup, api_checksum_mock):
        data = {'success': True}
        
        responses.add(responses.DELETE, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines/testid/delete", json={'success': True}, status=200)
        complete = api_checksum_mock("DELETE", "eu-poland-1poznan.api.e24cloud.com", "/v2/virtual-machines/testid/delete", data)
        r = session_setup.api_request('DELETE', '/v2/virtual-machines/testid/delete', data)
        
        assert r.json() == {'success': True}
        assert r.status_code == 200
        assert r.request.headers['Authorization'] == complete
    
    @responses.activate
    def test_bad_method(self, session_setup):
        
        with pytest.raises(ValueError):
            r = session_setup.api_request('BAD_METHOD', '/v2/virtual-machines')
    
    @responses.activate        
    def test_bad_request(self, session_setup):
    
        responses.add(responses.GET, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines-1", json={'success': False}, status=200)
        responses.add(responses.GET, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines-2", status=404)
        
        with pytest.raises(e24py.sess.ApiRequestFailed):
            r1 = session_setup.api_request('GET', '/v2/virtual-machines-1')
        with pytest.raises(e24py.sess.ApiRequestFailed):
            r2 = session_setup.api_request('GET', '/v2/virtual-machines-2')  


@pytest.fixture()
def api_call_mock():
    def _api_call_mock(datapoint):
        with open('tests/test-data.json') as file:
            data = json.load(file)
    
            responses.add(responses.GET, "http://test", json=data[datapoint])

            return requests.get("http://test"), data
            
    return _api_call_mock

class Test_session_utilities():
    """Tests e24py.E24sess utlilities methods (both public and private."""
    
            
    def test_bad_resource_search(self, session_setup):
        with pytest.raises(ValueError):
            session_setup.resource_search(type=None)
            
    @responses.activate
    def test_resource_search_by_id(self, session_setup, api_call_mock):
        
        rv, data = api_call_mock("test_resource_search_by_id_1")
        
        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv
        
        r = session_setup.resource_search(type='virtual_machine', id="test_vm_id")
        
        assert r == data["test_resource_search_by_id_1"]['virtual_machine']
    
    @responses.activate        
    def test_resource_search_by_id_no_resource(self, session_setup):
        
        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.side_effect = e24py.sess.ApiRequestFailed()
        
        r2 = session_setup.resource_search(type='virtual_machine', id="nonexistent_id")
        
        assert not r2
    
    @responses.activate   
    def test_resource_search_by_label_single_resource(self, session_setup, api_call_mock):
    
        rv, data = api_call_mock("test_resource_search_by_label_1")
        
        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv
        
        r = session_setup.resource_search(type='virtual_machine', label="test_label")
        
        assert r == data["test_resource_search_by_label_1"]['virtual_machines'][0]



