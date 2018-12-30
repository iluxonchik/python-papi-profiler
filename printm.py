import time
import argparse
from pathlib import Path
from statistics import mean, stdev
from collections import defaultdict
from os import listdir
from os.path import isfile, join
import json

from utils.colors import print_green, print_red, print_yellow
import papiprof.papihelper as papihelper
from papiprof.papihelper import (parse_ciphersuite_list_from_file, run_server, 
                     run_client, save_papi_metrics_to_file)

def cipher_id_to_name(id):
    idtoname = {
        '174': 'PSK',
        '182': 'RSA-PSK',
        '60': 'RSA',
        '178': 'DHE-PSK',
        '103': 'DHE-RSA',
        '49189': 'ECDH-ECDSA',
        '49187': 'ECDHE-ECDSA',
        '49207': 'ECDHE-PSK',
        '49191': 'ECDHE-RSA',
        '49193': 'ECDH-RSA'
    }
    return idtoname[id]

def collect_metrics(files):
    res = defaultdict(dict)

    jsons = []

    for file in files:
        with open(file, 'r') as f:
            jsons.append(json.load(f))

    for jmetric in jsons:
        for metric_name, cipher_metric in jmetric.items():
            metric_res = res[metric_name]
            for cipher_id, measurments in cipher_metric.items():
                cipher_id_name = cipher_id_to_name(cipher_id)
                for measurment_name, value_dict in measurments.items():
                    if measurment_name == 'num_runs':
                        continue
                    if cipher_id_name not in res[metric_name].keys():
                        res[metric_name][cipher_id_name] = {}
                    if measurment_name not in res[metric_name][cipher_id_name].keys():
                        res[metric_name][cipher_id_name][measurment_name] = {}
                    res[metric_name][cipher_id_name][measurment_name] = value_dict
    return res

def print_metrics(metrics, selected_metrics, is_print_list):
    #import pdb; pdb.set_trace()
    if selected_metrics:
        metrics = {name : metrics[name] for name in selected_metrics}
    mes_virttime_avg = []
    mes_cycles_avg = []
    for metric_name, cipher_metric in metrics.items():
        print(metric_name)
        ciphers_order_1 = [
                            'PSK',
                            'RSA-PSK',
                            'RSA',
                            'ECDH-RSA',
                            'ECDH-ECDSA',
                            'ECDHE-PSK',
                            'ECDHE-RSA',
                            'ECDHE-ECDSA',
                            'DHE-PSK',
                            'DHE-RSA',
                          ]
        cipher_names_order_2 = [
                              'PSK',
                              'ECDHE-PSK',
                              'DHE-PSK',
                              'ECDH-RSA',
                              'ECDHE-RSA',
                              'DHE-RSA',
                              'RSA',
                              'RSA-PSK',
                              'ECDH-ECDSA',
                              'ECDHE-ECDSA'
                              ]
        cipher_names_order = ciphers_order_2

        for cipher_name in cipher_names_order:
            print('\t' + cipher_name)
            measurments = cipher_metric[cipher_name]

            for measurment_name, values in measurments.items():
                if measurment_name == 'virttime':
                    mes_virttime_avg.append(values['avg'])
                elif measurment_name == 'virtcyc':
                    mes_cycles_avg.append(values['avg'])

                avg_rnd = round(values['avg'])
                stdev_rnd = round(values['stdev'])
                print('\t'*2 + measurment_name)
                print('\t'*3 + f'AVG: {avg_rnd}' )
                print('\t'*3 + f'STD: {stdev_rnd}' )
        if is_print_list:
            print_green('** Virtual Time Average List**')
            for value in mes_virttime_avg:
                print(round(value))
            print('')
            print_green('** Virtual Cycles Average List**')
            for value in mes_cycles_avg:
                print(round(value))


def run(ciphers, path, is_client, is_server, chosen_measurments, 
        is_print_list, is_verbose):
    SERVER_CALLGRIND_OUT_FILE = '{}/server.papi.out.{}.{}.{}'
    CLIENT_CALLGRIND_OUT_FILE = '{}/client.papi.out.{}.{}.{}'
    PROFILE_RESULTS_SRV = {}
    PROFILE_RESULTS_CLI = {}

    entity = 'client' if is_client else 'server'
    
    print_green(f'Parsing {entity} results...\n')

    all_files = [join(path, f) for f in listdir(path) if isfile(join(path, f)) and f.startswith(entity)]

    collected_metrics = collect_metrics(all_files)
    print_metrics(collected_metrics, chosen_measurments, is_print_list)

    #import pdb; pdb.set_trace()

    """
    print('Parsing ciphersuties...',end='')
    ciphersuites = parse_ciphersuite_list_from_file(ciphers_path)
    num_cipheruites = len(ciphersuites)
    num_skipped_ciphersuites = 0
    completed_iterations = 0
    num_sigttou = 0
    ciphersuite_names = []  # display names in graph
    print('ok')

    if 0 in (srv_bytes_step, srv_bytes_end):
        print('\t[!] Setting server send bytes to zero')
        srv_bytes_start = 0
        srv_bytes_end = 1
        srv_bytes_step = 1

    if 0 in (cli_bytes_step, cli_bytes_end):
        print('\t[!] Setting client send bytes to zero')
        cli_bytes_start = 0
        cli_bytes_end = 1
        cli_bytes_step = 1

    srv_bytes_to_send_list = list(range(srv_bytes_start, srv_bytes_end, 
                                        srv_bytes_step))
    cli_bytes_to_send_list = list(range(cli_bytes_start, cli_bytes_end, 
                                        cli_bytes_step))

    max_iter = max(srv_bytes_to_send_list, cli_bytes_to_send_list)
    total_iterations = len(max_iter) * num_cipheruites
"""
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description= 
    'Print stats for PAPI profilings outputs'
    'All the tool outputs JSON files wit the following naming:'
    '\t[client|server].papi.out.<ciphersuite_id>.<num_bytes_sent>.'
    '<num_bytes_received>')

    parser.add_argument('ciphers', type=str, help='file containing a '
                        'list of '
                        'ciphersuite ids and their respective names.'
                        'Each line of the file must have the format: '
                        '<ciphersuite_id> <ciphersuite_name> '
                        '[arbitrary_info, ...]')
    parser.add_argument('path', type=str, help='path to folder with '
                                               'JSON profilings') 

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--client', default=False, 
                        action='store_true', help='present client metrics')
    group.add_argument('-s', '--server', default=False, action='store_true', 
                        help='present server metrics')
    parser.add_argument('-m', '--metrics', nargs='+', help='show the '
                       'selected metric(s) only', default=[] )
    parser.add_argument('-p', '--print', help='print metrics list at the '
                        'end. Useful for copy/paste to Excel',
                        default=False, action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        default=False, help='enable verbose output')

    args = parser.parse_args()
    run(
        args.ciphers,
        args.path,
        args.client,
        args.server,
        args.metrics,
        args.print,
        args.verbose
        )
