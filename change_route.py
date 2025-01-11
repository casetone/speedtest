#!/usr/bin/env python3

import os
import subprocess


def main():
    result = subprocess.run(["curl ifconfig.me"], shell=True, capture_output=True, text=True)
    print(f"Server External IP address at start : {result.stdout}")

    # Change up the Virgin link to be higher priority by adding a routing table record with a lower metric
    result = subprocess.run(["sudo ip route add default via 192.168.0.1 metric 102"], shell=True, capture_output=True, text=True)
    result = subprocess.run(["curl ifconfig.me"], shell=True, capture_output=True, text=True)
    print(f"Server External IP address changed to : {result.stdout}")

    # Remove the added routing table metric so that BT becomes the lowest again
    result = subprocess.run(["sudo ip route del default via 192.168.0.1 metric 102"], shell=True, capture_output=True, text=True)
    result = subprocess.run(["curl ifconfig.me"], shell=True, capture_output=True, text=True)
    print(f"Server External IP address changed back to : {result.stdout}")


if __name__ == "__main__":

    main()