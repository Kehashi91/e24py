from .session import E24sess, ApiRequestFailed, TYPEMAP



class ApiObject():
    """
    Base class that includes all methods and properties common for API resources. Also includes handler for proper 
    session object.
    """
    @staticmethod
    def session_handler(session):
        """
        Handler do ustawienia sesji przy inicjalizacji obiektu
        """
        if not session and not E24sess.default_session:
            raise ValueError('No session set')
        elif type(session) is E24sess:
            return session
        elif E24sess.default_session:
            return E24sess.default_session
        else:
            raise KeyError('Valid endpoints are DC1 and DC2!')

    def __init__(self, type, id="", label="", session=None):
        
        self.session = ApiObject.session_handler(session)
        
        if not id and not label:
            raise ValueError('Cannot find resource without ID or label.')

        
        request = self.session.resource_search(type, id, label)
        if not request:
            raise ApiRequestFailed("No resource found!")
        print (request)
        
        
        self.data = request
        self.type = type
        self.id = request['id']
        self.label = request['label']
        self.session.objects[self.id] = self
    

        
    def update(self):
            
        url = "/v2/{}/{}".format(TYPEMAP[self.type]['urlname'], self.id)
        
        r =  self.session.api_request("GET", url)
        print (r.json())
        print (".......")
        self.data = r.json()[self.type]
        print (self.data)

        attributes = [attribute for attribute in dir(self) if not callable(getattr(self, attribute)) and not attribute.startswith("__")]
        
        attributes.remove('id')
        attributes.remove('data')
        attributes.remove('type')
        attributes.remove('session')
        
        for attribute in attributes:
            setattr(self, attribute, self.data[attribute])
            
    def delete(self):
        url = "/v2/{}/{}".format(TYPEMAP[self.type]['urlname'], self.id)

        r = self.session.api_request("DELETE", url)

        del self.session.objects[self.id]


class VirtualMachine(ApiObject):
    """
    Represents a vm resource
    """
    
    def __init__(self, id='', label='', session=None):
        super(VirtualMachine, self).__init__(type='virtual_machine', id=id, label=label, session=session)
        self.cores = self.data['cores']
        self.ram = self.data['ram']
        self.storage_volumes = [StorageVolume(storage['id']) for storage in self.data['storage_volumes']]

    def update(self):
        super(VirtualMachine, self).update()
        
    def delete(self):
        super(VirtualMachine, self).delete()

        for volume in self.storage_volumes:

            del self.session.objects[volume.id] #Volume is deleted, we tidy up conn.objects

    def power_on(self):
        r = self.session.api_request('POST', "/v2/virtual-machines/{}/poweron".format(self.id))
        if r.json()["success"]:
            print("hurray!")

    def power_off(self):
        r = self.session.api_request('POST', "/v2/virtual-machines/{}/poweroff".format(self.id))
        if r.json()["success"]:
            print("hurray!")

    def resize(self, cores, memory):
        resize_amount = {"cores": cores, "ram": memory}

        r = self.session.api_request('POST', "/v2/virtual-machines/{}/resize".format(self.id), resize_amount)



class StorageVolume(ApiObject):
    """
    Represents a storage resource.
    """

    def __init__(self,  id='', label='', session=None):
        super(StorageVolume, self).__init__(type='storage_volume', id=id, label=label, session=session)
        self.size = self.data['size']

    def update(self):
        super(StorageVolume, self).update(id=self.id)
    
    def attach(self, vmid):

        data = {"virtual_machine_id": vmid}

        r = self.session.api_request('POST', "/v2/storage-volumes/{}/attach".format(self.id), data)
        
    def detach(self):

        r = self.session.api_request('POST', "/v2/storage-volumes/{}/detach".format(self.id))


class IpAdress(ApiObject):

    pass
    

    