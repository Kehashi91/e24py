"""
This test suite uses responses and mock to avoid any real request to the API. It provides us with a stable testing 
enviroment that works offline, and is much faster to execute. Using pytest fixtures we have a way to conveniently and
modurarly mock commonly used methods, such as api_request and resource_search.

This file depends on a test-data.json file, that has all mocked API responses. Every response has a unique name, and 
some are reused to avoid repetition.

TODO:
Tests for VirtualMachine class
Tests for proper session handling for ApiObject class
Refactor this namespace to make it more readable (together with test-data.json)
Introduce fixtures scopes
Check if we can activate responses globally
Fix api_call_mock minor bug (more in docstring)
Rarely checking authstring will not work (more in docstring)
"""


import pytest
import responses
from unittest import mock

import e24py

import hmac, hashlib, base64
import json
import requests

from email.utils import formatdate


@pytest.fixture()
def session_setup(request):
    """Session setup and teardown."""

    def finalizer():
        e24py.E24sess.default_session = None

    request.addfinalizer(finalizer)

    return e24py.E24sess("EU/POZ-1", set_default=False)


@pytest.fixture()
def api_checksum_mock():
    """Mocks checksum in the authority request header. This fixture pretty much recreates the process of preparing a
    hash, that we can check against tested method
    
    BUG: Since time used in testing method and one used in this fixture method rarely can differ by one second, hashes
    will differ and test will fail."""

    def _api_call_mock(method, endpoint, url, data=None):
        if data:
            rawauth = "{}\n{}\n{}\n{}\n{}".format(method, endpoint, formatdate(usegmt=True), url, json.dumps(data))
        else:
            rawauth = "{}\n{}\n{}\n{}\n".format(method, endpoint, formatdate(usegmt=True), url)

        rawauth = hmac.new(bytes(e24py.session.APISECRET, 'utf-8'), bytes(rawauth, 'utf-8'), hashlib.sha256).digest()
        authstring = (base64.b64encode(rawauth))
        complete = bytes(e24py.session.APIKEY, 'utf-8') + b':' + authstring

        return complete

    return _api_call_mock


@pytest.fixture()
def api_call_mock():
    """This factory conveniently mocks request objects that are returned by api_request and resource_search methods.
    Since in this context we don't really care about the url (other than the fact that response and request url must 
    match) we create one based on datapoint name. We still can still check if mocked method was called with appropiate
    parametheres using 'assert_called_with'. 
    
    BUG: URL uniqeness works around problem when multiple responses are tied to same
    url, which caused problem when this fixture is used alongside create_api_object. Why?"""
    def _api_call_mock(datapoint):
        with open('tests/test-data.json') as file:
            data = json.load(file)

            responses.add(responses.GET, "http://{}".format(datapoint), json=data[datapoint])

            return requests.get("http://{}".format(datapoint)), data

    return _api_call_mock


@pytest.fixture()
def create_api_object():
    """This factory wraps api_call_mock to create a ready-to-use instance of desired class, with parameters specified
    in test-data.json file."""
    def _create_api_object(datapoint, objecttype, session):
        object_data = api_call_mock()
        object_data, smth = object_data(datapoint)

        types = {"virtual_machine": e24py.VirtualMachine, "storage_volume": e24py.StorageVolume}

        session.resource_search = mock.MagicMock()
        session.resource_search.return_value = object_data.json()

        rv = types[objecttype]
        return rv(id="test_id", session=session)

    return _create_api_object


class TestSessionInitialization:
    """Tests e24py.E24sess initialization and proper e24py.E24sess.default_session setting."""

    def test_e24_constructor(self, session_setup):
        assert type(session_setup) is e24py.E24sess
        assert type(session_setup.session) is requests.Session
        assert type(session_setup.objects) is dict

        with pytest.raises(KeyError):
            e24py.E24sess('jkh432k4g32kg4')
            e24py.E24sess('')

    def test_e24_default_session(self, session_setup):
        # we already have a non default session set up

        assert not e24py.E24sess.default_session

        test_inst_2 = e24py.E24sess("EU/POZ-1", set_default=True)

        assert e24py.E24sess.default_session == test_inst_2

        test_inst_3 = e24py.E24sess("EU/POZ-1", set_default=True)

        assert e24py.E24sess.default_session == test_inst_3

        test_inst_4 = e24py.E24sess("EU/POZ-1", set_default=False)

        assert e24py.E24sess.default_session == test_inst_3


