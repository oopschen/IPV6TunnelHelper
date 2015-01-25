IPV6TunnelHelper
================
[tunel]: http://tunnelbroker.net/ "Tunnel Broker"
[godown]: http://golang.org "go 1.3"
This project is help users to get into IPV6 network easily. All the project done is some scripts to ease using the service provided by **[tunnelbroker.net][tunel]**. The current status of this project only support OS with Go installed and linux MUST have *iproute2* installed, it is very welcome for you to add support for platforms like **bsd**, **winxp** and so on.  
  
Feature
====
1. auto create tunnel at [tunnelbroker][tunel]
2. auto update end user's ip settings at [tunnelbroker][tunnel] when ip changed
3. OS tunnel creation automation
  
### Install  
You can install by the following command.  
  
    export GOPATH=$(pwd)
    go install github.com/oopschen/xtunnel
  
Then check the executable file at bin/xtunnel, copy it to your *PATH*.

### Usage
Open a tunnel by using the tunnelbroker **username** and **passwd**.
    
    xtunnel -u username -p passwd open

     
Close a tunnel.
    
    xtunnel close
      
### Tips  
Put the executable file to path, use the sudo for convenience.

Where it from?
===
It is not easy to use service like **Google**, **Facebook** and **Forbidden websites** at China mainland. The idea happens to me the moment i saw the ipv6 tunnel -- the GFW may not filter ipv6 tunnel for safety. Then i do it and it works. Though, some sites like **Youtube** do not work.   
  
Prerequest
===
* register at [tunnelbroker][tunel]
* [go][godown]\(>=1.3\) installed
  
#### Linux  
1. you need **iproute2** preinstalled.  
2. you need permission to send icmp packets and run *ip* command.
