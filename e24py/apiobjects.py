"""Contains ApiObject and its subclasses. Creates high-level representation
for for API resources, and interacts with the API through e24sess class.
"""

import logging

from .session import E24sess, ApiRequestFailed
from .globals import TYPEMAP


class ApiObject():
    """Base class that includes all methods and properties common for API 
    resources. Also includes handler for proper session object.
    """

    def __init__(self, type, id="", label="", session=E24sess.default_session):

        self.session = session

        if not id and not label:
            raise ValueError('Cannot find resource without ID or label.')

        request = self.session.resource_search(type, id, label)
        if not request:
            raise ApiRequestFailed("No resource found!", self.session)

        self.data = request
        self.type = type
        self.id = request['id']
        self.label = request['label']
        self.session.objects[self.id] = self
        logging.info("ApiObject {} id: {} labeled: {} successfuly created".
                    format(self.type, self.id, self.label))

    def __repr__(self):
        return "{} {} object, id={}, bound to {} at {}".format(
            __class__.__name__, self.type, self.id, self.session.endpoint_label, hex(id(self)))

    def update(self):

        url = "/v2/{}/{}".format(TYPEMAP[self.type]['urlname'], self.id)

        r = self.session.api_request("GET", url)
        self.data = r.json()[self.type]

        attributes = [attribute for attribute in dir(self) if not callable(getattr(self, attribute)) and not attribute.startswith("__")]

        attributes.remove('id')
        attributes.remove('data')
        attributes.remove('type')
        attributes.remove('session')

        for attribute in attributes:
            setattr(self, attribute, self.data[attribute])

    def delete(self):
        url = "/v2/{}/{}".format(TYPEMAP[self.type]['urlname'], self.id)

        self.session.api_request("DELETE", url)

        del self.session.objects[self.id]


class VirtualMachine(ApiObject):
    """Represents a vm resource."""

    def __init__(self, id='', label='', session=E24sess.default_session):
        super().__init__(type='virtual_machine', id=id, label=label, session=session)
        self.state = self.data['state']
        self.cores = self.data['cores']
        self.ram = self.data['ram']
        self.storage_volumes = [StorageVolume(storage['id'], session=self.session) for storage in self.data['storage_volumes']]

    def delete(self):
        super(VirtualMachine, self).delete()

        for volume in self.storage_volumes:

            del self.session.objects[volume.id]
            # Volume is deleted, we tidy up conn.objects

    def power_on(self):
        self.session.api_request('POST', "/v2/virtual-machines/{}/poweron".format(self.id))

    def shutdown(self, wait_for=None):
        if wait_for:
            wait_for = {"wait_for": wait_for}

        self.session.api_request('POST', "/v2/virtual-machines/{}/poweroff".format(
                                 self.id), wait_for)

    def power_off(self):
        self.session.api_request('POST', "/v2/virtual-machines/{}/poweroff".format(self.id))

    def reboot(self):
        self.session.api_request('POST', "/v2/virtual-machines/{}/reboot".format(self.id))

    def resize(self, cores, memory):
        resize_amount = {"cores": cores, "ram": memory}

        self.session.api_request('POST', "/v2/virtual-machines/{}/resize".format(
            self.id), resize_amount)


class StorageVolume(ApiObject):
    """Represents a storage resource."""

    def __init__(self,  id='', label='', session=E24sess.default_session):
        super().__init__(type='storage_volume', id=id, label=label, 
                         session=session)
        self.size = self.data['size']

    def attach(self, vmid):

        data = {"virtual_machine_id": vmid}

        self.session.api_request('POST', "/v2/storage-volumes/{}/attach".format(
            self.id), data)

    def detach(self):

        self.session.api_request('POST', "/v2/storage-volumes/{}/detach".format(self.id))

    def create_image(self, label):

        data = {"storage_volume_id": self.id, "label": label}

        r = self.session.api_request('PUT', "/v2/disk-images", data)
        return r.json()["disk_image"]["id"]


class DiscImage(ApiObject):
    """Represents a disc image resource."""

    def __init__(self,  id='', label='', session=E24sess.default_session):
        super().__init__(type='disk_image', id=id, label=label, session=session)
