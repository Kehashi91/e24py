"""
Contains E24sess class and related exceptions. 

E24sess contains all methods that directly interacts with the API,
leaving high-level abstractions ApiObject classes. It also contains
a range of utility methods that interact with the API. 
"""


import requests

import hmac, hashlib, base64
import json
import os

from email.utils import formatdate

from .globals import APIKEY, APISECRET, ENDPOINTS, TYPEMAP


class ApiRequestFailed(Exception):
    """Generic exception on non 2xx API response"""
    pass


class E24sess():
    """
    Session class encapsulating all methods tied to making actual requests and other non-resource tied utlilites.
    Registers all created API objects within a dictionary. Also creates a single requests.Session for use in all API 
    calls.
    """
    default_session = None

    def __init__(self, endpoint="dc1", set_default=True):
        self.session = requests.Session()  # Single request.Session() bound to instance
        self.endpoint = ENDPOINTS[endpoint]
        self.objects = {}
        if set_default: 
            E24sess.default_session = self

    def api_request(self, method, path, data=None):
        """
        This method creates a valid authorization header, and prepares all data requeired to make an API request. It passess
        the data to request_dispatch that handles actually sending the request.
        """

        url = "https://{}{}".format(self.endpoint, path)

        if data:
            authstring = "{}\n{}\n{}\n{}\n{}".format(method, self.endpoint, formatdate(usegmt=True), path,
                                                  json.dumps(data))
        else:
            authstring = "{}\n{}\n{}\n{}\n".format(method, self.endpoint, formatdate(usegmt=True), path)

        authstring = hmac.new(bytes(APISECRET, 'utf-8'), bytes(authstring, 'utf-8'), hashlib.sha256).digest()
        authstring = (base64.b64encode(authstring))

        authstring = bytes(APIKEY, 'utf-8') + b':' + authstring

        headers = {'Content-type': 'application/json', 'X-Date': formatdate(usegmt=True), 'Authorization': authstring}

        return self.request_dispatch(method, headers, url, data)

    def request_dispatch(self, method, headers, url, data):
        """
        Sends the request prepared by previous method and makes sure the response from the server is valid and succeded
        """
        methods = {"GET", "POST", "PUT", "DELETE"}

        if method not in methods:
            raise ValueError("Unrecognized method: {}".format(method))
        request = requests.Request(method, url, headers=headers, json=data)
        request = self.session.prepare_request(request)
        request = self.session.send(request)
        
   
        #write to file (TODO: move to debug mode)
        with open('data.json', 'a') as out:
            out.write("url:\n")
            out.write(url)
            out.write("Headers:\n")
            out.write(str(headers))
            out.write("status:\n")
            out.write(str(request.status_code))
            out.write("response:\n")
            json.dump(request.json(), out)
            out.write("\n")


        if request.status_code == 404:  # Necessary before we access request.json() to avoid JSONDecodeError
            raise ApiRequestFailed("Status Code: {} \n No Json response".format(request.status_code))
        elif request.json()['success'] != True or not request.ok:
            raise ApiRequestFailed(("Status Code: {} \n Response: \n {}").format(request.json(), request.status_code))
        else:
            return request

    def resource_search(self, type, id=None, label=None):
        """
        Generic search function, returns uniformally formatted json responses independently. As a search function,
        it handles not finding a resources simply by returning False, not an exception.

        BUG(minor): In case of many resources with same label, only the first one will be returned
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

    def create_vm(self, name, cpu, memory):
        """This method is used to request the API to create a new vm. As the response
        for this request contains only vm id, it is insufficient to instantiate a VirtualMachine
        object. It also canno call VirtualMachine contructor right after an ID is returned, as there
        is a significant delay befor e24 cloud actually creates a valid resource."""

        params = {
            "create_vm": {
                "cpus": cpu,
                "ram": memory,
                "zone_id": "24e12e20-0851-5354-e2c3-04b16c4c9c45",
                "name": name,
                "boot_type": "image",
                "os": "2599",
                "password": "placeholder123placeholder123",
            }
        }

        r = self.api_request('PUT', "/v2/virtual-machines", params)
        print(r.json())
        return r.json()["virtual_machine"]["id"]



    def get_os(self):
        """
        Returns a dictionary where temlates id are the keys. Temporary until proper
        ApiObject for templates is introduced.
        """
        r = self.api_request('GET', "/v2/templates", "kek")

        r = r.json()["templates"]

        rv = {template["id"]: template for template in r}
        for key, value in rv.items():
            del value["id"]

        return rv