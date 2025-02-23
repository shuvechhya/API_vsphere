variable "user" {
  default = "sanjay@vsphere.local" 
}

# vCenter / ESXi Password
variable "password" {
  default = "Cloud$$$8" 
}

# vCenter / ESXi Endpoint
variable "vsphere_server" {
  default = "lab.samundra.local" 
}

# vCenter / ESXi Datacenter
variable "datacenter" {
  default = "Datacenter" 
}

# vCenter / ESXi Datastore
variable "datastore" {
  default = "TEST-LUN0" 
}

# vCenter / ESXi ResourcePool
variable "resource_pool" {
  default = "Resources" 
}

# Virtual Machine configuration
# VM Name
variable "name" {
  default = "testvm" 
}

# Name of OVA template (chosen in import process)
variable "template" {
  default = "Ubuntu-templateCI" 
}

# VM Network
variable "network" {
  default = "Lab Network" 
}

# VM Number of CPU's
variable "cpus" {
  default = 1 
}

# VM Memory in MB
variable "memory" {
  default = 1048 
}