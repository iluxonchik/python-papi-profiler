import time
import argparse
from pathlib import Path
from statistics import mean, stdev
from collections import defaultdict
from multiprocessing.pool import ThreadPool
from utils.colors import print_green, print_red, print_yellow
import papiprof.papihelper as papihelper
from papiprof.papihelper import (parse_ciphersuite_list_from_file, run_server, 
                     run_client, save_papi_metrics_to_file)

def get_next_or_default(iterator, default):
    try:
        return next(iterator)
    except StopIteration:
        return default

def build_key(sc_id, name, flags):
    flag_to_use = ''
    if flags.lower() != 'none':
        flag_to_use = f'[{flags}] '
    key = f'{flag_to_use}{sc_id}'
    return key

def create_output_directory_if_needed(out_dir):
    p = Path(out_dir)
    if not p.exists():
        print(f'\t[!] Creating {out_dir} since it did not exit.\n')
        p.mkdir(parents=True)

def init_funcname_dict_if_needed(all_profs, funcname, sc_id):
    funcname_dict = all_profs[funcname]

    if sc_id not in funcname_dict:
        funcname_dict[sc_id] = {}
        funcname_dict[sc_id]['num_runs'] = 0
        for metric_id in papihelper.ALL_METRICS:
            funcname_dict[sc_id][metric_id] = []
    
def append_profiling_results(all_profs, indiv_profs, sc_id):
    """
    indiv_profs structure:
        {
            'func_name': {
                'virttime: 123,
            }
        }
    """
    for funcname, metrics in indiv_profs.items():
        init_funcname_dict_if_needed(all_profs, funcname, sc_id)

        all_profs[funcname][sc_id]['num_runs'] += 1
        for metric_id in papihelper.ALL_METRICS:
            all_profs[funcname][sc_id][metric_id].append(metrics[metric_id])

def print_max_min_for_entity(prof_res, cs_id, entity, indent='\t'*3):
    print_green(f'{indent}{entity}---')
    
    #import pdb; pdb.set_trace()
    for func_name, values in prof_res.items():
        print_green(f'{indent}\t{func_name}:')

        cs_values = values[cs_id]

        for metric_name, metric_values in cs_values.items():
            if metric_name == 'num_runs':
                print_green(f'{indent}\t\t Number of runs: {metric_values}')
                continue

            print_green(f'{indent}\t\t{metric_name} Min: {min(metric_values)}')
            print_green(f'{indent}\t\t{metric_name} Max: {max(metric_values)}')
    print_green('')

def avg_profiling_results(prof_res, is_verbose=False):
    result = {}
    for func_name, cs_ids in prof_res.items():
        result[func_name] = {}
        for cs_id, metrics in cs_ids.items():
            result[func_name][cs_id] = {}
            for metric_name, metric_values in metrics.items():
                if metric_name == 'num_runs':
                    result[func_name][cs_id][metric_name] = metric_values
                    continue
                result[func_name][cs_id][metric_name] = {
                    'avg': mean(metric_values),
                    'stdev': stdev(metric_values)
                }
    return result

