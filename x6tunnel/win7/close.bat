@echo off
REM name, cip6
netsh interface teredo set state default
netsh interface ipv6 delete address %1 %2
route -f -6
netsh interface ipv6 delete interface %1
