# in top level directory, because of path problems with subprocess calls

import re
import os
import socket


class LogAnalysisResult:
    def __init__(self, dynamic_analysis_result, connected_ips=None):
        self.dynamic_analysis_result = dynamic_analysis_result
        self.connected_ips = connected_ips
        self.connected_hostnames_ips = dict()

        for connected_ip in self.connected_ips:
            hostname = socket.gethostbyaddr(connected_ip)
            if hostname not in self.connected_hostnames_ips:
                self.connected_hostnames_ips[hostname] = list()
            self.connected_hostnames_ips[hostname] += connected_ip

    def is_vulnerable(self):
        return self.connected_ips


def analyse_logs(dynamic_analysis_results):
    log_analysis_results = []
    for dynamic_analysis_result in dynamic_analysis_results:
        if dynamic_analysis_result.has_been_run:
            log_analysis_results += LogAnalysisResult(dynamic_analysis_result, analyse_log(dynamic_analysis_result))
        else:
            log_analysis_results += LogAnalysisResult(dynamic_analysis_result)
    return log_analysis_results


def analyse_log(dynamic_analysis_result):
    mitm_proxy = open(dynamic_analysis_result.get_mitm_proxy_log(), "r")
    # network = open(dynamic_analysis_result.get_network_monitor_log(), "r")

    ssl_regex = r"ssl_established,4:true"
    between_ssl_ip_regex = r"(?!ssl_established).*address,[0-9]{1,2}:[0-9]{1,2}:address,[0-9]{1,2}:[0-9]{1,2}:"
    ip_regex = r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})"
    get_ip_regex = ssl_regex + between_ssl_ip_regex + ip_regex

    ips = set()
    for line in mitm_proxy:
        if re.findall(get_ip_regex, line):
            print "regex: " + str(re.findall(get_ip_regex, line)) + ", line: " + line
        ips |= set(re.findall(get_ip_regex, line))

    print "ips: " + str(ips)

    connected_ips = ips
    # connected_ips = set()
    # for line in network:
    #     for ip in ips:
    #         ip_regex = r".*" + ip + r".*" # TODO: escape dots
    #         if re.match(ip_regex, line):
    #             connected_ips |= {ip}

    print "connected_ips: " + str(connected_ips)

    mitm_proxy.close()
    os.remove(mitm_proxy.name)
    # network.close()
    # os.remove(network.name)

    return connected_ips
