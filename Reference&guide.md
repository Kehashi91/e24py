# Guide

e24py is a wrapper around the e24cloud API, and is meant to make using the API more convenient. To use e24py, familiarize youreself with the e24cloud API reference:

https://support.e24cloud.com/API_e24cloud

It is important to understand that e24py DOES NOT evaluate if your inputs are correct. It is left to the actual API, and any request that does not end in "success": True will throw an ApiRequestFailed exception - it is up to the user to handle these exceptions. Another important issue is the fact that despite a succesful API request, there is often a delay before e24cloud will actually implement any change we requested (beacouese of its internal queueing mechanisms). For example, consider we want to power on a VirtualMachine object vm:
```
vm.power_on()
vm.update()
vm.state # offline
```
Despite the update call that requests fresh data from the API, we still get the old values. This is beacouse we have to wait some times before the changes are actually implemented on the VM.

Lets consider a simple use case: we want to create a vm and then power it off:
```
import e24py 

session = e24py.E24sess(endpoint="EU/POZ-1") #1

os = session.get_os() #2
for id in os:
	if os[id]['label'] == "Ubuntu 18.04":
		ubuntu = id

vm_id = session.create_vm("example", 1, 512, ubuntu, "example_password") #4
sleep(30) #4

vm = e24py.VirtualMachine(id=vm_id) #5
vm.power_off() #6
```
Lets explain the code above.  
We create a default session object (#1). Since we need a os template id to create a vm, we use a get_os helper method (#2) to get a list of all aviable templates. We the iterate over this list, selecting the id of Ubuntu 18.04 template. Now we can create the vm (#3), but this method only returns the id of a new VM, so we cannot act on this vm yet. We call sleep to make sure our vm is ready (#4). We then create a VirtualMachine object (#5), using the id returned by create_vm method. Now we can call the power_off method to turn off the vm.

# Reference

## class e24py.E24sess(endpoint="EU/POZ-1", set_default=True)

E24sess contains all methods that directly interacts with the API, leaving high-level abstractions ApiObject classes. It also contains a range of utility methods that interact with the API. A single instance is tied to a single API endpoint, by default the EU-POZ1 localization. If "set_default" is set to True, all ApiObject instances will interface with the API using default instance, unless told explicitly to use another instance. Contains "objects" attribute, which is a dictionary referencing all ApiObjects bound to this session by their respective ID. Also encapsulates requests.session.
Valid endpoints are: "EU/POZ-1", "EU/POZ-2"
	
### method e24py.E24sess.api_request(self, method, path, data=None)
This method creates a valid authorization header, and prepares all data requeired to make an API request. It passess the data to _request_dispatch that handles actually sending the request. It is the main and only method that directly interacts with the API. Method is an appropriate HTTP method, path is respective resource URL. Data optional argument will be added as a dictionary to the request data header and request body. This method return a pure request object, and to access it contents a request.json() method must be used.
### method e24py.E24sess.resource_search(self, type, id=None, label=None)
This method facilitates e24py.E24sess.api_request to search for a resource, either by it's id or label. If found, it returns the relevant json data for searched object, unlike api_request which returns a full resonse. If no resource is found, it simply returns False, silencing unsuccesful requests exception.
### method e24py.E24sess.create_vm(self, name, cpu, memory, os, password)
### method e24py.E24sess.get_os(self)
Returns a dictionary of all os templates aviable to the user. Template id's are the keys, and the values are itself a dictionary containing all aviable template information
##class e24py.ApiObject(self, type, id="", label="", session=E24sess.default_session)
Base class for (almost) all resources returned by the API. All it's methods and attributes are abiable to other classes.
###method e24py.ApiObject.update()
Updates all instance attributes based on a fresh GET resource request
###method e24py.ApiObject.delete()
Sends DELETE request, and also cleans E24sess.objects from this instance.
## class e24py.VirtualMachine(ApiObject)(self, id='', label='', session=E24sess.default_session)
###method e24py.VirtualMachine.resize(cpu, ram)
###method e24py.VirtualMachine.shutdown(self, wait_for=None)
###method e24py.VirtualMachine.power_off(self):
###method e24py.VirtualMachine.reboot(self):
###method e24py.ApiObject.resize(cpu, ram)
## class e24py.StorageVolume(ApiObject)(self, id='', label='', session=E24sess.default_session)
###method e24py.StorageVolume.attach(self, vmid)
###method e24py.StorageVolume.def detach(self)
###method e24py.StorageVolume.create_image(self, label)
## class e24py.DiscImage(ApiObject)(self, id='', label='', session=E24sess.default_session)