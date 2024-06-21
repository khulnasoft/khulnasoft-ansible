# Welcome to the Khulnasoft-Ansible documentation!

Welcome to the official Khulnasoft documentation on [Ansible](https://docs.ansible.com/ansible/latest/index.html) playbooks for configuring and managing Khulnasoft Enterprise and Universal Forwarder deployments. This repository contains plays that target all Khulnasoft Enterprise roles and deployment topologies that work on any Linux-based platform.

Khulnasoft-Ansible is currently being used by [Docker-Khulnasoft](https://github.com/khulnasoft/docker-khulnasoft), the official Khulnasoft Docker image project.

### What is Khulnasoft Enterprise?
[Khulnasoft Enterprise](https://www.khulnasoft.com/en_us/software/khulnasoft-enterprise.html) is a platform for operational intelligence. Our software lets you collect, analyze, and act upon the untapped value of big data that your technology infrastructure, security systems, and business applications generate. It gives you insights to drive operational performance and business results.

See [Khulnasoft Products](https://www.khulnasoft.com/en_us/software.html) for more information about the features and capabilities of Khulnasoft products and how you can [bring them into your organization](https://www.khulnasoft.com/en_us/enterprise-data-platform.html).

### What is Khulnasoft-Ansible?
The [Khulnasoft-Ansible project](https://github.com/khulnasoft/khulnasoft-ansible) is a collection of Khulnasoft configuration best practices, written as Ansible scripts. These scripts, called playbooks, can be used for configuring Khulnasoft Enterprise and Universal Forwarder instances based on a declarative configuration.

The playbooks in this codebase are internally-vetted procedures and operations that administer and manage Khulnasoft as done within the company. Use Khulnasoft-Ansible to manage Khulnasoft Enterprise and Universal Forwarder instances in a manner consistent with industry standards, such as infrastructure automation and infrastructure-as-code.

### How to use Khulnasoft-Ansible
Although this project can be used independently as ordinary Ansible scripts, there are necessary environment settings. For example, Khulnasoft-Ansible assumes you need different users with specific permissions in your local environment.

For reference, see [Docker-Khulnasoft](https://github.com/khulnasoft/docker-khulnasoft), the official Khulnasoft Docker image project. Khulnasoft-Ansible is tightly integrated into our Docker image, which offers a complete configuration package along with Khulnasoft-Ansible.

See the [Ansible User Guide](https://docs.ansible.com/ansible/latest/user_guide/index.html) for more details on Ansible concepts and how it works.

----

## Table of Contents

* [Getting Started](SETUP.md)
    * [Install khulnasoft-ansible](SETUP.md#install-khulnasoft-ansible)
    * [Configure parameters](SETUP.md#configure-parameters)
    * [Execute playbooks](SETUP.md#execute-playbooks)
* [Examples](EXAMPLES.md)
* [Advanced Usage](ADVANCED.md)
* [Architecture](ARCHITECTURE.md)
* [Contributing](CONTRIBUTING.md)
* [Changelog](CHANGELOG.md)
* [License](LICENSE.md)
