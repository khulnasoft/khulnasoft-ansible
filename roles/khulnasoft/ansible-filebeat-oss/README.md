Ansible Role: Filebeat for Elastic Stack
------------------------------------

An Ansible Role that installs [Filebeat-oss](https://www.elastic.co/products/beats/filebeat), this can be used in conjunction with [ansible-khulnasoft-manager](https://github.com/khulnasoft/khulnasoft-ansible/ansible-khulnasoft-server).

Requirements
------------

This role will work on:
 * Red Hat
 * CentOS
 * Fedora
 * Debian
 * Ubuntu

Role Variables
--------------

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
  filebeat_output_indexer_hosts:
    - "localhost:9200"

```

License and copyright
---------------------

WAZUH Copyright (C) 2016, Khulnasoft Inc. (License GPLv3)

### Based on previous work from geerlingguy

 - https://github.com/geerlingguy/ansible-role-filebeat

### Modified by Khulnasoft

The playbooks have been modified by Khulnasoft, including some specific requirements, templates and configuration to improve integration with Khulnasoft ecosystem.
