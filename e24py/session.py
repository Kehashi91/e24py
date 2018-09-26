"""Contains E24sess class and related exceptions. 

E24sess contains all methods that directly interacts with the API,
leaving high-level abstractions ApiObject classes. It also contains
a range of utility methods that interact with the API. 
"""

import logging

import hmac, hashlib, base64
import json

from email.utils import formatdate

from .globals import APIKEY, APISECRET, ENDPOINTS, TYPEMAP

try:
    import requests
except ImportError:
    print("request module not found - import it!")
    exit(1)


class ApiRequestFailed(Exception):
    """Generic exception on non 2xx API response"""
    def __init__(self, msg=None, session=None):
        if session:
            logging.error("An {} exception occured: {} - for endpoint: {}".format(
                __class__.__name__, msg, session.endpoint))
        else:
            logging.error("An {} exception occured: {}".format(
                __class__.__name__, msg))


class E24sess():
    """
    Session class encapsulating all methods tied to making actual requests and
    other non-resource tied utlilites. Registers all created API objects within
    a dictionary. Also creates a single requests.Session for use in all API 
    calls."""

    default_session = None

    def __init__(self, endpoint="DC1/PUBLIC-1", set_default=True):
        if endpoint not in ENDPOINTS:
            raise KeyError("Valid endpoints are: {}".format(ENDPOINTS.keys()))

        self.session = requests.Session() # request.Session is instance-bound
        self.endpoint = endpoint
        self.objects = {}
        self.zone = None # lazy init
        if set_default:
            E24sess.default_session = self

    def __repr__(self):
        if E24sess.default_session == self:
            is_default = True
        else:
            is_default = False
        return "{} object default_session={}, endpoint={} at {}".format(
            __class__.__name__, is_default, self.endpoint, hex(id(self)))

    def api_request(self, method, path, data=None):
        """
        This method creates a valid authorization header, and prepares all 
        data requeired to make an API request. It passess the data to 
        request_dispatch that handles actually sending the request."""

        short_url = ENDPOINTS[self.endpoint]
        full_url = "https://{}{}".format(short_url, path)

        if data:
            authstring = "{}\n{}\n{}\n{}\n{}".format(method, short_url,
                                                     formatdate(usegmt=True), 
                                                     path, json.dumps(data))
        else:
            authstring = "{}\n{}\n{}\n{}\n".format(method, short_url,
                                                   formatdate(usegmt=True), path)

        authstring = hmac.new(bytes(APISECRET, 'utf-8'), 
                              bytes(authstring, 'utf-8'), 
                              hashlib.sha256).digest()

        authstring = (base64.b64encode(authstring))
        authstring = bytes(APIKEY, 'utf-8') + b':' + authstring

        headers = {
            'Content-type': 'application/json',
            'X-Date': formatdate(usegmt=True),
            'Authorization': authstring
            }

        return self._request_dispatch(method, headers, full_url, data)

    def _request_dispatch(self, method, headers, url, data):
        """Sends the request prepared by previous method and makes sure the
        response from the server is valid and succeded.
        """
        methods = {"GET", "POST", "PUT", "DELETE"}

        if method not in methods:
            raise ValueError("Unrecognized method: {}".format(method))
        request = requests.Request(method, url, headers=headers, json=data)
        request = self.session.prepare_request(request)
        try:
            request = self.session.send(request)
            logging.info("Sending request, url: {} headers: {} status: {} response:\n{}".format(
                url, str(headers), request.status_code, request.json()))
            if not request.json()['success'] or not request.ok:
                raise ApiRequestFailed(("Status Code: {} \n Response: \n {}").format(
                                        request.json(), request.status_code), self)
            return request

        except json.JSONDecodeError:
            raise ApiRequestFailed("Status Code: {} \n No Json response".format(
                                   request.status_code), self)

    def resource_search(self, type, id=None, label=None):
        """Generic search function, returns uniformally formatted json responses
        independently. As a search function, it handles not finding a resources 
        simply by returning False, not an exception.

        BUG(minor): In case of many resources with same label,only the first one
        will be returned.
        """
        if id:
            url = "/v2/{}/{}".format(TYPEMAP[type]['urlname'], id)
            try:
                r = self.api_request('GET', url)

            except ApiRequestFailed:
                return False
            return r.json()[type]

        elif label:
            url = "/v2/{}".format(TYPEMAP[type]['urlname'])

            r = self.api_request('GET', url)

            for resource in r.json()[TYPEMAP[type]['jsonname']]:
                if resource['label'] == label:
                    return resource
            return False

        else:
            raise ValueError('No ID or label provided.')

    def _set_zone(self):
        """This function sets proper zone id for selected endpoint. This 
        attribute is initalized lazily since for the time being only create_vm
        method needs zone information, and as such first use of create_vm() runs
        this method.
        """

        r = self.api_request("GET", '/v2/regions')

        for zone in r.json()['regions']:
            if zone['zones'][0]['label'] == self.endpoint:
                self.zone = zone['zones'][0]['id']
        if not self.zone:
            raise ApiRequestFailed(
                "Endpoint {} zone info not found:\njson info:\n{}".format(
                    self.endpoint, r.json()))

    def create_vm(self, name, cpu, memory, os_template, password=None, key_id=None, user_data=None):
        """This method is used to request the API to create a new vm. As the 
        response for this request contains only vm id, it is insufficient to
        instantiate a VirtualMachine object. It also cannot call VirtualMachine
        contructor right after an ID is returned, as there is a significant 
        delay before e24 cloud actually creates a valid resource.
        """
        if not self.zone:
            self._set_zone()

        params = {
            "create_vm": {
                "cpus": cpu,
                "ram": memory,
                "zone_id": self.zone,
                "name": name,
                "boot_type": "image",
                "os": os_template,
            }
        }
        if password:
            params["create_vm"]["password"] = password
        if key_id:
            params["create_vm"]["key_id"] = key_id
        if user_data:
            params["create_vm"]["user_data"] = user_data

        r = self.api_request('PUT', "/v2/virtual-machines", params)
        return r.json()["virtual_machine"]["id"]

    def get_os(self):
        """Returns a dictionary where temlates id are the keys. Temporary until proper
        ApiObject for templates is introduced.
        """
        r = self.api_request('GET', "/v2/templates", "kek")

        r = r.json()["templates"]

        rv = {template["id"]: template for template in r}
        for key, value in rv.items():
            del value["id"]

        return rv
