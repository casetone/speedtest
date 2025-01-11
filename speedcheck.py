#!/usr/bin/env python3

import os
import re
import speedtest
import subprocess
import socket
import requests
import json


def check_internet_connection():
    try:
        subprocess.check_output(["ping", "-c", "1", "8.8.8.8"])
        internet_connection_status = "connected"
    except subprocess.CalledProcessError:
        internet_connection_status = "not connected"

    return internet_connection_status


def test_internet_speed():
    try:
        st = speedtest.Speedtest()
        #print("Testing internet speed...")

        # Perform the download speed test
        download_speed = st.download() / 1000000  # Convert to Mbps

        # Perform the upload speed test
        upload_speed = st.upload() / 1000000  # Convert to Mbps

        servernames = []
        st.get_servers(servernames)
        data = st.get_config()
        isp = data["client"]["isp"]

        # Print the results
        # print("Download Speed: {:.2f} Mbps".format(download_speed))
        # print("Upload Speed: {:.2f} Mbps".format(upload_speed))

        return "{:,.2f}".format(download_speed), "{:,.2f}".format(upload_speed), isp

    except speedtest.SpeedtestException as e:
        # print("An error occurred during the speed test:", str(e))
        return 0, 0, "unknown"
    


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def request_post(data_payload):

    index = "speedtest"
    sourcetype = "_json"
    source = "ip_mac"
    hec_token = f"Splunk {os.getenv('HEC_TOKEN_SPEEDTEST')}"
    print(hec_token)
    splunk_data_payload = '{"event": ' + data_payload + '}'
    endpoint = "event"

    hec_url = f"https://{os.getenv('HEC_IP')}:{os.getenv('HEC_PORT')}/services/collector/{endpoint}?index={index}&sourcetype={sourcetype}&source={source}"

    r = requests.post(hec_url,
                      data=splunk_data_payload,
                      headers={"Authorization": hec_token},
                      verify=False)

    return r.text


def test_and_send():

    results = {}

    results["hostname"] = socket.gethostname()
    results["ip_external"] = requests.get("https://api.ipify.org").text
    results["ip_internal"] = get_ip()
    results["internet_connection_status"] = check_internet_connection()

    results["download_speed"], results["upload_speed"], results["isp"] = test_internet_speed()
    json_results = json.dumps(results) 
    #print(json_results)

    r = request_post(json_results)
    #print(f'INFO : Sent data payload with outcome - {json.loads(r)["text"]}')


def main():

    result = subprocess.run(["curl ifconfig.me"], shell=True, capture_output=True, text=True)
    print(f"Server External IP address at start : {result.stdout}")

    test_and_send()

    # Change up the Virgin link to be higher priority by adding a routing table record with a lower metric
    result = subprocess.run(["sudo ip route add default via 192.168.0.1 metric 102"], shell=True, capture_output=True, text=True)
    result = subprocess.run(["curl ifconfig.me"], shell=True, capture_output=True, text=True)
    print(f"Server External IP address changed to : {result.stdout}")

    test_and_send()

    result = subprocess.run(["sudo ip route del default via 192.168.0.1 metric 102"], shell=True, capture_output=True, text=True)
    result = subprocess.run(["curl ifconfig.me"], shell=True, capture_output=True, text=True)
    print(f"Server External IP address changed back to : {result.stdout}")

if __name__ == "__main__":

    main()