def run(client_path, server_path, num_runs, ciphers_path, 
        cli_bytes_start, cli_bytes_end, cli_bytes_step, 
        srv_bytes_start, srv_bytes_end, srv_bytes_step,
        out_path, is_verbose):
    SERVER_CALLGRIND_OUT_FILE = '{}/server.papi.out.{}.{}.{}'
    CLIENT_CALLGRIND_OUT_FILE = '{}/client.papi.out.{}.{}.{}'
    PROFILE_RESULTS_SRV = {}
    PROFILE_RESULTS_CLI = {}

    DEFAULT_BYTES_TO_SEND = 0

    timeout = 1

    print('Running with configurations: ')
    print(f'\tClient Path: {client_path}')
    print(f'\tSever Path: {server_path}')
    print(f'\tCiphesuite List Path: {ciphers_path}')
    print(f'\tclient bytes to send start, end, step: '
          f'{cli_bytes_start} {cli_bytes_end} {cli_bytes_step}')
    print(f'\tserver bytes to send start, end, step: '
          f'{srv_bytes_start} {srv_bytes_end} {srv_bytes_step}')
    print(f'\tOutput directory: {out_path}')
    print(f'\tTimeout: {timeout}')
    print(f'\tVerbose: {is_verbose}')

    print('\n')

    create_output_directory_if_needed(out_path)

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
    {
        'client' : {
                    <funcname>: {
                        <cipherid>: {
                            'num_runs': 123,
                            'avg:: 123,
                            'stdev': 123,
                        }
                    }
            }
    }
    """


    for sc_id, name, flags in ciphersuites:
        """
        1. Start server in thread 1
        2. Start client in thread 2
        3. Make sure that server ret code == 0
            else - continue
        4. Make sure that server ret coce == 0
            else - continue
        """
        cli_prof_res = defaultdict(dict)
        srv_prof_res = defaultdict(dict)

        srv_bytes_to_send_iter = iter(srv_bytes_to_send_list)
        cli_bytes_to_send_iter = iter(cli_bytes_to_send_list)

        for _ in max_iter:
            cli_bytes_to_send = get_next_or_default(cli_bytes_to_send_iter,
                                                        DEFAULT_BYTES_TO_SEND)
            srv_bytes_to_send = get_next_or_default(srv_bytes_to_send_iter,
                                                    DEFAULT_BYTES_TO_SEND)

            papi_out_srv = SERVER_CALLGRIND_OUT_FILE.format(out_path,
                                                            sc_id,
                                                            srv_bytes_to_send,
                                                            cli_bytes_to_send)
            papi_out_cli = CLIENT_CALLGRIND_OUT_FILE.format(out_path,
                                                            sc_id,
                                                            cli_bytes_to_send,
                                                            srv_bytes_to_send)
            for i in range(num_runs):
                pool = ThreadPool(processes=2)
                completed_iterations += 1
                print(f'--- Begin profiling for {sc_id} : {name} : {flags} [{completed_iterations}/{total_iterations} Run {i+1}/{num_runs}] ---')

                print(f'\tStarting server... (Out file: {papi_out_srv})')

                async_result_srv = pool.apply_async(run_server,
                                                    (server_path,
                                                    sc_id,
                                                    is_verbose,
                                                    srv_bytes_to_send
                                                    )
                                                    )

                print(f'\t\tWaiting {timeout} seconds for server to load...')
                time.sleep(timeout) # give the server time to start

                print(f'\tStarting client... (Out file: {papi_out_cli})')
                async_result_cli = pool.apply_async(run_client,
                                                    (client_path,
                                                    sc_id,
                                                    is_verbose,
                                                    cli_bytes_to_send
                                                    )
                                                    )

                srv_res = async_result_srv.get()
                cli_res = async_result_cli.get()

                srv_ret = srv_res[0]
                cli_ret = cli_res[0]

                srv_prof = srv_res[1]
                cli_prof = cli_res[1]

                pool.close()

                if srv_ret != 0 or cli_ret != 0:
                    print(f'\n\t[!!!] Non-zero return code from ciphersuite {sc_id} {name} {flags}')
                    print(f'\t\tServer: {srv_ret} Client: {cli_ret}')
                    print('\t\tSkipping to next ciphersuite...\n')
                    num_skipped_ciphersuites += 1

                    if -27 in (srv_ret, cli_ret):
                        # This here is sort of for debugging. If you're getting
                        # -27 return codes, make sure you're not compiling/linking
                        # with the "-pg" option
                        num_sigttou += 1

                    continue

                append_profiling_results(cli_prof_res, 
                                            cli_prof, sc_id) 

                append_profiling_results(srv_prof_res,
                                            srv_prof, sc_id)
            

            print_max_min_for_entity(cli_prof_res,
                                    sc_id,
                                    'client')

        
            print_max_min_for_entity(srv_prof_res,
                                    sc_id,
                                    'server')

            cli_prof_res_avg = avg_profiling_results(cli_prof_res)
            srv_prof_res_avg = avg_profiling_results(srv_prof_res)
            
            save_papi_metrics_to_file(cli_prof_res_avg, papi_out_cli,)
            save_papi_metrics_to_file(srv_prof_res_avg, papi_out_srv)

        print(f'--- End profiling for {sc_id} : {name} : {flags} [{completed_iterations}/{total_iterations}] ---\n')
            

    

    print('--- STATISTICS ---')
    print(f'\tTotal CipherSuites:{num_cipheruites}'
    f'\nMeasured: {num_cipheruites - num_skipped_ciphersuites}\n'
    f'Skipped: {num_skipped_ciphersuites}')
    print(f'Number of SIGTTOU signals: {num_sigttou}')

    if (num_sigttou > 0):
        print('[!!!] SIGTTOU singals detected! Make sure you\'re not compiling'
        '/linking with the "-pg" opiton (for gprof). You cannot use valgrind'
        ' and grpof together.')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description= 
    'Profile And Collect Metrics Into a JSON File\n'
    'All the tool outputs JSON files wit the following naming:'
    '\t[client|server].papi.out.<ciphersuite_id>.<num_bytes_sent>.'
    '<num_bytes_received>')

    parser.add_argument('client', type=str, help='client program path')
    parser.add_argument('server', type=str, help='server program path')
    parser.add_argument('runs', type=int, help='number of times to '
                                                'each program')
    parser.add_argument('ciphers', type=str, help='file containing a '
                        'list of '
                        'ciphersuite ids and their respective names.'
                        'Each line of the file must have the format: '
                        '<ciphersuite_id> <ciphersuite_name> '
                        '[arbitrary_info, ...]')
    parser.add_argument('cli_bytes_start', type=int, help='number of' 
                                 'bytes to send start value for client')
    parser.add_argument('cli_bytes_end', type=int, help='number of '
                                   'bytes to send end value for client')
    parser.add_argument('cli_bytes_step', type=int, help='number of '
                          'bytes to send step value for client')
    parser.add_argument('srv_bytes_start', type=int, help='number of '
                                 'bytes to send start value for server')
    parser.add_argument('srv_bytes_end', type=int, help='number of '
                                   'bytes to send end value for server')
    parser.add_argument('srv_bytes_step', type=int, help='number of '
                                  'bytes to send step value for server')
    parser.add_argument('out', type=str, help='profiled results '
                                               'output path')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        default=False, help='enable verbose output')

    args = parser.parse_args()
    run(args.client, 
        args.server, 
        args.runs, 
        args.ciphers,
        args.cli_bytes_start, 
        args.cli_bytes_end, 
        args.cli_bytes_step,
        args.srv_bytes_start, 
        args.srv_bytes_end, 
        args.srv_bytes_step,
        args.out, 
        args.verbose)
