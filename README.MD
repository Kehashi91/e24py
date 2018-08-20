# e24py

Python wrapper for e24cloud REST API, powered by requests package.

## Installation

1. Clone this repository
```
git clone https://github.com/Kehashi91/e24py
```
2. Make sure you have Python3.5+ installed
3. Install required dependecies through requirements file:
```
pip install -r requirements.txt
```
or install dependencies manually:
```
pip install requests
pip install responses
pip install pytest #optional if you don't want to run tests
```
4. Export your e24cloud API access key and secret key:
```
export E24_KEY='YOUR_KEY'
export E24_SECRET='YOUR_SECRET_KEY'
```

## Basic usage

First, you need to create a session instance. It is bound to single API endpoint, and all other methods require an
instance. Currently there are 2 endpoints, labeled "dc1" and "dc2".

```
import e24py

session = e24py.E24sess(endpoint="dc1")
```
If session is specified this way, it will become a default session and all other methods will use it by default (unless
told to use diffrent session explicitly). We can now bind our cloud resources to Python objects, for example:
```
vm_label = e24py.VirtualMachine(label="myvm") #searches by label
vm_id = e24py.VirtualMachine(id="00000000000000000000") #searches by id
```
We can now inspect resource attributes and call its methods:
```
vm_label.id # returns id
vm_label.cores # returns number of CPU cores
vm_label.storage_volumes # returns a list of StorageVolume object corresponding to the vm hard drives

vm_label.power_off() # Shut down the vm
vm_label.resize(2, 1024) # Resizes vm to 2 cores and 1024 mb of ram
vm_label.delete() # deletes the vm
```



