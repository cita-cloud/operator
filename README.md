# cita_cloud_operator

创建部署到`k8s`集群的`yaml`文件。

### 依赖

* python 3

安装依赖包:

```
pip install -r requirements.txt
```

### 用法

```
$ ./cita_cloud_operator.py --help
usage: cita_cloud_operator.py [-h] [--work_dir WORK_DIR] [--chain_name CHAIN_NAME] [--service_config SERVICE_CONFIG]
                              [--kms_passwords KMS_PASSWORDS] [--lbs_tokens LBS_TOKENS] [--node_ports NODE_PORTS] [--pvc_names PVC_NAMES]
                              [--need_debug NEED_DEBUG] [--need_monitor NEED_MONITOR] [--state_db_user STATE_DB_USER]
                              [--state_db_password STATE_DB_PASSWORD] [--image_pull_policy IMAGE_PULL_POLICY]
                              [--docker_registry DOCKER_REGISTRY] [--docker_image_namespace DOCKER_IMAGE_NAMESPACE]
                              [--node_addresses NODE_ADDRESSES]

optional arguments:
  -h, --help            show this help message and exit
  --work_dir WORK_DIR   The output director of config files.
  --chain_name CHAIN_NAME
                        The name of chain.
  --service_config SERVICE_CONFIG
                        Config file about service information.
  --kms_passwords KMS_PASSWORDS
                        Password list of kms.
  --lbs_tokens LBS_TOKENS
                        The token list of LBS.
  --node_ports NODE_PORTS
                        The list of start port of Nodeport.
  --pvc_names PVC_NAMES
                        The list of persistentVolumeClaim names.
  --need_debug NEED_DEBUG
                        Is need debug container
  --need_monitor NEED_MONITOR
                        Is need monitor
  --state_db_user STATE_DB_USER
                        User of state db.
  --state_db_password STATE_DB_PASSWORD
                        Password of state db.
  --image_pull_policy IMAGE_PULL_POLICY
                        image pull policy, can be IfNotPresent or Always
  --docker_registry DOCKER_REGISTRY
                        Registry of docker images.
  --docker_image_namespace DOCKER_IMAGE_NAMESPACE
                        Namespace of docker images.
  --node_addresses NODE_ADDRESSES
                        use node address name mode instead of serial number.
```

### 例子

```
./cita_cloud_operator.py --lbs_tokens lb-bp12,lb-bp34,lb-bp56,lb-bp78 --kms_passwords 123456,123456,123456,123456 --node_ports 30000,30010,30020,30030 --pvc_names nas-pvc,nas-pvc,nas-pvc,nas-pvc --need_debug true
args: Namespace(work_dir='.', chain_name='test-chain', service_config='./service-config.toml', kms_passwords='123456,123456,123456,123456', lbs_tokens='lb-bp12,lb-bp34,lb-bp56,lb-bp78', node_ports='30000,30010,30020,30030', pvc_names='nas-pvc,nas-pvc,nas-pvc,nas-pvc', need_debug=True, need_monitor=False, state_db_user='citacloud', state_db_password='citacloud')
service_config: {'services': [{'name': 'network', 'docker_image': 'citacloud/network_p2p', 'cmd': 'network run -p 50000 -k /network/network-key'}, {'name': 'consensus', 'docker_image': 'citacloud/consensus_bft', 'cmd': 'consensus run -p 50001'}, {'name': 'executor', 'docker_image': 'citacloud/executor_evm', 'cmd': 'executor run -p 50002'}, {'name': 'storage', 'docker_image': 'citacloud/storage_rocksdb', 'cmd': 'storage run -p 50003'}, {'name': 'controller', 'docker_image': 'citacloud/controller', 'cmd': 'controller run -p 50004'}, {'name': 'kms', 'docker_image': 'citacloud/kms_sm', 'cmd': 'kms run -p 50005 -k /kms/key_file'}]}
yaml_ptah:{} /path/to/operator/test-chain-0.yaml
yaml_ptah:{} /path/to/operator/test-chain-1.yaml
yaml_ptah:{} /path/to/operator/test-chain-2.yaml
yaml_ptah:{} /path/to/operator/test-chain-3.yaml
Done!!!
```

注意：

1. `kms_passwords`,`lbs_tokens`,`node_ports`,`pvc_names` 四个参数的值均为数组，以逗号分割。值的数量都跟链的节点数保持一致，且按照节点序号排列，顺序不能乱。
2. `kms_passwords`参数要和创建节点配置文件时的参数保持一致。
3. 配置`node_addresses`节点的用户名将会变成`<chain name>-<node address>`
