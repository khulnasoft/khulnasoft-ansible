# Execution

The Ansible plays in the `khulnasoft-ansible` project can be run in two ways: separately on each instance/host of the Khulnasoft Enterprise deployment, or through more traditional separation of control nodes and managed nodes. In the first method each host asynchronously sets itself up using Ansible roles to form the final desired topology which is most clearly displayed through the [docker-khulnasoft](https://github.com/khulnasoft/docker-khulnasoft) project. All execution methods are listed below.

--- 

## Navigation

* [Local](#local)
* [Embedded](#embedded)
* [Remote](#remote)

---

## Local
Local connection is the intended mode of using `khulnasoft-ansible`. The dynamic inventory script `environ.py` reads environment variables and maps them into Ansible run-time variables that determine how Khulnasoft Enterprise is setup. 

In order to bring up the most basic Khulnasoft standalone instance on a local host, you can run the following:

```bash
export KHULNASOFT_PASSWORD=helloworld
export KHULNASOFT_BUILD_URL=https://download.khulnasoft.com/products/khulnasoft/releases/8.0.3/linux/khulnasoft-8.0.3-a6754d8441bf-Linux-x86_64.tgz
export KHULNASOFT_USER=$(whoami)
export KHULNASOFT_GROUP=$(id -gn)

ansible-playbook --inventory inventory/environ.py --limit localhost site.yml
```

---

## Embedded
The embedded, or wrapper, mode of using `khulnasoft-ansible` involves treating this entire project as a package. See [these instructions](wrapper-example/README.md) on how to install `khulnasoft-ansible` on multiple target machines to bring up an indexer cluster.

---

## Remote
The more traditional and familiar approach to running Ansible can also be used with `khulnasoft-ansible`. This fits the use-case where `khulnasoft-ansible` is installed on some controller node (ex. your personal workstation, Ansible Tower, or Ansible AWX) and this controller uses the ssh connection to setup Khulnasoft on a series of target hosts. 

See [these instructions](remote/README.md) on how to install `khulnasoft-ansible` on multiple target machines to bring up an indexer cluster.
