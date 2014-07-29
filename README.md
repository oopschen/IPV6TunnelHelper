IPV6TunnelHelper
================
[tunel]: http://tunnelbroker.net/ "Tunnel Broker"
[pydown]: http://www.python.org/download/releases/2.7.5/ "python2.7"
This project is help end users to get into IPV6 network easily. All the project done is some scripts to ease using the service provided by **[tunnelbroker.net][tunel]**. The current status of this project only support on win7 with python installed and linux with *iproute2* installed, it is very welcome for you to add support for platforms like **bsd**, **winxp** and so on.  
  
Feature
====
1. auto create tunnel at [tunnelbroker][tunel]
2. auto update end user ip when ip changed
3. win7 tunnel creation automation
  
### Install  
You can install by the following command.  
  
    pip install X6tunnel 
  

### Usage
Open a tunnel by using the tunnelbroker **username** and **passwd**.
    
    xtunnel -m o username passwd   

     
Close a tunnel.The **username** and **passwd** is irelevant, can be anything.
    
    xtunnel -m c username passwd   

     

Where it from?
===
It is not easy to use service like **Google**, **Facebook** and **Forbidden websites** at China mainland. The idea happens to me the moment i saw the ipv6 tunnel -- the GFW may not filter ipv6 tunnel for safety. Then i do it and it works. Though, some sites like **Youtube** do not work.   
  
Prerequest
===
* register at [tunnelbroker][tunel]
* [python][pydown]\(>=2.6\) installed
  
#### Linux  
1. you need **iproute2** preinstalled  
2. add sudo detect, i will suggest you to add *user ALL=(ALL) NOPASSWD:/sbin/sudo* to you sudo configuration, if wants normal user run the scripts
