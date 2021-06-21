#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import argparse
import os
import sys
import toml
import base64
import yaml


SYNCTHING_DOCKER_IMAGE = 'syncthing/syncthing:latest'

DEBUG_DOCKER_IMAGE = 'praqma/network-multitool'

# IfNotPresent or Always
DEFAULT_IMAGEPULLPOLICY = 'Always'

SERVICE_LIST = [
    'network',
    'consensus',
    'executor',
    'storage',
    'controller',
    'kms',
]


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() == 'false':
        return False
    elif value.lower() == 'true':
        return True
    raise ValueError(f'{value} is not a valid boolean value')


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--work_dir', default='.', help='The output director of config files.')
    
    parser.add_argument(
        '--chain_name', default='test-chain', help='The name of chain.')

    parser.add_argument(
        '--service_config', default='./service-config.toml', help='Config file about service information.')

    parser.add_argument(
        '--kms_passwords', help='Password list of kms.')

    parser.add_argument(
        '--lbs_tokens',
        help='The token list of LBS.')

    parser.add_argument(
        '--node_ports',
        help='The list of start port of Nodeport.')

    parser.add_argument(
        '--pvc_names', help='The list of persistentVolumeClaim names.')
    
    parser.add_argument(
        '--need_debug',
        type=str_to_bool,
        default=False,
        help='Is need debug container')

    parser.add_argument(
        '--need_monitor',
        type=str_to_bool,
        default=False,
        help='Is need monitor')

    parser.add_argument(
        '--state_db_user', default='citacloud', help='User of state db.')

    parser.add_argument(
        '--state_db_password', default='citacloud', help='Password of state db.')

    parser.add_argument(
        '--docker_registry', help='Registry of docker images.')

    parser.add_argument(
        '--docker_image_namespace', help='Namespace of docker images.')

    args = parser.parse_args()
    return args


# pod name is {chain_name}-{index}
def get_node_pod_name(index, chain_name):
    return '{}-{}'.format(chain_name, index)


def gen_kms_secret(kms_password, secret_name):
    bpwd = bytes(kms_password, encoding='utf8')
    b64pwd = base64.b64encode(bpwd)
    b64pwd_str = b64pwd.decode('utf-8')
    secret = {
        'apiVersion': 'v1',
        'kind': 'Secret',
        'metadata': {
            'name': secret_name,
        },
        'type': 'Opaque',
        'data': {
            'key_file': b64pwd_str
        }
    }
    return secret


def gen_grpc_service(chain_name, node_port):
    grpc_service = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'name': '{}-node-port'.format(chain_name)
        },
        'spec': {
            'type': 'NodePort',
            'ports': [
                {
                    'port': 50004,
                    'targetPort': 50004,
                    'nodePort': node_port,
                    'name': 'rpc',
                },
            ],
            'selector': {
                'chain_name': chain_name
            }
        }
    }
    return grpc_service


def gen_network_secret_name(chain_name, i):
    return '{}-{}-network-secret'.format(chain_name, i)


def gen_network_secret(chain_name, i):
    network_key = '0x' + os.urandom(32).hex()
    netwok_secret = {
        'apiVersion': 'v1',
        'kind': 'Secret',
        'metadata': {
            'name': gen_network_secret_name(chain_name, i),
        },
        'type': 'Opaque',
        'data': {
            'network-key': base64.b64encode(bytes(network_key, encoding='utf8')).decode('utf-8')
        }
    }
    return netwok_secret


def gen_network_service(i, chain_name):
    network_service = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'name': get_node_pod_name(i, chain_name)
        },
        'spec': {
            'ports': [
                {
                    'port': 40000,
                    'targetPort': 40000,
                    'name': 'network',
                },
                {
                    'port': 22000,
                    'targetPort': 22000,
                    'name': 'syncthing',
                },
                {
                    'port': 8384,
                    'targetPort': 8384,
                    'name': 'gui',
                }
            ],
            'selector': {
                'node_name': get_node_pod_name(i, chain_name)
            }
        }
    }
    return network_service

def gen_monitor_service(i, chain_name, node_port):
    monitor_service = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'name': 'monitor-{}-{}'.format(chain_name, i)
        },
        'spec': {
            'type': 'NodePort',
            'ports': [
                {
                    'port': 9256,
                    'targetPort': 9256,
                    'nodePort': node_port + 1 + 5 * i,
                    'name': 'process',
                },
                {
                    'port': 9349,
                    'targetPort': 9349,
                    'nodePort': node_port + 1 + 5 * i + 1,
                    'name': 'exporter',
                },
            ],
            'selector': {
                'node_name': get_node_pod_name(i, chain_name)
            }
        }
    }
    return monitor_service