@mock.patch("e24py.session.APIKEY", "access_key")
@mock.patch("e24py.session.APISECRET", "secret_key")
class TestApiCall:
    """Tests e24py.E24sess.api_request and request_dispatch  method."""

    @responses.activate
    def test_authorization_get(self, session_setup, api_checksum_mock):
        responses.add(responses.GET, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines",
                      json={'success': True}, status=200)
        complete = api_checksum_mock("GET", "eu-poland-1poznan.api.e24cloud.com", "/v2/virtual-machines")
        r = session_setup.api_request('GET', '/v2/virtual-machines')

        assert r.json() == {'success': True}
        assert r.status_code == 200
        assert r.request.headers['Authorization'] == complete

    @responses.activate
    def test_authorization_put(self, session_setup, api_checksum_mock):
        data = {'success': True}

        responses.add(responses.PUT, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines/testid/resize",
                      json={'success': True}, status=200)
        complete = api_checksum_mock("PUT", "eu-poland-1poznan.api.e24cloud.com", "/v2/virtual-machines/testid/resize",
                                     data)
        r = session_setup.api_request('PUT', '/v2/virtual-machines/testid/resize', data)

        assert r.json() == {'success': True}
        assert r.status_code == 200
        assert r.request.headers['Authorization'] == complete

    @responses.activate
    def test_authorization_delete(self, session_setup, api_checksum_mock):
        data = {'success': True}

        responses.add(responses.DELETE, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines/testid/delete",
                      json={'success': True}, status=200)
        complete = api_checksum_mock("DELETE", "eu-poland-1poznan.api.e24cloud.com",
                                     "/v2/virtual-machines/testid/delete", data)
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
        responses.add(responses.GET, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines-1",
                      json={'success': False}, status=200)
        responses.add(responses.GET, "https://eu-poland-1poznan.api.e24cloud.com/v2/virtual-machines-2", status=404)

        with pytest.raises(e24py.session.ApiRequestFailed):
            session_setup.api_request('GET', '/v2/virtual-machines-1')
        with pytest.raises(e24py.session.ApiRequestFailed):
            session_setup.api_request('GET', '/v2/virtual-machines-2')


class TestSessionUtilities:
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
        session_setup.api_request.assert_called_once_with('GET', "/v2/virtual-machines/test_vm_id")

    @responses.activate
    def test_resource_search_by_id_no_resource(self, session_setup):
        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.side_effect = e24py.session.ApiRequestFailed()

        r2 = session_setup.resource_search(type='virtual_machine', id="nonexistent_id")

        assert not r2
        session_setup.api_request.assert_called_once_with('GET', "/v2/virtual-machines/nonexistent_id")

    @responses.activate
    def test_resource_search_by_label_single_resource(self, session_setup, api_call_mock):
        rv, data = api_call_mock("test_resource_search_by_label_1")  # reusing existing data entry

        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv

        r = session_setup.resource_search(type='virtual_machine', label="test_label")

        assert r == data["test_resource_search_by_label_1"]['virtual_machines'][0]
        session_setup.api_request.assert_called_once_with('GET', "/v2/virtual-machines")

    @responses.activate
    def test_resource_search_by_label_multiple_resources(self, session_setup, api_call_mock):
        rv, data = api_call_mock("test_resource_search_by_multiple_resources")

        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv

        r = session_setup.resource_search(type='virtual_machine', label="test_label_correct")

        assert r == data["test_resource_search_by_multiple_resources"]['virtual_machines'][1]
        session_setup.api_request.assert_called_once_with('GET', "/v2/virtual-machines")

    @responses.activate
    def test_create_vm(self, session_setup, api_call_mock):
        rv, data = api_call_mock("test_create_vm")

        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv

        session_setup.zone = "test_zone_id"

        r = session_setup.create_vm("test_vm", 2, 1024)

        expected_data = {  # data that is meant to be sent to api_request by tested method
            "create_vm": {
                "cpus": 2,
                "ram": 1024,
                "zone_id": "test_zone_id",
                "name": "test_vm",
                "boot_type": "image",
                "os": "2599",
                "password": "placeholder123placeholder123",
            }
        }

        assert r == "test_create_vm"
        session_setup.api_request.assert_called_once_with('PUT', "/v2/virtual-machines", expected_data)


