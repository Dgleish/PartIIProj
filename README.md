# P2P Co-operative Editing

Code is in crdt folder

## Requirements
If you want to run multiple instances on one machine you will need Docker running as well as running the following command:
`docker network create --subnet=172.18.0.0/16 net1` as the IP addresses of each container are assigned statically based on this setup.

### Only if you run a [single instance without Docker](#singlerun)
There is a [requirements.txt](https://github.com/Dgleish/PartIIProj/tree/master/crdt) file which can be satisfied with
`pip3 install -r requirements.txt`.

You will also need Tor running on your machine, with the CookieAuthentication set rather than a password

## Running
To run k instances of the text-editing app locally use `./run [args] [k]` where k defaults to 1.

Otherwise use <a name="singlerun">`./single_run [args] -f [file]`</a> where you pass it a file containing parameters as specified by the usage of the program 