def gen_executor_service(i, chain_name, node_port, is_chaincode_executor):
    executor_service = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'name': 'executor-{}-{}'.format(chain_name, i)
        },
        'spec': {
            'type': 'NodePort',
            'ports': [
                {
                    'port': 50002,
                    'targetPort': 50002,
                    'nodePort': node_port + 1 + 5 * i + 4,
                    'name': 'call',
                },
            ],
            'selector': {
                'node_name': get_node_pod_name(i, chain_name)
            }
        }
    }
    if is_chaincode_executor:
        chaincode_port = {
            'port': 7052,
            'targetPort': 7052,
            'nodePort': node_port + 1 + 5 * i + 2,
            'name': 'chaincode',
        }
        eventhub_port = {
            'port': 7053,
            'targetPort': 7053,
            'nodePort': node_port + 1 + 5 * i + 3,
            'name': 'eventhub',
        }
        executor_service['spec']['ports'].append(chaincode_port)
        executor_service['spec']['ports'].append(eventhub_port)
    return executor_service


def custom_docker_image(default_docker_image, docker_registry, docker_image_namespace):
    if all([docker_registry, docker_image_namespace]):
        return '{}:{}/{}'.format(docker_registry, docker_image_namespace, default_docker_image.split('/')[-1])
    else:
        return default_docker_image


