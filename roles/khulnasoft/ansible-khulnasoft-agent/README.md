Ansible Playbook - Khulnasoft agent
==============================

This role will install and configure a Khulnasoft Agent.

OS Requirements
----------------

This role is compatible with:
 * Red Hat
 * CentOS
 * Fedora
 * Debian
 * Ubuntu


Role Variables
--------------

* `khulnasoft_managers`: Collection of Khulnasoft Managers' IP address, port, and protocol used by the agent
* `khulnasoft_agent_authd`: Collection with the settings to register an agent using authd.

Playbook example
----------------

The following is an example of how this role can be used:

     - hosts: all:!khulnasoft-manager
       roles:
         - ansible-khulnasoft-agent
       vars:
         khulnasoft_managers:
           - address: 127.0.0.1
             port: 1514
             protocol: tcp
             api_port: 55000
             api_proto: 'http'
             api_user: 'ansible'
         khulnasoft_agent_authd:
           registration_address: 127.0.0.1
           enable: true
           port: 1515
           ssl_agent_ca: null
           ssl_auto_negotiate: 'no'


License and copyright
---------------------

WAZUH Copyright (C) 2016, Khulnasoft Inc. (License GPLv3)

### Based on previous work from dj-wasabi

  - https://github.com/dj-wasabi/ansible-ossec-server

### Modified by Khulnasoft

The playbooks have been modified by Khulnasoft, including some specific requirements, templates and configuration to improve integration with Khulnasoft ecosystem.
