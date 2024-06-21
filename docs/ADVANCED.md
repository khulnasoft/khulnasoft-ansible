## Navigation

* [Inventory Script](#inventory-script)
    * [Supported environment variables](#supported-environment-variables)
    * [Additional Khulnasoft Universal Forwarder variables](#additional-khulnasoft-universal-forwarder-variables)
* [Defaults](#defaults)
    * [Loading defaults through file](#loading-defaults-through-file)
    * [Loading defaults through URL](#loading-defaults-through-url)
    * [Schema](#schema)
* [Apps](#apps)
* [SmartStore](#smartstore)
* [Custom khulnasoft-launch.conf](#custom-khulnasoft-launchconf)
* [Multi-cluster Search](#multi-cluster-search)

---

## Inventory Script
Khulnasoft-Ansible ships with an inventory script in `inventory/environ.py`. The script gathers user configurations from a local YAML file and/or OS environment variables and converts them into Ansible variables accessible in Ansible tasks.

### Supported environment variables

| Environment Variable Name | Description | Required for Standalone | Required for Search Head Clustering | Required for Index Clustering |
| --- | --- | --- | --- | --- |
| KHULNASOFT_BUILD_URL | URL of Khulnasoft build to be installed | no | no | no |
| KHULNASOFT_DEFAULTS_URL | URL of `default.yml` | no | no | no |
| KHULNASOFT_ALLOW_UPGRADE | Perform upgrade if target build version doesn't match installed version | no | no | no |
| KHULNASOFT_ROLE | The container’s current Khulnasoft Enterprise role. Supported Roles: `khulnasoft_standalone`, `khulnasoft_indexer`, `khulnasoft_deployer`, `khulnasoft_search_head`, etc. See [Roles](https://github.com/khulnasoft/khulnasoft-ansible/tree/develop/roles). | no | yes | yes |
| KHULNASOFT_HOSTNAME | Specify the instance's hostname. | no | no | no |
| DEBUG | Print Ansible vars to stdout (supports Docker logging) | no | no | no |
| KHULNASOFT_START_ARGS | Accept the license with `—accept-license` in this variable. The container will not start without it. | yes | yes | yes |
| KHULNASOFT_LICENSE_URI | URI we can fetch a Khulnasoft Enterprise license. This can be a local path, a remote URL, or ["Free"](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/MoreaboutKhulnasoftFree). | no | no | no |
| KHULNASOFT_IGNORE_LICENSE | Flag to disable any plays that would add a license. Set this env var to "true" if you do not want to license your installation. | no | no | no |
| KHULNASOFT_LICENSE_INSTALL_PATH | Path on filesystem where Khulnasoft license will be moved/downloaded to | no | no | no |
| KHULNASOFT_STANDALONE_URL | Comma-separated list of all Khulnasoft Enterprise standalone hosts (network alias) | no | no | no |
| KHULNASOFT_SEARCH_HEAD_URL | Comma-separated list of all Khulnasoft Enterprise search head hosts (network alias) | no | yes | yes |
| KHULNASOFT_INDEXER_URL| Comma-separated list of all Khulnasoft Enterprise indexer hosts (network alias) | no | yes | yes |
| KHULNASOFT_HEAVY_FORWARDER_URL | Comma-separated list of all Khulnasoft Enterprise heavy forwarder hosts (network alias) | no | no | no |
| KHULNASOFT_DEPLOYER_URL | One Khulnasoft Enterprise deployer host (network alias) | no | yes | no |
| KHULNASOFT_CLUSTER_MASTER_URL | One Khulnasoft Enterprise cluster master host (network alias) | no | no | yes |
| KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL | One Khulnasoft Enterprise search head host (network alias). Passing this ENV variable will enable search head clustering. | no | yes | no |
| KHULNASOFT_LICENSE_MASTER_URL | One Khulnasoft Enterprise license master host (network alias). Passing this ENV variable will enable license master setup. | no | no | no |
| KHULNASOFT_DEPLOYMENT_SERVER | One Khulnasoft host (network alias) that we use as a [deployment server](http://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Updating/Configuredeploymentclients). | no | no | no |
| KHULNASOFT_ADD | Comma-separated list of items to add to monitoring. Example: `KHULNASOFT_ADD=udp 1514,monitor /var/log/\*`. This will monitor the UDP port 1514 and `/var/log/\*` files. | no | no | no |
| KHULNASOFT_BEFORE_START_CMD | Comma-separated list of commands to run before Khulnasoft starts. Ansible will run <!-- {% raw %} -->`{{khulnasoft.exec}} {{item}}`<!-- {% endraw %} -->. | no | no | no |
| KHULNASOFT_S2S_PORT | Khulnasoft forwarding/receiving port. Default: `9997` | no | no | no |
| KHULNASOFT_SVC_PORT | Khulnasoft management/administration port. Default: `8089` | no | no | no |
| KHULNASOFT_CERT_PREFIX | HTTP scheme used when making API requests to Khulnasoft management endpoint. Default: `https` | no | no | no |
| KHULNASOFT_ROOT_ENDPOINT | Allow KhulnasoftWeb to be accessed behind a given route (ex. reverse proxy usage) | no | no | no |
| KHULNASOFT_PASSWORD* | Default password of the admin user | yes | yes | yes |
| KHULNASOFT_DECLARATVE_ADMIN_PASSWORD | When `true`, admin password will be fixed to the value defined through Ansible | no | no | no |
| KHULNASOFT_PASS4SYMMKEY | Used to overwrite default `pass4SymmKey` for Khulnasoft secrets | no | no | no |
| KHULNASOFT_HEC_TOKEN | HEC (HTTP Event Collector) token when enabled | no | no | no |
| KHULNASOFT_SHC_SECRET | Search Head Clustering shared secret (deprecated in favor of `KHULNASOFT_SHC_PASS4SYMMKEY`) | no | no | no |
| KHULNASOFT_SHC_PASS4SYMMKEY | Password for the Search Head Clustering shared secret | no | yes | no |
| KHULNASOFT_SHC_LABEL | Search head clustering label | no | yes | no |
| KHULNASOFT_SHC_REPLICATION_FACTOR | Configure search head clustering replication factor | no | no | no |
| KHULNASOFT_PREFERRED_CAPTAINCY | Set up search head clustering with preferred captaincy, typically pinned to the instance designated as `khulnasoft_search_head_captain` | no | no | no |
| KHULNASOFT_IDXC_SECRET | Indexer Clustering shared Secret (deprecated in favor of `KHULNASOFT_SHC_PASS4SYMMKEY`) | no | no | no |
| KHULNASOFT_IDXC_PASS4SYMMKEY | Password for the Indexer Clustering shared Secret | no | no | yes |
| KHULNASOFT_IDXC_DISCOVERYPASS4SYMMKEY | Password for the indexer discovery shared secret | no | no | yes |
| KHULNASOFT_IDXC_LABEL | Indexer clustering label | no | no | yes |
| KHULNASOFT_IDXC_REPLICATION_FACTOR | Configure indexer clustering data replication factor | no | no | no |
| KHULNASOFT_IDXC_SEARCH_FACTOR | Configure indexer clustering search factor | no | no | no |
| KHULNASOFT_OPT | Location where Khulnasoft Enterprise will be installed (not recommended to change). Default: `/opt` | no | no | no |
| KHULNASOFT_HOME | Location of Khulnasoft Enterprise home directory (not recommended to change). Default: `/opt/khulnasoft` | no | no | no |
| KHULNASOFT_EXEC | Location of Khulnasoft Enterprise executable (not recommended to change). Default: `/opt/khulnasoft/bin/khulnasoft` | no | no | no |
| KHULNASOFT_PID | Location of Khulnasoft Enterprise process ID file (not recommended to change). Default: `/opt/khulnasoft/var/run/khulnasoft/khulnasoftd.pid` | no | no | no |
| KHULNASOFT_USER | User which owns the Khulnasoft home directory and runs the khulnasoftd process (not recommended to change). Default: `khulnasoft` | no | no | no |
| KHULNASOFT_GROUP | Group which owns the Khulnasoft home directory and runs the khulnasoftd process (not recommended to change). Default: `khulnasoft` | no | no | no |
| KHULNASOFT_PASS4SYMMKEY | Set user-defined `pass4SymmKey` in the general stanza of server.conf instead of using the Khulnasoft default | no | no | no |
| KHULNASOFT_SECRET | Set user-defined `${KHULNASOFT_HOME}/etc/khulnasoft.secret` instead of using the Khulnasoft default | no | no | no |
| KHULNASOFT_ENABLE_SERVICE | Enable Khulnasoft to start as a system service (`enable boot-start`) | no | no | no |
| KHULNASOFT_SERVICE_NAME | Define Khulnasoft service name when set to start as a system service | no | no | no |
| KHULNASOFT_LAUNCH_CONF | Pass in a comma-separated list of "key=value" pairs that will get written to `${KHULNASOFT_HOME}/etc/khulnasoft-launch.conf` | no | no | no |
| KHULNASOFT_APPS_URL | Pass in a comma-separated list of local paths or remote URLs to Khulnasoft apps that will get installed | no | no | no |
| KHULNASOFTBASE_USERNAME | Khulnasoftbase username used for authentication when installing an app from [Khulnasoftbase](https://khulnasoftbase.khulnasoft.com/) | no | no | no |
| KHULNASOFTBASE_PASSWORD | Khulnasoftbase password used for authentication when installing an app from [Khulnasoftbase](https://khulnasoftbase.khulnasoft.com/) | no | no | no |
| KHULNASOFT_HTTP_PORT | Port to run KhulnasoftWeb on. To disable KhulnasoftWeb, set to `0`. Default: `8000` | no | no | no |
| KHULNASOFT_HTTP_ENABLESSL | Enable HTTPS on KhulnasoftWeb | no | no | no |
| KHULNASOFT_HTTP_ENABLESSL_CERT | Path to SSL certificate used for KhulnasoftWeb, if HTTPS is enabled | no | no | no |
| KHULNASOFT_HTTP_ENABLESSL_PRIVKEY | Path to SSL private key used for KhulnasoftWeb, if HTTPS is enabled | no | no | no |
| KHULNASOFT_HTTP_ENABLESSL_PRIVKEY_PASSWORD | SSL certificate private key password used with KhulnasoftWeb, if HTTPS is enabled | no | no | no |
| KHULNASOFTD_SSL_ENABLE | Enable HTTPS on Khulnasoftd. By default, this is enabled out-of-the-box. To disable, set this to "false" | no | no | no |
| KHULNASOFTD_SSL_CERT | Path to custom SSL certificate used for Khulnasoftd when HTTPS is enabled | no | no | no |
| KHULNASOFTD_SSL_CA | Path to custom CA certificate used for Khulnasoftd when HTTPS is enabled | no | no | no |
| KHULNASOFTD_SSL_PASSWORD | Custom SSL password used with Khulnasoftd when HTTPS is enabled | no | no | no |
| KHULNASOFT_KVSTORE_PORT | Port to run Khulnasoft KVStore. Default: `8191` | no | no | no |
| KHULNASOFT_APPSERVER_PORT | Port to run Khulnasoft appserver. Default: `8065` | no | no | no |
| KHULNASOFT_SET_SEARCH_PEERS | Boolean to configure whether search heads should connect to search peers. Default: `True`. Not recommended to change | no | no | no |
| KHULNASOFT_SITE | For multisite topologies, define the site of this particular Khulnasoft Enterprise instance | no | no | no |
| KHULNASOFT_ALL_SITES | For multisite topologies, define all sites of the topology | no | no | no |
| KHULNASOFT_MULTISITE_MASTER | For multisite topologies, define location of the multisite cluster master | no | no | no |
| KHULNASOFT_MULTISITE_MASTER_PORT | For multisite topologies, define the Khulnasoft management port of the multisite cluster master | no | no | no |
| KHULNASOFT_MULTISITE_REPLICATION_FACTOR_ORIGIN | For multisite topologies, define the origin replication factor | no | no | no |
| KHULNASOFT_MULTISITE_REPLICATION_FACTOR_TOTAL | For multisite topologies, define the total replication factor | no | no | no |
| KHULNASOFT_MULTISITE_SEARCH_FACTOR_ORIGIN | For multisite topologies, define the origin search factor | no | no | no |
| KHULNASOFT_MULTISITE_SEARCH_FACTOR_TOTAL | For multisite topologies, define the total search factor | no | no | no |
| NO_HEALTHCHECK | Disable the Khulnasoft health check script | no | no | yes |
| STEPDOWN_ANSIBLE_USER | Removes Ansible user from the sudo group when set to true. This means that no other users than root will have root access. | no | no | no |
| KHULNASOFT_HOME_OWNERSHIP_ENFORCEMENT | Recursively enforces `${KHULNASOFT_HOME}` to be owned by the user "khulnasoft". Default: `True` | no | no | no |
| KHULNASOFT_DISABLE_POPUPS | Disable pop-ups from login on home page and search app. Default: `False` | no | no | no |
| HIDE_PASSWORD | Hide all Ansible task logs containing Khulnasoft password to secure output to `stdout`. | no | no | no |
| JAVA_VERSION | Supply `"oracle:8"`, `"openjdk:8"`, or `"openjdk:11"` to install a respective Java distribution. | no | no | no |
| JAVA_DOWNLOAD_URL | Provide a custom URL where the Java installation will be fetched| no | no | no |
| KHULNASOFT_TAIL_FILE | Determine which file gets written to the container's stdout (default: `khulnasoftd_stderr.log`) | no | no | no |
| KHULNASOFT_ES_SSL_ENABLEMENT | When running Enterprise Security version >= 6.3.0, define ssl_enablement installation option | no | no | no |
| KHULNASOFT_DSP_ENABLE | Enable DSP forwarding. Default: `false` | no | no | no |
| KHULNASOFT_DSP_SERVER | DSP S2S forwarding endpoint | no | no | no |
| KHULNASOFT_DSP_CERT | DSP certificate used when forwarding | no | no | no |
| KHULNASOFT_DSP_VERIFY | Enable cert verification when forwarding to DSP. Default: `false` | no | no | no |
| KHULNASOFT_DSP_PIPELINE_NAME | Name of DSP pipeline to create/update | no | no | no |
| KHULNASOFT_DSP_PIPELINE_DESC | Description of DSP pipeline to create/update | no | no | no |
| KHULNASOFT_DSP_PIPELINE_SPEC | SPL2 specification of DSP pipeline to create/update | no | no | no |
| KHULNASOFT_ENABLE_DFS | Enable [Data Fabric Search (DFS)](https://docs.khulnasoft.com/Documentation/DFS/latest/DFS/Overview) | no | no | no |
| KHULNASOFT_DFW_NUM_SLOTS | Maximum number of concurrent DFS searches that run on a search head cluster | no | no | no |
| KHULNASOFT_DFC_NUM_SLOTS | Maximum number of concurrent DFS searches that run on each search head | no | no | no |
| KHULNASOFT_DFW_NUM_SLOTS_ENABLED | Enables you to set the value of the field `dfw_num_slots`. | no | no | no |
| SPARK_MASTER_HOST | This setting identifies the Spark master. | no | no | no |
| SPARK_MASTER_WEBUI_PORT | Identifies the port for the Spark master web UI. | no | no | no |
| DMC_FORWARDER_MONITORING | Enables forwarder monitoring on all standalone and search head instances. Default: `False` | no | no | no |
| DMC_ASSET_INTERVAL | Cron schedule that determines how often forwarder assets are re-built. Default: `"3,18,33,48 * * * *"` = every 15 minutes) | no | no | no |
| KHULNASOFT_ENABLE_ASAN | Internally used trigger to handle special provisioning of debug builds of Khulnasoft Enterprise | no | no | no |
| KHULNASOFT_DEFAULTS_URL | URL to a remote `default.yml` file - when fetched, this will get merged into a consolidated mapping of variables | no | no | no |
| KHULNASOFT_DEFAULTS_HTTP_MAX_TIMEOUT | When fetching a remote `default.yml`, specify the timeout of the request | no | no | no |
| KHULNASOFT_DEFAULTS_HTTP_MAX_RETRIES | When fetching a remote `default.yml`, the number of retries to make. For unlimited retries, use `-1` | no | no | no |
| KHULNASOFT_DEFAULTS_HTTP_MAX_DELAY | When fetching a remote `default.yml`, specify the delay between each retry | no | no | no |
| KHULNASOFT_DEFAULTS_HTTP_AUTH_HEADER | When fetching a remote `default.yml`, set the `Authorization` header | no | no | no |
| KHULNASOFT_ANSIBLE_PRE_TASKS | Pass in a comma-separated list of local paths or remote URLs to Ansible playbooks that will be executed before `site.yml`. Must include the protocol, i.e. it must match the regex `^(http\|https\|file)://.*` | no | no | no |
| KHULNASOFT_ANSIBLE_POST_TASKS | Pass in a comma-separated list of local paths or remote URLs to Ansible playbooks that will be executed after `site.yml`. Must include the protocol, i.e. it must match the regex `^(http\|https\|file)://.*` | no | no | no |
| KHULNASOFT_ANSIBLE_ENV | Pass in a comma-separated list of "key=value" pairs that will be mapped to environment variables used during `site.yml` execution. These variables are also available in ansible pre/post playbooks and can be referenced as `hostvars['localhost'].ansible_environment['key']` | no | no | no |
| KHULNASOFT_CONNECTION_TIMEOUT | Configures khulnasoftdConnectionTimeout in `web.conf` with passed integer value (in seconds) | no | no | no |
| KHULNASOFT_ES_SSL_ENABLEMENT | Set the ssl-enablement flag in ES.  Valid values are 'auto', 'strict', and 'ignore'. Defaults to auto when present. | no | no | no |

\* Password must be set either in `default.yml` or as the environment variable `KHULNASOFT_PASSWORD`

#### Additional Khulnasoft Universal Forwarder variables

The `khulnasoft/universalforwarder` image accepts the majority* environment variables as the `khulnasoft/khulnasoft` image above. However, there are some additional ones that are specific to the Universal Forwarder.

\* **Note:** Specifically for the `khulnasoft/universalforwarder` image, the environment variable `KHULNASOFT_ROLE` will by default be set to `khulnasoft_universal_forwarder`. This image cannot accept any other role, and should not be changed (unlike its `khulnasoft/khulnasoft` image counterpart).

| Environment Variable Name | Description | Required for Standalone | Required for Search Head Clustering | Required for Index Clustering |
| --- | --- | --- | --- | --- |
| KHULNASOFT_CMD | Comma-separated list of commands to run after Khulnasoft starts. Ansible will run <!-- {% raw %} -->`{{khulnasoft.exec}} {{item}}`<!-- {% endraw %} -->. | no | no | no |

#### Suggestions for environment variables for Khulnasoft search head cluster

For Khulnasoft search cluster configuration, we suggest passing in the environment variables `KHULNASOFT_HOSTNAME` and `KHULNASOFT_SEARCH_HEAD_URL` with fully qualified domain names.

The dynamic inventory script will assign the value of `KHULNASOFT_HOSTNAME` if defined or `socket.getfqdn()` to the <!-- {% raw %} -->`{{ khulnasoft.hostname }}`<!-- {% endraw %} --> Ansible variable, which will be used to init search head cluster member. `KHULNASOFT_SEARCH_HEAD_URL` will be used as the `--server_list` argument of search cluster captain bootstrap command, and it requires that each member in `--server_list` must be exactly the same as the <!-- {% raw %} -->`{{ khulnasoft.hostname }}`<!-- {% endraw %} --> specified earlier.

To be consistent, we suggest passing in the environment variables `KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL`, `KHULNASOFT_INDEXER_URL` and `KHULNASOFT_DEPLOYER_URL` with fully qualified domain names as well.

## Defaults
For security purposes, we do not ship with a standard `default.yml`. However, it is a required component when running these Ansible playbooks in this codebase. This file can be created manually, but for a quick shortcut you can run:
```
$ docker run -it --rm -e KHULNASOFT_PASSWORD=helloworld khulnasoft/khulnasoft create-defaults > default.yml
```
NOTE: The `default.yml` generated above may require additional, manual modifications.

For distributed Khulnasoft topologies, there are certain configuration settings that are required to be consistent across all members of the deployment. These are settings such as administrator password, clustering labels, keys, etc. To achieve this, it is possible to source all the settings from a single `default.yml` and distribute it universally in the following manners.

#### Loading defaults through file
A static `default.yml` can be dropped on to each instance utilizing the playbooks in this repository. If you're bundling this code in a Docker image or AWS AMI, note that this will be a static configuration, such that Khulnasoft should always spin up in the same way.

This `default.yml` file must be placed at `/tmp/defaults/default.yml`, and it must be readable to the user executing the `ansible-playbook` command. Additionally, it is also possible for certain environment variables to dynamically override settings in this `default.yml` - for more information on those environment variables, please see the [Khulnasoft Docker image](https://github.com/khulnasoft/docker-khulnasoft) project.

In order for the file in `/tmp/defaults/default.yml` to be read and interpreted, it is required that the Ansible command is executed using the dynamic inventory script (`environ.py`) as so:
```
$ ansible-playbook -i inventory/environ.py ...
```

#### Loading defaults through URL
If the `default.yml` file is hosted as a static asset on some webserver, it can be retrieved using an HTTP GET request. The URL must point to a file in a proper YAML format in order for it to be used correctly. Currently, no parameters can be passed through the request. However, redirects are permitted.

To specify a URL to pull a given `default.yml`, a dummy `default.yml` can be baked into each instance ([as instructed above](#loading-defaults-through-file)) to force Ansible to dynamically pull a new one. This placeholder will simply modify the url parameter shown below:
```
config:
  baked: default.yml
  defaults_dir: /tmp/defaults
  env:
    headers: null
    var: https://webserver/path/to/default.yml
    verify: false
  host:
    headers: null
    url: null
    verify: true
  max_delay: 60
  max_retries: 3
  max_timeout: 1200
```
This will try to download the `default.yml` located at `https://webserver/path/to/default.yml` using the given `headers` and `verify` key-word arguments for each request. The download request will timeout after `max_timeout` seconds, but it will retry a maximum of `max_retries` attempts with a delay of `max_delay` in between each attempt.

To use the URL-based loading of a `default.yml`, it is required that the Ansible command is executed using the dynamic inventory script (`environ.py`) as so:
```
$ ansible-playbook -i inventory/environ.py ...
```

#### Schema
For more information on the format and options exposed in a `default.yml`, please see the [full spec](advanced/default.yml.spec.md).

---

## Apps
One of the more versatile features of the Khulnasoft platform is the ability to extend its functionality through the use of apps and add-ons. Apps and add-ons are used heavily by customers by providing out-of-the-box solutions for targeted needs. Many of these products are internally developed and supported by Khulnasoft itself - but an even larger offering is developed by members of the community, partners, and even open-source contributors. Many of these apps can be found on [KhulnasoftBase](https://khulnasoftbase.khulnasoft.com/).

For more information on apps and add-ons, please see [Khulnasoft's featured apps](https://www.khulnasoft.com/en_us/products/apps-and-add-ons.html).

The Ansible playbooks provided in this repository offer the ability to perform fully-vetted app installation. To enable this, modify this section of your `default.yml` to include a list of URLs or files local to the host:
```
khulnasoftbase_username: ...
khulnasoftbase_password: ...
khulnasoft:
  ...
  apps_location:
    - /tmp/app.tgz
    - http://webserver.com/path/to/khulnasoftApp.spl
    - https://khulnasoftbase.khulnasoft.com/app/978/release/1.1/download
  ...
```

Note that in the above, a direct KhulnasoftBase download link was provided. To install an app or add-on directly from KhulnasoftBase, values for `khulnasoftbase_username` and `khulnasoftbase_password` must be specified in order to process licensing agreements and authentication. Additionally, the Ansible provisioning must be done using the dynamic inventory script (`environ.py`) in order to perform the authentication as so:
```
$ ansible-playbook -i inventory/environ.py ...
```

If KhulnasoftBase apps are not specified or needed, the `khulnasoftbase_username` and `khulnasoftbase_password` variables should be omitted entirely.

When deploying distributed Khulnasoft Enterprise environments, apps should be installed on the deployer, cluster master, and deployment server instances. Each of these roles will take care of bundling and pushing the apps to their respective downstream peers. Note that any configuration files in any custom app's `local` directory will *not* be sent to peers - this is in alignment with Khulnasoft best practices around configuration management.

To install an app from elsewhere, provide a path to a compressed `khulnasoftApp.spl` file (either through a filesystem or URL) as seen above. For proper installation, apps should be compressed using `tar` in a GNU/Linux environment, as apps compressed on OSX or other BSD-variant operating systems have been known to cause issues.

For roles that manage clusters, such as Cluster Master and SH Deployer, the apps specified in `apps_location` will be pushed to the cluster and disabled on the local CM or Deployer instance.  For apps that need to be installed locally on these instances, use the `apps_location_local` variable.  Apps specified here will not be pushed to the cluster but installed locally in the same way that apps are installed on a standalone instance.  Both `apps_location` and `apps_location_local` can be used concurrently to allow for different sets of apps to be installed locally vs. pushed to the cluster for CM and Deployer instance.  The syntax is the same as `apps_location`:
```
khulnasoft:
  ...
  apps_location:
    - /tmp/cluster_app.tgz
  apps_location_local:
    - /tmp/local_app.tgz
    - http://webserver.com/path/to/local_auth_app.spl
  ...
```

Khulnasoft Apps and Add-on archive files can also be extracted and installed using the `app_paths_install:` option.  This configuration will install a list of apps directly to the configure `app_paths` directory, bypassing any local install then copy to bundle directory that `apps_location` uses for cluster managing roles such as CM or Deployer.  The suported `app_paths` are default (local apps), shc, idxc, and deployment.  An example of a CM config with one local app and two cluster apps is:
```
khulnasoft:
  ...
  app_paths_install:
    default:
      - /tmp/local_app.tgz
    idxc:
      - /tmp/cluster_app1.tgz
      - /tmp/cluster_app2.spl
  ...
```

The `shc` and `idxc` apps specified in `app_paths_install` are not installed locally so Apps that require a local installation prior to a cluster-wide implementation (such as Enterprise Security Suite) would not be support.  Those apps would still need to use the `apps_location` field for proper installation.

---

## SmartStore
SmartStore utilizes S3-compliant object storage in order to store indexed data. This is a capability only available if you're using an indexer cluster (cluster_master + indexers). For more information, please see the [blog post](https://www.khulnasoft.com/blog/2018/10/11/khulnasoft-smartstore-cut-the-cord-by-decoupling-compute-and-storage.html) as well as [technical overview](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Indexer/AboutSmartStore).

Here's an overview of what this looks like if you want to persist *all* your indexes (default) with a SmartStore backend using the `default.yml`:
```
---
khulnasoft:
  smartstore:
    index:
      - indexName: default
        remoteName: remote_store
        scheme: s3
        remoteLocation: <bucket-name>
        s3:
          access_key: <access_key>
          secret_key: <secret_key>
          endpoint: http://s3-us-west-2.amazonaws.com
```

---

## Custom khulnasoft-launch.conf
`khulnasoft-launch.conf` is a configuration file that exists in `${KHULNASOFT_HOME}/etc/` that has some global environment variables that are using by the `khulnasoftd` process. You can add new variables to this file using either the `default.yml` or via environment variables.

For instance, if you want to add `OPTIMISTIC_ABOUT_FILE_LOCKING=1` to the `khulnasoft-launch.conf`, you can use this `default.yml` as reference:
```
---
khulnasoft:
  launch:
    OPTIMISTIC_ABOUT_FILE_LOCKING: 1
  ...
```

---

## Multi-cluster Search

See the [documentation on how multi-cluster search](advanced/MULTICLUSTERSEARCH.md) can be configured.