def gen_node_deployment(i, service_config, chain_name, pvc_name, state_db_user, state_db_password, is_need_monitor, kms_secret_name, is_need_debug, docker_registry, docker_image_namespace):
    containers = []
    if is_need_debug:
        debug_container = {
            'image': custom_docker_image(DEBUG_DOCKER_IMAGE, docker_registry, docker_image_namespace),
            'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
            'name': 'debug',
            'ports': [
                    {
                        'containerPort': 9999,
                        'protocol': 'TCP',
                        'name': 'debug',
                    },
            ],
            'env': [
                {
                    'name': 'HTTP_PORT',
                    'value': '9999',
                },
            ],
            'volumeMounts': [
                {
                    'name': 'datadir',
                    'subPath': get_node_pod_name(i, chain_name),
                    'mountPath': '/data',
                }
            ],
        }
        containers.append(debug_container)
    syncthing_container = {
        'image': custom_docker_image(SYNCTHING_DOCKER_IMAGE, docker_registry, docker_image_namespace),
        'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
        'name': 'syncthing',
        'ports': [
                {
                    'containerPort': 22000,
                    'protocol': 'TCP',
                    'name': 'sync',
                },
                {
                    'containerPort': 8384,
                    'protocol': 'TCP',
                    'name': 'gui',
                }
        ],
        'volumeMounts': [
            {
                'name': 'datadir',
                'subPath': get_node_pod_name(i, chain_name),
                'mountPath': '/var/syncthing',
            }
        ],
        'env': [
            {
                'name': 'PUID',
                'value': '0',
            },
            {
                'name': 'PGID',
                'value': '0',
            },
        ]
    }
    containers.append(syncthing_container)
    for service in service_config['services']:
        if service['name'] == 'network':
            network_container = {
                'image': custom_docker_image(service['docker_image'], docker_registry, docker_image_namespace),
                'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
                'name': service['name'],
                'ports': [
                    {
                        'containerPort': 40000,
                        'protocol': 'TCP',
                        'name': 'network',
                    },
                    {
                        'containerPort': 50000,
                        'protocol': 'TCP',
                        'name': 'grpc',
                    }
                ],
                'command': [
                    'sh',
                    '-c',
                    service['cmd'],
                ],
                'workingDir': '/data',
                'volumeMounts': [
                    {
                        'name': 'datadir',
                        'subPath': get_node_pod_name(i, chain_name),
                        'mountPath': '/data',
                    },
                    {
                        'name': 'network-key',
                        'mountPath': '/network',
                        'readOnly': True,
                    },
                ],
            }
            containers.append(network_container)
        elif service['name'] == 'consensus':
            consensus_container = {
                'image': custom_docker_image(service['docker_image'], docker_registry, docker_image_namespace),
                'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
                'name': service['name'],
                'ports': [
                    {
                        'containerPort': 50001,
                        'protocol': 'TCP',
                        'name': 'grpc',
                    }
                ],
                'command': [
                    'sh',
                    '-c',
                    service['cmd'],
                ],
                'workingDir': '/data',
                'volumeMounts': [
                    {
                        'name': 'datadir',
                        'subPath': get_node_pod_name(i, chain_name),
                        'mountPath': '/data',
                    },
                ],
            }
            containers.append(consensus_container)
        elif service['name'] == 'executor':
            executor_container = {
                'image': custom_docker_image(service['docker_image'], docker_registry, docker_image_namespace),
                'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
                'name': service['name'],
                'ports': [
                    {
                        'containerPort': 50002,
                        'protocol': 'TCP',
                        'name': 'grpc',
                    }
                ],
                'command': [
                    'sh',
                    '-c',
                    service['cmd'],
                ],
                'workingDir': '/data',
                'volumeMounts': [
                    {
                        'name': 'datadir',
                        'subPath': get_node_pod_name(i, chain_name),
                        'mountPath': '/data',
                    },
                ],
            }
            # if executor is chaincode
            # add chaincode_port for executor
            # add chaincode_container
            if "chaincode" in service['docker_image']:
                chaincode_port = {
                    'containerPort': 7052,
                    'protocol': 'TCP',
                    'name': 'chaincode',
                }
                executor_container['ports'].append(chaincode_port)
                eventhub_port = {
                    'containerPort': 7053,
                    'protocol': 'TCP',
                    'name': 'eventhub',
                }
                executor_container['ports'].append(eventhub_port)
                if "chaincode_ext" in service['docker_image']:
                    state_db_container = {
                        'image': custom_docker_image('couchdb', docker_registry, docker_image_namespace),
                        'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
                        'name': "couchdb",
                        'ports': [
                            {
                                'containerPort': 5984,
                                'protocol': 'TCP',
                                'name': 'couchdb',
                            }
                        ],
                        'volumeMounts': [
                            {
                                'name': 'datadir',
                                'subPath': get_node_pod_name(i, chain_name),
                                'mountPath': '/opt/couchdb/data',
                            },
                        ],
                        'env': [
                            {
                                'name': 'COUCHDB_USER',
                                'value': state_db_user,
                            },
                            {
                                'name': 'COUCHDB_PASSWORD',
                                'value': state_db_password,
                            },
                        ],
                    }
                    containers.append(state_db_container)
                    # add --couchdb-username username --couchdb-password password
                    executor_ext_cmd = service['cmd'] + " --couchdb-username " + state_db_user + " --couchdb-password " + state_db_password
                    executor_container['command'] = [
                        'sh',
                        '-c',
                        executor_ext_cmd,
                    ]
            containers.append(executor_container)
        elif service['name'] == 'storage':
            storage_container = {
                'image': custom_docker_image(service['docker_image'], docker_registry, docker_image_namespace),
                'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
                'name': service['name'],
                'ports': [
                    {
                        'containerPort': 50003,
                        'protocol': 'TCP',
                        'name': 'grpc',
                    }
                ],
                'command': [
                    'sh',
                    '-c',
                    service['cmd'],
                ],
                'workingDir': '/data',
                'volumeMounts': [
                    {
                        'name': 'datadir',
                        'subPath': get_node_pod_name(i, chain_name),
                        'mountPath': '/data',
                    },
                ],
            }
            containers.append(storage_container)
        elif service['name'] == 'controller':
            controller_container = {
                'image': custom_docker_image(service['docker_image'], docker_registry, docker_image_namespace),
                'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
                'name': service['name'],
                'ports': [
                    {
                        'containerPort': 50004,
                        'protocol': 'TCP',
                        'name': 'grpc',
                    }
                ],
                'command': [
                    'sh',
                    '-c',
                    service['cmd'],
                ],
                'workingDir': '/data',
                'volumeMounts': [
                    {
                        'name': 'datadir',
                        'subPath': get_node_pod_name(i, chain_name),
                        'mountPath': '/data',
                    },
                ],
            }
            containers.append(controller_container)
        elif service['name'] == 'kms':
            kms_container = {
                'image': custom_docker_image(service['docker_image'], docker_registry, docker_image_namespace),
                'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
                'name': service['name'],
                'ports': [
                    {
                        'containerPort': 50005,
                        'protocol': 'TCP',
                        'name': 'grpc',
                    }
                ],
                'command': [
                    'sh',
                    '-c',
                    service['cmd'],
                ],
                'workingDir': '/data',
                'volumeMounts': [
                    {
                        'name': 'datadir',
                        'subPath': get_node_pod_name(i, chain_name),
                        'mountPath': '/data',
                    },
                    {
                        'name': 'kms-key',
                        'mountPath': '/kms',
                        'readOnly': True,
                    },
                ],
            }
            containers.append(kms_container)
        else:
            print("unexpected service")
            sys.exit(1)

    if is_need_monitor:
        monitor_process_container = {
            'image': custom_docker_image('citacloud/monitor-process-exporter:0.4.1', docker_registry, docker_image_namespace),
            'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
            'name': 'monitor-process',
            'ports': [
                {
                    'containerPort': 9256,
                    'protocol': 'TCP',
                    'name': 'process',
                }
            ],
            'args': [
                '--procfs',
                '/proc',
                '--config.path',
                '/config/process_list.yml'
            ],
            'workingDir': '/data',
            'volumeMounts': [
                {
                    'name': 'datadir',
                    'subPath': get_node_pod_name(i, chain_name),
                    'mountPath': '/data',
                },
            ],
        }
        containers.append(monitor_process_container)
        monitor_citacloud_container = {
            'image': custom_docker_image('citacloud/monitor-citacloud-exporter:0.1.1', docker_registry, docker_image_namespace),
            'imagePullPolicy': DEFAULT_IMAGEPULLPOLICY,
            'name': 'monitor-citacloud',
            'ports': [
                {
                    'containerPort': 9349,
                    'protocol': 'TCP',
                    'name': 'exporter',
                }
            ],
            'args': [
                "--node-grpc-host",
                "localhost",
                "--node-grpc-port",
                "50004",
                "--node-data-folder",
                ".",
            ],
            'workingDir': '/data',
            'volumeMounts': [
                {
                    'name': 'datadir',
                    'subPath': get_node_pod_name(i, chain_name),
                    'mountPath': '/data',
                },
            ],
        }
        containers.append(monitor_citacloud_container)

    volumes = [
        {
            'name': 'kms-key',
            'secret': {
                'secretName': kms_secret_name
            }
        },
        {
            'name': 'network-key',
            'secret': {
                'secretName': gen_network_secret_name(chain_name, i)
            }
        },
        {
            'name': 'datadir',
            'persistentVolumeClaim': {
                'claimName': pvc_name,
            }
        },
    ]
    deployment = {
        'apiVersion': 'apps/v1',
        'kind': 'Deployment',
        'metadata': {
            'name': get_node_pod_name(i, chain_name),
            'labels': {
                'node_name': get_node_pod_name(i, chain_name),
                'chain_name': chain_name,
            }
        },
        'spec': {
            'replicas': 1,
            'selector': {
                'matchLabels': {
                    'node_name': get_node_pod_name(i, chain_name),
                }
            },
            'template': {
                'metadata': {
                    'labels': {
                        'node_name': get_node_pod_name(i, chain_name),
                        'chain_name': chain_name,
                    }
                },
                'spec': {
                    'shareProcessNamespace': True,
                    'containers': containers,
                    'volumes': volumes,
                }
            }
        }
    }
    return deployment


