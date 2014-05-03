@echo off
REM name, cip4, cip6 sip4, sip6, prefix
netsh interface teredo set state disabled
netsh interface ipv6 add v6v4tunnel %1 %2 %4
netsh interface ipv6 add address %1 %3
netsh interface ipv6 add route %6 %1 %5
