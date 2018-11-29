import json
import re
import subprocess
from collections import defaultdict

from utils.colors import print_green, print_red, print_yellow
from utils.jsonhelper import convert_dict_keys_to_str, write_json_to_file

METRIC_VIRTTIME = 'virttime'
METRIC_REALTIME = 'realtime'
METRIC_VIRTCYC = 'virtcyc'
METRIC_REALCYC = 'realcyc'

ALL_METRICS = (METRIC_VIRTTIME, METRIC_VIRTCYC)

def verbose_print(content, is_verbose):
    if is_verbose:
        print_yellow(f'DBG: {content}')

def parse_ciphersuite_list_from_file(file_path):
    """Parses a list of ciphersuites from a file.

    Format of file:
    CIPHERSUITE_ID[:id] CIPHERSUITE_NAME[:str] TAG[:str]
    """
    with open(file_path, 'r') as sc_file:
        ciphersuites = [line.strip().split(' ') for line in sc_file.readlines()]

    ciphersuites = [ciphersuite for ciphersuite in ciphersuites if len(ciphersuite) > 1]

    for i in range(0, len(ciphersuites)):
        ciphersuite = ciphersuites[i]
        if len(ciphersuite) < 3:
            ciphersuite.append('')
        elif len(ciphersuite) > 3:
            ciphersuites[i] = ciphersuite[0:2] + [' '.join(ciphersuite[2:])]
    return ciphersuites

def get_cc_from_papi_output(content, func_name):
    raise Exception('Not yet implemented')

def save_papi_metrics_to_file(metrics, filename):
    metrics_json = convert_dict_keys_to_str(metrics)
    write_json_to_file(metrics_json, filename)

def parse_output_into_metrics(output, is_verbose=False):
    """
    returns metrics: 
    {
        funcname : {
            virttime: 123,
            realtime: 123,
        }
    }
    """
    metrics = defaultdict(dict)

    for metric_name in ALL_METRICS:
        verbose_print(f'Parsing {metric_name}...', is_verbose)

        REGEX = fr'(?P<funcname>.+?)_{metric_name} (?P<value>\d+\n\r?)'
        matches = re.finditer(REGEX, output, flags=re.MULTILINE)

        for match in matches:
            match = match.groupdict()
            funcname = match['funcname']
            value = match['value']
            metrics[funcname][metric_name] = float(value)

            verbose_print(f'\tfuncname: {funcname}', is_verbose)
            verbose_print(f'\tvalue: {value}', is_verbose)
    
    return metrics


def get_cc_from_papi_file(papi_file, func_name):
    """Gets the number of CPU cycles for a function from a callgrind file."""
    with open(papi_file, 'r') as f:
        file_content = f.read()
    
    return get_cc_from_papi_output(file_content, func_name)

def run_server(server_path, ciphersuite_id, show_output=True,
               num_bytes_to_send=None):
    """
    {
        func_name : {
            virttime : 123,
            realtime: 123,
        }
    }
    """
    srv_args = [server_path, str(ciphersuite_id)]

    if num_bytes_to_send:
        srv_args.append(str(num_bytes_to_send))

    args = srv_args

    p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    return_code = p.returncode

    if (show_output):
        print(f'\n\nServer OUT:\n{stdout}')
        print(f'\n\nServer ERR:\n{stderr}')

    metrics = parse_output_into_metrics(stdout.decode(encoding='utf-8'), show_output)
    return (return_code, metrics)

def run_client(client_path, ciphersuite_id, show_output=True,
                num_bytes_to_send=None):

    cli_args = [client_path, str(ciphersuite_id)]

    if num_bytes_to_send:
        cli_args.append(str(num_bytes_to_send))

    args =  cli_args

    p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()



    return_code = p.returncode
      
    if (show_output):
        print(f'\n\nClient OUT:\n{stdout}')
        print(f'\n\nClient ERR:\n{stderr}')

    metrics = parse_output_into_metrics(stdout.decode(encoding='utf-8'), show_output)
    return (return_code, metrics)