def find_docker_image(service_config, service_name):
    for service in service_config['services']:
        if service['name'] == service_name:
            return service['docker_image']


def load_service_config(service_config):
    return toml.load(service_config)


def verify_service_config(service_config):
    indexs = 1
    for service in service_config['services']:
        index = (SERVICE_LIST.index(service['name']) + 1) * 10
        indexs *= index

    if indexs != 10 * 20 * 30 * 40 * 50 * 60:
        print('There must be 6 services:', SERVICE_LIST)
        sys.exit(1)


def gen_kms_secret_name(chain_name):
    return 'kms-secret-{}'.format(chain_name)


# multi cluster
def gen_peers_net_addr(nodes, node_ports):
    return list(map(lambda ip, port: {'ip': ip, 'port': port}, nodes, node_ports))


def gen_sync_peers_mc(nodes, node_ports, sync_device_ids):
    return list(map(lambda ip, port, device_id: {'ip': ip, 'port': port + 1, 'device_id': device_id}, nodes, node_ports, sync_device_ids))


def gen_all_service(i, chain_name, node_port, token, is_need_monitor, is_need_debug, is_chaincode_executor):
    ports = [
        {
            'port': node_port,
            'targetPort': 40000,
            'name': 'network',
        },
        {
            'port': node_port + 1,
            'targetPort': 22000,
            'name': 'sync',
        },
        {
            'port': node_port + 2,
            'targetPort': 50004,
            'name': 'rpc',
        },
        {
            'port': node_port + 3,
            'targetPort': 50002,
            'name': 'call',
        },
    ]
    if is_need_monitor:
        process_port = {
            'port': node_port + 4,
            'targetPort': 9256,
            'name': 'process',
        }
        ports.append(process_port)
        exporter_port = {
            'port': node_port + 5,
            'targetPort': 9349,
            'name': 'exporter',
        }
        ports.append(exporter_port)
    if is_chaincode_executor:
        chaincode_port = {
            'port': node_port + 6,
            'targetPort': 7052,
            'name': 'chaincode',
        }
        ports.append(chaincode_port)
        eventhub_port = {
            'port': node_port + 7,
            'targetPort': 7053,
            'name': 'eventhub',
        }
        ports.append(eventhub_port)
    if is_need_debug:
        debug_port = {
            'port': node_port + 8,
            'targetPort': 9999,
            'name': 'debug',
        }
        ports.append(debug_port)
    all_service = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'annotations': {
                'service.beta.kubernetes.io/alibaba-cloud-loadbalancer-id': token,
                'service.beta.kubernetes.io/alicloud-loadbalancer-force-override-listeners': 'true',
                'service.beta.kubernetes.io/alibaba-cloud-loadbalancer-health-check-interval': "50"
            },
            'name': 'all-{}-{}'.format(chain_name, i)
        },
        'spec': {
            'type': 'LoadBalancer',
            'ports': ports,
            'selector': {
                'node_name': get_node_pod_name(i, chain_name)
            }
        }
    }
    return all_service


