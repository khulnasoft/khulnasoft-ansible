## Examples

The purpose of this section is to showcase a wide variety of examples on how `khulnasoft-ansible` can be used. Please use the files and content here as simple references designs for implementing and getting immediate value out of the playbooks in this repository.

From a design perspective, the plays within `khulnasoft-ansible` are meant to be run locally on each instance of your intended Khulnasoft deployment. The execution flow of the provisioning process is meant to gracefully handle interoperability in this manner, while also maintaining idempotency and configuration management. It is also possible to use these plays against a remote instance, although that is not the intended use case so it might not work in all cases.

----

## I want to...

* [Provision localhost as a standalone Khulnasoft](#provision-local-standalone)
* [Enable a user-defined HEC token](#provision-hec)
* [Access KhulnasoftWeb behind a reverse proxy](#enable-reverse-proxy)
* [Use a dynamic inventory](#provision-with-dynamic-inventory)
* [Provision Docker containers with khulnasoft-ansible](#provision-docker-containers)

---

## Provision local standalone

<details><summary markdown='span'><code>hosts</code> file inventory</summary><p></p>

```
localhost ansible_connection=local
```
</details><p></p>

<details><summary markdown='span'><code>default.yml</code></summary><p></p>

```yaml
---
ansible_post_tasks: null
ansible_pre_tasks: null
config:
baked: default.yml
defaults_dir: /tmp/defaults
env:
    headers: null
    var: KHULNASOFT_DEFAULTS_URL
    verify: true
host:
    headers: null
    url: null
    verify: true
max_delay: 60
max_retries: 3
max_timeout: 1200
hide_password: false
retry_delay: 3
retry_num: 60
wait_for_khulnasoft_retry_num: 60
shc_sync_retry_num: 60
khulnasoft:
    admin_user: admin
    app_paths:
        default: /opt/khulnasoft/etc/apps
        deployment: /opt/khulnasoft/etc/deployment-apps
        httpinput: /opt/khulnasoft/etc/apps/khulnasoft_httpinput
        idxc: /opt/khulnasoft/etc/master-apps
        shc: /opt/khulnasoft/etc/shcluster/apps
    enable_service: false
    exec: /opt/khulnasoft/bin/khulnasoft
    group: khulnasoft
    hec:
        enable: True
        ssl: True
        token: null
        port: 8088
    home: /opt/khulnasoft
    http_enableSSL: 0
    http_enableSSL_cert: null
    http_enableSSL_privKey: null
    http_enableSSL_privKey_password: null
    http_port: 8000
    idxc:
        label: idxc_label
        replication_factor: 3
        replication_port: 9887
        search_factor: 3
        secret: null
        pass4SymmKey: null
    ignore_license: false
    license_download_dest: /tmp/khulnasoft.lic
    opt: /opt
    password: helloworld
    pid: /opt/khulnasoft/var/run/khulnasoft/khulnasoftd.pid
    s2s_enable: true
    s2s_port: 9997
    search_head_cluster_url: null
    secret: null
    pass4SymmKey: null
    shc:
        label: shc_label
        replication_factor: 3
        replication_port: 9887
        secret: null
        pass4SymmKey: null
    smartstore: null
    svc_port: 8089
    tar_dir: khulnasoft
    user: khulnasoft
    wildcard_license: false
khulnasoft_home_ownership_enforcement: true
```
</details><p></p>

Execution command:
```
ansible-playbook --inventory hosts --connection local site.yml --extra-vars "@default.yml" 
```

---

## Provision HEC
The HTTP Event Collector (HEC) enables sending data directly to Khulnasoft via a HTTP endpoint and a token. Here's how you can enable it with a user-defined token (`abcd-1234-efgh-5678`).
<details><summary markdown='span'><code>hosts</code> file inventory</summary><p></p>

```
localhost ansible_connection=local
```
</details><p></p>

<details><summary markdown='span'><code>default.yml</code></summary><p></p>

```yaml
---
ansible_post_tasks: null
ansible_pre_tasks: null
config:
baked: default.yml
defaults_dir: /tmp/defaults
env:
    headers: null
    var: KHULNASOFT_DEFAULTS_URL
    verify: true
host:
    headers: null
    url: null
    verify: true
max_delay: 60
max_retries: 3
max_timeout: 1200
hide_password: false
retry_delay: 3
retry_num: 60
wait_for_khulnasoft_retry_num: 60
shc_sync_retry_num: 60
khulnasoft:
    admin_user: admin
    app_paths:
        default: /opt/khulnasoft/etc/apps
        deployment: /opt/khulnasoft/etc/deployment-apps
        httpinput: /opt/khulnasoft/etc/apps/khulnasoft_httpinput
        idxc: /opt/khulnasoft/etc/master-apps
        shc: /opt/khulnasoft/etc/shcluster/apps
    enable_service: false
    exec: /opt/khulnasoft/bin/khulnasoft
    group: khulnasoft
    hec:
        enable: True
        ssl: True
        token: abcd-1234-efgh-5678
        port: 8088
    home: /opt/khulnasoft
    http_enableSSL: 0
    http_enableSSL_cert: null
    http_enableSSL_privKey: null
    http_enableSSL_privKey_password: null
    http_port: 8000
    idxc:
        label: idxc_label
        replication_factor: 3
        replication_port: 9887
        search_factor: 3
        secret: null
    ignore_license: false
    license_download_dest: /tmp/khulnasoft.lic
    opt: /opt
    password: helloworld
    pid: /opt/khulnasoft/var/run/khulnasoft/khulnasoftd.pid
    s2s_enable: true
    s2s_port: 9997
    search_head_cluster_url: null
    secret: null
    shc:
        label: shc_label
        replication_factor: 3
        replication_port: 9887
        secret: null
    smartstore: null
    svc_port: 8089
    tar_dir: khulnasoft
    user: khulnasoft
    wildcard_license: false
khulnasoft_home_ownership_enforcement: true
```
</details><p></p>

Execution command:
```
ansible-playbook --inventory hosts --connection local site.yml --extra-vars "@default.yml" 
```

For this case, the `khulnasoft.hec.ssl` parameter will govern whether the HEC endpoint will be reachable over HTTP or HTTPS.

---

## Enable Reverse Proxy
A reverse proxy can be used to access Khulnasoft through some ingress controller resource or behind a load-balancer within your corporate firewall policy. Here's how you can enable KhulnasoftWeb to run behind a prefix route such as `/khulnasoftweb`.

<details><summary markdown='span'><code>default.yml</code></summary><p></p>

```yaml
---
ansible_post_tasks: null
ansible_pre_tasks: null
config:
baked: default.yml
defaults_dir: /tmp/defaults
env:
    headers: null
    var: KHULNASOFT_DEFAULTS_URL
    verify: true
host:
    headers: null
    url: null
    verify: true
max_delay: 60
max_retries: 3
max_timeout: 1200
hide_password: false
retry_delay: 3
retry_num: 60
wait_for_khulnasoft_retry_num: 60
shc_sync_retry_num: 60
khulnasoft:
    root_endpoint: /khulnasoftweb
    admin_user: admin
    app_paths:
        default: /opt/khulnasoft/etc/apps
        deployment: /opt/khulnasoft/etc/deployment-apps
        httpinput: /opt/khulnasoft/etc/apps/khulnasoft_httpinput
        idxc: /opt/khulnasoft/etc/master-apps
        shc: /opt/khulnasoft/etc/shcluster/apps
    enable_service: false
    exec: /opt/khulnasoft/bin/khulnasoft
    group: khulnasoft
    hec:
        enable: True
        ssl: True
        token: abcd-1234-efgh-5678
        port: 8088
    home: /opt/khulnasoft
    http_enableSSL: 0
    http_enableSSL_cert: null
    http_enableSSL_privKey: null
    http_enableSSL_privKey_password: null
    http_port: 8000
    idxc:
        label: idxc_label
        replication_factor: 3
        replication_port: 9887
        search_factor: 3
        secret: null
    ignore_license: false
    license_download_dest: /tmp/khulnasoft.lic
    opt: /opt
    password: helloworld
    pid: /opt/khulnasoft/var/run/khulnasoft/khulnasoftd.pid
    s2s_enable: true
    s2s_port: 9997
    search_head_cluster_url: null
    secret: null
    shc:
        label: shc_label
        replication_factor: 3
        replication_port: 9887
        secret: null
    smartstore: null
    svc_port: 8089
    tar_dir: khulnasoft
    user: khulnasoft
    wildcard_license: false
khulnasoft_home_ownership_enforcement: true
```
</details><p></p>

Execution command:
```
ansible-playbook --inventory hosts --connection local site.yml --extra-vars "@default.yml" 
```

After the command runs, you can access KhulnasoftWeb at <http://localhost:8000/khulnasoftweb>.

---

## Provision with Dynamic Inventory
Ansible enables the use of custom inventory scripts. For more information on how to do this and how to create your own inventory script, please go to Ansible's documentation on dynamic inventories.

This codebase includes an example of this, located at `inventory/environ.py`. This script is meant for local connection use and is the primary driver in making the official Khulnasoft Docker image successful. The `environ.py` converts environment variables into Ansible variables dynamically so there's no need for the `default.yml` from previous examples. However, in some cases, the `default.yml` is still necessary in order to consolidate state across multiple instances of a distributed deployment.

Execution command:
```
ansible-playbook --inventory inventory/environ.py --connection local site.yml
```

---

## Provision Docker Containers
The playbooks in this repository are already being used in the context of containers! For more information on how this works, please see the [docker-khulnasoft](https://github.com/khulnasoft/docker-khulnasoft/) project and learn how `khulnasoft-ansible` is incorporated.

---