class TestApiObjects:
    """Tests e24py.Apiobjects instancing and methods. We skip testing ApiObject class, as it is not called directly."""

    def test_session_handling(self, session_setup):
        """Tests proper session handling on ApiObject initialization"""
        with pytest.raises(ValueError):
            e24py.apiobjects.ApiObject.session_handler(None)

        with pytest.raises(KeyError):
            e24py.apiobjects.ApiObject.session_handler("False_endpoint")

        handler1 = e24py.apiobjects.ApiObject.session_handler(session_setup)

        session = e24py.E24sess("EU/POZ-1", set_default=True)
        handler2 = e24py.apiobjects.ApiObject.session_handler(None)

        assert handler1 == session_setup
        assert handler2 == session

    @responses.activate
    def test_create_storage_volume(self, session_setup, api_call_mock):
        """This method is not using the create_api_object as it simulates normal flow when instancing objects."""
        rv, data = api_call_mock("test_storage")

        session_setup.resource_search = mock.MagicMock()
        session_setup.resource_search.return_value = rv.json()

        storage = e24py.StorageVolume(id="test_storage_id", session=session_setup)

        assert storage.id == "test_storage_id"
        assert storage.data == data["test_storage"]
        assert not storage.label
        assert storage.size == 40
        assert session_setup.objects[storage.id] == storage
        session_setup.resource_search.assert_called_once_with('storage_volume', "test_storage_id", '')

    @responses.activate
    def test_storage_volume_attach(self, session_setup, api_call_mock, create_api_object):
        test_storage = create_api_object("test_storage", "storage_volume", session_setup)

        rv, data = api_call_mock("placeholder_success")

        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv

        test_storage.attach("test_id")

        session_setup.api_request.assert_called_once_with('POST', "/v2/storage-volumes/test_storage_id/attach",
                                                     {"virtual_machine_id": "test_id"})

    @responses.activate
    def test_storage_volume_attach(self, session_setup, api_call_mock, create_api_object):
        test_storage = create_api_object("test_storage", "storage_volume", session_setup)

        rv, data = api_call_mock("placeholder_success")

        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv

        test_storage.detach()

        session_setup.api_request.assert_called_once_with('POST', "/v2/storage-volumes/test_storage_id/detach")

    @responses.activate
    def test_storage_volume_detach(self, session_setup, api_call_mock, create_api_object):
        test_storage = create_api_object("test_storage", "storage_volume", session_setup)

        rv, data = api_call_mock("placeholder_success")

        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv

        test_storage.attach("test_id")

        session_setup.api_request.assert_called_once_with('POST', "/v2/storage-volumes/test_storage_id/attach",
                                                     {"virtual_machine_id": "test_id"})

    @responses.activate
    def test_storage_volume_update(self, session_setup, api_call_mock, create_api_object):
        test_storage = create_api_object("test_storage", "storage_volume", session_setup)

        rv, data = api_call_mock("test_storage_updated")

        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv

        test_storage.update()
        session_setup.api_request.assert_called_once_with('GET', "/v2/storage-volumes/test_storage_id")
        assert test_storage.data == data["test_storage_updated"]["storage_volume"]
        assert test_storage.size == 60
        assert test_storage.label == "updated_label"

    @responses.activate
    def test_storage_volume_delete(self, session_setup, api_call_mock, create_api_object):
        test_storage = create_api_object("test_storage", "storage_volume", session_setup)

        rv, data = api_call_mock("placeholder_success")

        session_setup.api_request = mock.MagicMock()
        session_setup.api_request.return_value = rv

        test_storage.delete()
        with pytest.raises(KeyError):
            assert session_setup.objects[test_storage.id] != test_storage

        session_setup.api_request.assert_called_once_with('DELETE', "/v2/storage-volumes/test_storage_id")


    @responses.activate
    def test_create_vm(self, session_setup, create_api_object, api_call_mock):
        """This method is not using the create_api_object as it simulates normal flow when instancing objects."""
        pass