def gen_kms_secret_name_mc(chain_name, i):
    return 'kms-secret-{}-{}'.format(chain_name, i)


def run_operator(args, work_dir):
    # load service_config
    service_config = load_service_config(args.service_config)
    print("service_config:", service_config)

    # verify service_config
    verify_service_config(service_config)

    lbs_tokens = args.lbs_tokens.split(',')
    kms_passwords = args.kms_passwords.split(',')
    node_ports = list(map(lambda x : int(x), args.node_ports.split(',')))
    pvc_names = args.pvc_names.split(',')

    peers_count = len(kms_passwords)
    if len(lbs_tokens) != peers_count:
        print('The len of lbs_tokens is invalid')
        sys.exit(1)

    if len(node_ports) != peers_count:
        print('The len of node_ports is invalid')
        sys.exit(1)
    
    if len(pvc_names) != peers_count:
        print('The len of pvc_names is invalid')
        sys.exit(1)

    # is chaincode executor
    executor_docker_image = find_docker_image(service_config, "executor")
    is_chaincode_executor = "chaincode" in executor_docker_image

    # generate k8s yaml
    for i in range(peers_count):
        k8s_config = []
        kms_secret = gen_kms_secret(kms_passwords[i], gen_kms_secret_name_mc(args.chain_name, i))
        k8s_config.append(kms_secret)
        netwok_secret = gen_network_secret(args.chain_name, i)
        k8s_config.append(netwok_secret)
        deployment = gen_node_deployment(i, service_config, args.chain_name, pvc_names[i], args.state_db_user, args.state_db_password, args.need_monitor, gen_kms_secret_name_mc(args.chain_name, i), args.need_debug, args.docker_registry, args.docker_image_namespace)
        k8s_config.append(deployment)
        all_service = gen_all_service(i, args.chain_name, node_ports[i], lbs_tokens[i], args.need_monitor, args.need_debug, is_chaincode_executor)
        k8s_config.append(all_service)
        # write k8s_config to yaml file
        yaml_ptah = os.path.join(work_dir, '{}-{}.yaml'.format(args.chain_name, i))
        print("yaml_ptah:{}", yaml_ptah)
        with open(yaml_ptah, 'wt') as stream:
            yaml.dump_all(k8s_config, stream, sort_keys=False)

    print("Done!!!")


def main():
    args = parse_arguments()
    print("args:", args)
    work_dir = os.path.abspath(args.work_dir)
    run_operator(args, work_dir)


if __name__ == '__main__':
    main()
