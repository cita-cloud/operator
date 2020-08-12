# operator

将`cita-cloud`底层链运行在`Kubernetes`环境中，本项目实现一个`Operator`，用来在`k8s`集群中部署链的单个节点或者所有节点。将来还可以考虑集成软件版本升级，数据备份，增加/删除指定链的节点等运维操作。进一步还可以考虑集成配置生成，`SDK`网关，缓存服务，`Watch Tower`，甚至是合约`IDE`，合约编译服务等。

## `Operator`

`CRD`是`Kubernetes`为提高可扩展性，让开发者去自定义资源（如`Deployment`，`StatefulSet`等）的一种方法。

`CRD`仅仅是资源的定义，而`Controller`可以去监听`CRD`的`CRUD`事件来添加自定义业务逻辑。

`Operator`=`CRD`+`Controller`。

## `kubebuilder`

`kubebuilder`是一种工具，可以生成一个`Operator`工程以及相关的脚手架代码。

本项目使用`kubebuilder`生成最基础的工程文件。

相关文档参见：[英文](https://book.kubebuilder.io/quick-start.html)  [中文](https://blog.upweto.top/gitbooks/kubebuilder/)

## 设计

1. 每个微服务一个pod，端口固定，相互之间用域名访问。`KMS`单独部署并且可以多实例，但是是`stateful`的。
2. 网路端口和`Controller`的`RPC`服务要暴露出来，需要外部`ip`。
3. 存储和`KMS`微服务需要`PV`。
4. `KMS`需要保存密码。

## 步骤

1. 生成脚手架工程

   ```shell
   go mod init github.com/cita-cloud/operator
   kubebuilder init --domain citahub.com
   ```

   注意：生成的`Makefile`中需要用到`kustomize`命令，但是对于`Kubernetes 1.18`版本来说，这个命令已经集成进`kubectl`了。需要修改`Makefile`，将`kustomize build`替换为`kubectl kustomize` 。

2. 创建`API`

   ```shell
   kubebuilder create api --group cita-cloud --version v1 --kind SingleNode
   kubebuilder create api --group cita-cloud --version v1 --kind Cluster
   kubebuilder create api --group cita-cloud --version v1 --kind KMS
   ```

3. 定义`CRD`

   指定链的名字，`chain id`，节点列表，各个微服务的镜像，系统配置等信息。

4. 编写`Controller`逻辑

   调用`config-tool`生成链的配置。然后创建运行各个微服务的`Pod`，导出服务的`Service`，以及保存数据的`PV`等等。

5. 测试发布

   测试使用`minikube`在本机搭建`Kubernetes`环境。启动命令如下：

   ```shell
   minikube start --registry-mirror=https://xxx.mirror.aliyuncs.com --image-repository=registry.cn-hangzhou.aliyuncs.com/google_containers --vm-driver=docker --alsologtostderr -v=8 --base-image registry.cn-hangzhou.aliyuncs.com/google_containers/kicbase:v0.0.10
   ```

   

   