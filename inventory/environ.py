#!/usr/bin/env python
# Copyright 2018-2020 Khulnasoft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function

import os
import platform
import json
import argparse
import re
import random
import string
from time import sleep
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import socket
import requests
import urllib3
import yaml

urllib3.disable_warnings()

HERE = os.path.dirname(os.path.normpath(__file__))
_PLATFORM = platform.platform().lower()
PLATFORM = "windows" if ("windows" in _PLATFORM or "cygwin" in _PLATFORM) else "linux"
HOSTNAME = os.uname()[1]
JAVA_VERSION_WHITELIST = frozenset(("oracle:8", "openjdk:8", "openjdk:9", "openjdk:11"))

roleNames = [
    'khulnasoft_cluster_master', # (if it exists, set up indexer clustering)
    'khulnasoft_deployer',
    'khulnasoft_heavy_forwarder',
    'khulnasoft_standalone',
    'khulnasoft_search_head',
    'khulnasoft_indexer',
    'khulnasoft_license_master', # (if it exists, run adding license with a license master)
    'khulnasoft_search_head_captain', # TODO: remove this as we deprecate this role
    'khulnasoft_universal_forwarder',
    'khulnasoft_deployment_server',
    'khulnasoft_monitor'
]

varPrefix = "KHULNASOFT_VAR_"
reVarPrefix = r"${varPrefix}(.*)"
envPrefix = "KHULNASOFT_ROLE_"
reNamePattern = r"${envPrefix}(.*)"

inventory = {
    "_meta": {
        "hostvars": {}
    },
    "all": {
        "hosts": [],
        "children": ["ungrouped"]
    },
    "ungrouped": {
        "hosts": []
    }
}

def getVars(rePattern):
    """
    Return a mapping of environment keys::values if they match a given regex
    """
    return {re.match(rePattern, k).group(1).lower():os.environ[k] for k in os.environ
            if re.match(rePattern, k)}

def getKhulnasoftInventory(inventory, reName=r"(.*)_URL"):
    """
    Build an inventory of hosts based on a regex that defines host-groupings
    """
    group_information = getVars(reName)
    for group_name in group_information:
        if group_name.lower() in roleNames:
            inventory[group_name] = {}
            hosts = [host.strip() for host in group_information[group_name].split(',')]
            inventory[group_name] = {
                'hosts': list([host.split(':')[0] for host in hosts])
            }
    inventory["all"]["vars"] = getDefaultVars()
    inventory["all"]["vars"]["docker"] = False

    if os.path.isfile("/.dockerenv") or os.path.isfile("/run/.containerenv") or os.path.isdir("/var/run/secrets/kubernetes.io") or os.environ.get("KUBERNETES_SERVICE_HOST"):
        inventory["all"]["vars"]["docker"] = True
        if "localhost" not in inventory["all"]["children"]:
            inventory["all"]["hosts"].append("localhost")
        inventory["_meta"]["hostvars"]["localhost"] = inventory["all"]["vars"]
        inventory["_meta"]["hostvars"]["localhost"]["ansible_connection"] = "local"

def getDefaultVars():
    """
    Load all khulnasoft-ansible defaults and perform overwrites based on
    environment variables to return a consolidated inventory object
    """
    defaultVars = loadDefaults()
    defaultVars["khulnasoft"]["role"] = os.environ.get('KHULNASOFT_ROLE', defaultVars["khulnasoft"].get("role") or "khulnasoft_standalone")
    overrideEnvironmentVars(defaultVars)
    getAnsibleContext(defaultVars)
    getASan(defaultVars)
    getDisablePopups(defaultVars)
    getHEC(defaultVars)
    getSecrets(defaultVars)
    getKhulnasoftPaths(defaultVars)
    getIndexerClustering(defaultVars)
    getSearchHeadClustering(defaultVars)
    # getMultisite() must be called after getIndexerClustering() + getSearchHeadClustering()
    # in order to rectify multisite replication and search factors
    getMultisite(defaultVars)
    getKhulnasoftWebSSL(defaultVars)
    getKhulnasoftdSSL(defaultVars)
    getDistributedTopology(defaultVars)
    getLicenses(defaultVars)
    # Determine DMC settings
    defaultVars["dmc_forwarder_monitoring"] = os.environ.get('DMC_FORWARDER_MONITORING', False)
    defaultVars["dmc_asset_interval"] = os.environ.get('DMC_ASSET_INTERVAL', '3,18,33,48 * * * *')
    # Determine KHULNASOFT_HOME owner
    defaultVars["khulnasoft_home_ownership_enforcement"] = True
    if os.environ.get("KHULNASOFT_HOME_OWNERSHIP_ENFORCEMENT", "").lower() == "false":
        defaultVars["khulnasoft_home_ownership_enforcement"] = False
    # Determine password visibility
    if os.environ.get("HIDE_PASSWORD", "").lower() == "true":
        defaultVars["hide_password"] = True
    # Determine SHC preferred captaincy
    defaultVars["khulnasoft"]["preferred_captaincy"] = True
    if os.environ.get("KHULNASOFT_PREFERRED_CAPTAINCY", "").lower() == "false":
        defaultVars["khulnasoft"]["preferred_captaincy"] = False
    defaultVars["khulnasoft"]["hostname"] = os.environ.get('KHULNASOFT_HOSTNAME', socket.getfqdn())

    getJava(defaultVars)
    getKhulnasoftBuild(defaultVars)
    getKhulnasoftbaseToken(defaultVars)
    getKhulnasoftBuildAuth(defaultVars)
    getKhulnasoftApps(defaultVars)
    getKhulnasoftAppsLocal(defaultVars)
    getLaunchConf(defaultVars)
    getDFS(defaultVars)
    getUFKhulnasoftVariables(defaultVars)
    getESKhulnasoftVariables(defaultVars)
    getDSP(defaultVars)
    return defaultVars

def getKhulnasoftPaths(vars_scope):
    """
    Normalize the paths used by Khulnasoft for downstream plays
    """
    # TODO: Handle changes to KHULNASOFT_HOME that impact other paths (ex khulnasoft.app_paths.*)
    khulnasoft_vars = vars_scope["khulnasoft"]
    khulnasoft_vars["opt"] = os.environ.get("KHULNASOFT_OPT", khulnasoft_vars.get("opt"))
    khulnasoft_vars["home"] = os.environ.get("KHULNASOFT_HOME", khulnasoft_vars.get("home"))
    # Not sure if we should expose this - exec is fixed relative to KHULNASOFT_HOME
    khulnasoft_vars["exec"] = os.environ.get("KHULNASOFT_EXEC", khulnasoft_vars.get("exec"))
    # Not sure if we should expose this - pid is fixed relative to KHULNASOFT_HOME
    khulnasoft_vars["pid"] = os.environ.get("KHULNASOFT_PID", khulnasoft_vars.get("pid"))

def getIndexerClustering(vars_scope):
    """
    Parse and set parameters to configure indexer clustering
    """
    if "idxc" not in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["idxc"] = {}
    idxc_vars = vars_scope["khulnasoft"]["idxc"]
    idxc_vars["label"] = os.environ.get("KHULNASOFT_IDXC_LABEL", idxc_vars.get("label"))
    idxc_vars["secret"] = os.environ.get("KHULNASOFT_IDXC_SECRET", idxc_vars.get("secret"))
    idxc_vars["pass4SymmKey"] = os.environ.get("KHULNASOFT_IDXC_PASS4SYMMKEY", idxc_vars.get("pass4SymmKey")) # Control flow for issue #316 backwards-compatibility
    if idxc_vars["pass4SymmKey"]:
        idxc_vars["secret"] = idxc_vars["pass4SymmKey"]
    else:
        idxc_vars["secret"] = os.environ.get("KHULNASOFT_IDXC_SECRET", idxc_vars.get("secret"))
        idxc_vars["pass4SymmKey"] = idxc_vars["secret"]
    # Support separate pass4SymmKey for indexer discovery
    idxc_vars["discoveryPass4SymmKey"] = os.environ.get("KHULNASOFT_IDXC_DISCOVERYPASS4SYMMKEY", idxc_vars.get("discoveryPass4SymmKey"))
    if not idxc_vars["discoveryPass4SymmKey"]:
        idxc_vars["discoveryPass4SymmKey"] = idxc_vars["pass4SymmKey"]
    # Rectify replication factor (https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Indexer/Thereplicationfactor)
    # Make sure default repl/search factor>0 else Khulnasoft doesn't start unless user-defined
    if inventory.get("khulnasoft_indexer"):
        # If there are indexers, we need to make sure the replication factor is <= number of indexers
        indexer_count = len(inventory["khulnasoft_indexer"].get("hosts", []))
    else:
        # Only occurs during create-defaults generation or topologies without indexers
        indexer_count = idxc_vars.get("replication_factor", 1)
    replf = os.environ.get("KHULNASOFT_IDXC_REPLICATION_FACTOR", idxc_vars.get("replication_factor", 1))
    idxc_vars["replication_factor"] = min(indexer_count, int(replf))
    # Rectify search factor (https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Indexer/Thesearchfactor)
    searchf = os.environ.get("KHULNASOFT_IDXC_SEARCH_FACTOR", idxc_vars.get("search_factor", 1))
    idxc_vars["search_factor"] = min(idxc_vars["replication_factor"], int(searchf))

def getSearchHeadClustering(vars_scope):
    """
    Parse and set parameters to configure search head clustering
    """
    if "shc" not in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["shc"] = {}
    shc_vars = vars_scope["khulnasoft"]["shc"]
    shc_vars["label"] = os.environ.get("KHULNASOFT_SHC_LABEL", shc_vars.get("label"))
    shc_vars["pass4SymmKey"] = os.environ.get("KHULNASOFT_SHC_PASS4SYMMKEY", shc_vars.get("pass4SymmKey")) # Control flow for issue #316 backwards-compatibility
    if shc_vars["pass4SymmKey"]:
        shc_vars["secret"] = shc_vars["pass4SymmKey"]
    else:
        shc_vars["secret"] = os.environ.get("KHULNASOFT_SHC_SECRET", shc_vars.get("secret"))
        shc_vars["pass4SymmKey"] = shc_vars["secret"]
    # Rectify search factor (https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Indexer/Thesearchfactor)
    # Make sure default repl factor>0 else Khulnasoft doesn't start unless user-defined
    if inventory.get("khulnasoft_search_head"):
        # If there are indexers, we need to make sure the replication factor is <= number of search heads
        shcount = len(inventory["khulnasoft_search_head"].get("hosts", []))
    else:
        # Only occurs during create-defaults generation or topologies without search heads
        shcount = shc_vars.get("replication_factor", 1)
    replf = os.environ.get("KHULNASOFT_SHC_REPLICATION_FACTOR", shc_vars.get("replication_factor", 1))
    shc_vars["replication_factor"] = min(shcount, int(replf))

def getMultisite(vars_scope):
    """
    Parse and set parameters to configure multisite
    """
    khulnasoft_vars = vars_scope["khulnasoft"]
    if "KHULNASOFT_SITE" in os.environ or khulnasoft_vars.get("site"):
        khulnasoft_vars["site"] = os.environ.get("KHULNASOFT_SITE", khulnasoft_vars.get("site"))

        all_sites = os.environ.get("KHULNASOFT_ALL_SITES", khulnasoft_vars.get("all_sites"))
        if all_sites:
            khulnasoft_vars["all_sites"] = all_sites

        multisite_master = os.environ.get("KHULNASOFT_MULTISITE_MASTER", khulnasoft_vars.get("multisite_master"))
        if multisite_master:
            khulnasoft_vars["multisite_master"] = multisite_master
    # TODO: Split this into its own khulnasoft.multisite.* section
    khulnasoft_vars["multisite_master_port"] = int(os.environ.get("KHULNASOFT_MULTISITE_MASTER_PORT", khulnasoft_vars.get("multisite_master_port", 8089)))
    khulnasoft_vars["multisite_replication_factor_origin"] = int(os.environ.get("KHULNASOFT_MULTISITE_REPLICATION_FACTOR_ORIGIN", khulnasoft_vars.get("multisite_replication_factor_origin", 1)))
    khulnasoft_vars["multisite_replication_factor_total"] = int(os.environ.get("KHULNASOFT_MULTISITE_REPLICATION_FACTOR_TOTAL", khulnasoft_vars.get("multisite_replication_factor_total", 1)))
    khulnasoft_vars["multisite_replication_factor_total"] = max(khulnasoft_vars["multisite_replication_factor_total"], khulnasoft_vars["idxc"]["replication_factor"])
    khulnasoft_vars["multisite_search_factor_origin"] = int(os.environ.get("KHULNASOFT_MULTISITE_SEARCH_FACTOR_ORIGIN", khulnasoft_vars.get("multisite_search_factor_origin", 1)))
    khulnasoft_vars["multisite_search_factor_total"] = int(os.environ.get("KHULNASOFT_MULTISITE_SEARCH_FACTOR_TOTAL", khulnasoft_vars.get("multisite_search_factor_total", 1)))
    khulnasoft_vars["multisite_search_factor_total"] = max(khulnasoft_vars["multisite_search_factor_total"], khulnasoft_vars["idxc"]["search_factor"])

def getKhulnasoftWebSSL(vars_scope):
    """
    Parse and set parameters to define Khulnasoft Web accessibility
    """
    # TODO: Split this into its own khulnasoft.http.* section
    khulnasoft_vars = vars_scope["khulnasoft"]
    khulnasoft_vars["http_enableSSL"] = os.environ.get('KHULNASOFT_HTTP_ENABLESSL', khulnasoft_vars.get("http_enableSSL"))
    khulnasoft_vars["http_enableSSL_cert"] = os.environ.get('KHULNASOFT_HTTP_ENABLESSL_CERT', khulnasoft_vars.get("http_enableSSL_cert"))
    khulnasoft_vars["http_enableSSL_privKey"] = os.environ.get('KHULNASOFT_HTTP_ENABLESSL_PRIVKEY', khulnasoft_vars.get("http_enableSSL_privKey"))
    khulnasoft_vars["http_enableSSL_privKey_password"] = os.environ.get('KHULNASOFT_HTTP_ENABLESSL_PRIVKEY_PASSWORD', khulnasoft_vars.get("http_enableSSL_privKey_password"))
    khulnasoft_vars["http_port"] = int(os.environ.get('KHULNASOFT_HTTP_PORT', khulnasoft_vars.get("http_port")))

def getKhulnasoftdSSL(vars_scope):
    """
    Parse and set parameters to define Khulnasoftd
    """
    if "ssl" not in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["ssl"] = {}
    ssl_vars = vars_scope["khulnasoft"]["ssl"]
    ssl_vars["cert"] = os.environ.get("KHULNASOFTD_SSL_CERT", ssl_vars.get("cert"))
    ssl_vars["ca"] = os.environ.get("KHULNASOFTD_SSL_CA", ssl_vars.get("ca"))
    ssl_vars["password"] = os.environ.get("KHULNASOFTD_SSL_PASSWORD", ssl_vars.get("password"))
    ssl_vars["enable"] = ssl_vars.get("enable", True)
    enable = os.environ.get("KHULNASOFTD_SSL_ENABLE", "")
    if enable.lower() == "false":
        ssl_vars["enable"] = False
        vars_scope["cert_prefix"] = "http"
    

def getDistributedTopology(vars_scope):
    """
    Parse and set parameters to define topology if this is a distributed environment
    """
    license_master_url = os.environ.get("KHULNASOFT_LICENSE_MASTER_URL", vars_scope["khulnasoft"].get("license_master_url", ""))
    vars_scope["khulnasoft"]["license_master_url"] = parseUrl(license_master_url, vars_scope)
    vars_scope["khulnasoft"]["deployer_url"] = os.environ.get("KHULNASOFT_DEPLOYER_URL", vars_scope["khulnasoft"].get("deployer_url", ""))
    vars_scope["khulnasoft"]["cluster_master_url"] = os.environ.get("KHULNASOFT_CLUSTER_MASTER_URL", vars_scope["khulnasoft"].get("cluster_master_url", ""))
    vars_scope["khulnasoft"]["search_head_captain_url"] = os.environ.get("KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL", vars_scope["khulnasoft"].get("search_head_captain_url", ""))
    if not vars_scope["khulnasoft"]["search_head_captain_url"] and "search_head_cluster_url" in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["search_head_captain_url"] = vars_scope["khulnasoft"]["search_head_cluster_url"]

def getLicenses(vars_scope):
    """
    Determine the location of Khulnasoft licenses to install at start-up time
    """
    # Need to provide some file value (does not have to exist). The task will automatically skip over if the file is not found. Otherwise, will throw an error if no file is specified.
    vars_scope["khulnasoft"]["license_uri"] = os.environ.get("KHULNASOFT_LICENSE_URI", vars_scope["khulnasoft"].get("license_uri") or "khulnasoft.lic")
    vars_scope["khulnasoft"]["wildcard_license"] = False
    if vars_scope["khulnasoft"]["license_uri"] and '*' in vars_scope["khulnasoft"]["license_uri"]:
        vars_scope["khulnasoft"]["wildcard_license"] = True
    vars_scope["khulnasoft"]["ignore_license"] = False
    if os.environ.get("KHULNASOFT_IGNORE_LICENSE", "").lower() == "true":
        vars_scope["khulnasoft"]["ignore_license"] = True
    vars_scope["khulnasoft"]["license_download_dest"] = os.environ.get("KHULNASOFT_LICENSE_INSTALL_PATH", vars_scope["khulnasoft"].get("license_download_dest") or "/tmp/khulnasoft.lic")

def getJava(vars_scope):
    """
    Parse and set Java installation parameters
    """
    vars_scope["java_version"] = vars_scope.get("java_version")
    vars_scope["java_download_url"] = vars_scope.get("java_download_url")
    vars_scope["java_update_version"] = vars_scope.get("java_update_version")
    java_version = os.environ.get("JAVA_VERSION")
    if not java_version:
        return
    java_version = java_version.lower()
    if java_version not in JAVA_VERSION_WHITELIST:
        raise Exception("Invalid Java version supplied, supported versions are: {}".format(JAVA_VERSION_WHITELIST))
    vars_scope["java_version"] = java_version
    # TODO: We can probably DRY this up
    if java_version == "oracle:8":
        vars_scope["java_download_url"] = os.environ.get("JAVA_DOWNLOAD_URL", "https://download.oracle.com/otn-pub/java/jdk/8u141-b15/336fa29ff2bb4ef291e347e091f7f4a7/jdk-8u141-linux-x64.tar.gz")
        try:
            vars_scope["java_update_version"] = re.search(r"jdk-8u(\d+)-linux-x64.tar.gz", vars_scope["java_download_url"]).group(1)
        except:
            raise Exception("Invalid Java download URL format")
    elif java_version == "openjdk:11":
        vars_scope["java_download_url"] = os.environ.get("JAVA_DOWNLOAD_URL", "https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_linux-x64_bin.tar.gz")
        try:
            vars_scope["java_update_version"] = re.search(r"openjdk-(\d+\.\d+\.\d+)_linux-x64_bin.tar.gz", vars_scope["java_download_url"]).group(1)
        except:
            raise Exception("Invalid Java download URL format")

def getKhulnasoftBuild(vars_scope):
    """
    Determine the location of the Khulnasoft build
    """
    vars_scope["khulnasoft"]["build_url_bearer_token"] = os.environ.get("KHULNASOFT_BUILD_URL_BEARER_TOKEN", vars_scope["khulnasoft"].get("build_url_bearer_token"))
    vars_scope["khulnasoft"]["build_location"] = os.environ.get("KHULNASOFT_BUILD_URL", vars_scope["khulnasoft"].get("build_location"))

def getKhulnasoftbaseToken(vars_scope):
    """
    Authenticate to KhulnasoftBase and modify the variable scope in-place to utilize temporary session token
    """
    vars_scope["khulnasoftbase_token"] = None
    vars_scope["khulnasoftbase_username"] = os.environ.get("KHULNASOFTBASE_USERNAME", vars_scope.get("khulnasoftbase_username"))
    vars_scope["khulnasoftbase_password"] = os.environ.get("KHULNASOFTBASE_PASSWORD", vars_scope.get("khulnasoftbase_password"))
    if vars_scope["khulnasoftbase_username"] and vars_scope["khulnasoftbase_password"]:
        resp = requests.post("https://khulnasoftbase.khulnasoft.com/api/account:login/",
                             data={"username": vars_scope["khulnasoftbase_username"], "password": vars_scope["khulnasoftbase_password"]})
        if resp.status_code != 200:
            raise Exception("Invalid Khulnasoftbase credentials - will not download apps from Khulnasoftbase")
        output = resp.content
        if isinstance(output, bytes):
            output = output.decode("utf-8", "ignore")
        khulnasoftbase_token = re.search("<id>(.*)</id>", output, re.IGNORECASE)
        vars_scope["khulnasoftbase_token"] = khulnasoftbase_token.group(1) if khulnasoftbase_token else None

def getKhulnasoftBuildAuth(vars_scope):
    """
    Load username and password to be used in basic auth when fetching khulnasoft build or apps
    """
    vars_scope["khulnasoft"]["artifact_auth_user"] = os.environ.get("ARTIFACTORY_USER", vars_scope["khulnasoft"].get("artifact_auth_user"))
    vars_scope["khulnasoft"]["artifact_auth_pass"] = os.environ.get("ARTIFACTORY_TOKEN", vars_scope["khulnasoft"].get("artifact_auth_pass"))

def getKhulnasoftApps(vars_scope):
    """
    Determine the set of Khulnasoft apps to install as union of defaults.yml and environment variables
    """
    appList = []
    if not "apps_location" in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["apps_location"] = []
    # From default.yml
    elif type(vars_scope["khulnasoft"]["apps_location"]) == str:
        appList = vars_scope["khulnasoft"]["apps_location"].split(",")
    elif type(vars_scope["khulnasoft"]["apps_location"]) == list:
        appList = vars_scope["khulnasoft"]["apps_location"]
    # From environment variables
    apps = os.environ.get("KHULNASOFT_APPS_URL")
    if apps:
        apps = apps.split(",")
        for app in apps:
            if app not in appList:
                appList.append(app)
    vars_scope["khulnasoft"]["apps_location"] = appList

def getKhulnasoftAppsLocal(vars_scope):
    """
    Determine the set of Khulnasoft apps to install locally only as union of defaults.yml and environment variables
    """
    # Check if theres a local apps list for CM/Deployer roles
    appListLocal = []
    if not "apps_location_local" in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["apps_location_local"] = []
    # From default.yml
    elif type(vars_scope["khulnasoft"]["apps_location_local"]) == str:
        appListLocal = vars_scope["khulnasoft"]["apps_location_local"].split(",")
    elif type(vars_scope["khulnasoft"]["apps_location_local"]) == list:
        appListLocal = vars_scope["khulnasoft"]["apps_location_local"]
    # From environment variables
    apps = os.environ.get("KHULNASOFT_APPS_URL_LOCAL")
    if apps:
        apps = apps.split(",")
        for app in apps:
            if app not in appListLocal:
                appListLocal.append(app)
    vars_scope["khulnasoft"]["apps_location_local"] = appListLocal

def getKhulnasoftAppPathInstall(vars_scope):
    """
    Determine the set of Khulnasoft apps to install at which location as a
    union of defaults.yml.  The actual path to install to is determined by
    the khulnasoft.app_paths.* variable
    """
    appPaths = ["shc", "idxc", "default", "deployment"]
    if not "app_paths_install" in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["app_paths_install"] = {}
        for path in appPaths:
            vars_scope["khulnasoft"]["app_paths_install"][path] = []
    else:
        for path in appPaths:
            appList = []
            if path in vars_scope["khulnasoft"]["app_paths_install"]:
                # From default.yml
                if type(vars_scope["khulnasoft"]["app_paths_install"][path]) == str:
                    appList = vars_scope["khulnasoft"]["app_paths_install"][path].split(",")
                elif type(vars_scope["khulnasoft"]["app_paths_install"][path]) == list:
                    appList = vars_scope["khulnasoft"]["app_paths_install"][path]

            vars_scope["khulnasoft"]["app_paths_install"][path] = appList

def getSecrets(vars_scope):
    """
    Parse sensitive passphrases
    """
    vars_scope["khulnasoft"]["password"] = os.environ.get("KHULNASOFT_PASSWORD", vars_scope["khulnasoft"].get("password"))
    if not vars_scope["khulnasoft"]["password"]:
        raise Exception("Khulnasoft password must be supplied!")
    if os.path.isfile(vars_scope["khulnasoft"]["password"]):
        with open(vars_scope["khulnasoft"]["password"], "r") as f:
            vars_scope["khulnasoft"]["password"] = f.read().strip()
            if not vars_scope["khulnasoft"]["password"]:
                raise Exception("Khulnasoft password supplied is empty/null")
    dpw = os.environ.get("KHULNASOFT_DECLARATIVE_ADMIN_PASSWORD", "")
    if dpw.lower() == "true":
        vars_scope["khulnasoft"]["declarative_admin_password"] = True
    else:
        vars_scope["khulnasoft"]["declarative_admin_password"] = bool(vars_scope["khulnasoft"].get("declarative_admin_password"))
    vars_scope["khulnasoft"]["pass4SymmKey"] = os.environ.get('KHULNASOFT_PASS4SYMMKEY', vars_scope["khulnasoft"].get("pass4SymmKey"))
    vars_scope["khulnasoft"]["secret"] = os.environ.get('KHULNASOFT_SECRET', vars_scope["khulnasoft"].get("secret"))

def getLaunchConf(vars_scope):
    """
    Parse key/value pairs to set in khulnasoft-launch.conf
    """
    launch = {}
    if not "launch" in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["launch"] = {}
    # From default.yml
    if type(vars_scope["khulnasoft"]["launch"]) == dict:
        launch.update(vars_scope["khulnasoft"]["launch"])
    # From environment variables
    settings = os.environ.get("KHULNASOFT_LAUNCH_CONF")
    if settings:
        launch.update({k:v for k,v in [x.split("=", 1) for x in settings.split(",")]})
    vars_scope["khulnasoft"]["launch"] = launch

def ensureListValue(value, separator):
    if isinstance(value, list):
        return value
    elif (not value) or (not value.strip()):
        return []
    else:
        return splitAndStrip(value, separator)

def splitAndStrip(value, separator):
    if not value:
        return []
    return [x.strip() for x in value.split(separator)]

def transformEnvironmentVariable(environmentVariableName, transform, default):
    if environmentVariableName in os.environ:
        return transform(os.environ.get(environmentVariableName))
    else:
        return default

def getAnsibleContext(vars_scope):
    """
    Parse parameters that influence Ansible execution
    """
    stringSeparator = ","
    vars_scope["ansible_pre_tasks"] = transformEnvironmentVariable("KHULNASOFT_ANSIBLE_PRE_TASKS", lambda v: splitAndStrip(v, stringSeparator), ensureListValue(vars_scope.get("ansible_pre_tasks"), stringSeparator))
    vars_scope["ansible_post_tasks"] = transformEnvironmentVariable("KHULNASOFT_ANSIBLE_POST_TASKS", lambda v: splitAndStrip(v, stringSeparator), ensureListValue(vars_scope.get("ansible_post_tasks"), stringSeparator))
    vars_scope["ansible_environment"] = vars_scope.get("ansible_environment") or {}
    env = os.environ.get("KHULNASOFT_ANSIBLE_ENV")
    if env:
        vars_scope["ansible_environment"].update({k:v for k,v in [x.split("=", 1) for x in env.split(",")]})

def getASan(vars_scope):
    """
    Enable ASan debug builds
    """
    vars_scope["khulnasoft"]["asan"] = bool(os.environ.get("KHULNASOFT_ENABLE_ASAN", vars_scope["khulnasoft"].get("asan")))
    if vars_scope["khulnasoft"]["asan"]:
        vars_scope["ansible_environment"].update({"ASAN_OPTIONS": "detect_leaks=0"})

def getDisablePopups(vars_scope):
    """
    Configure pop-up settings
    """
    vars_scope["khulnasoft"]["disable_popups"] = bool(vars_scope["khulnasoft"].get("disable_popups"))
    popups_disabled = os.environ.get("KHULNASOFT_DISABLE_POPUPS", "")
    if popups_disabled.lower() == "true":
        vars_scope["khulnasoft"]["disable_popups"] = True
    elif popups_disabled.lower() == "false":
        vars_scope["khulnasoft"]["disable_popups"] = False

def getHEC(vars_scope):
    """
    Configure HEC settings
    """
    if not "hec" in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["hec"] = {}
    vars_scope["khulnasoft"]["hec"]["token"] = os.environ.get("KHULNASOFT_HEC_TOKEN", vars_scope["khulnasoft"]["hec"].get("token"))
    vars_scope["khulnasoft"]["hec"]["port"] = int(os.environ.get("KHULNASOFT_HEC_PORT", vars_scope["khulnasoft"]["hec"].get("port")))
    ssl = os.environ.get("KHULNASOFT_HEC_SSL", "")
    if ssl.lower() == "false":
        vars_scope["khulnasoft"]["hec"]["ssl"] = False
    else:
        vars_scope["khulnasoft"]["hec"]["ssl"] = bool(vars_scope["khulnasoft"]["hec"].get("ssl"))

def getDSP(vars_scope):
    """
    Configure DSP settings
    """
    if not "dsp" in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["dsp"] = {}
    vars_scope["khulnasoft"]["dsp"]["server"] = os.environ.get("KHULNASOFT_DSP_SERVER", vars_scope["khulnasoft"]["dsp"].get("server"))
    vars_scope["khulnasoft"]["dsp"]["cert"] = os.environ.get("KHULNASOFT_DSP_CERT", vars_scope["khulnasoft"]["dsp"].get("cert"))
    vars_scope["khulnasoft"]["dsp"]["verify"] = bool(vars_scope["khulnasoft"]["dsp"].get("verify"))
    verify = os.environ.get("KHULNASOFT_DSP_VERIFY", "")
    if verify.lower() == "true":
        vars_scope["khulnasoft"]["dsp"]["verify"] = True
    vars_scope["khulnasoft"]["dsp"]["enable"] = bool(vars_scope["khulnasoft"]["dsp"].get("enable"))
    enable = os.environ.get("KHULNASOFT_DSP_ENABLE", "")
    if enable.lower() == "true":
        vars_scope["khulnasoft"]["dsp"]["enable"] = True
    vars_scope["khulnasoft"]["dsp"]["pipeline_name"] = os.environ.get("KHULNASOFT_DSP_PIPELINE_NAME", vars_scope["khulnasoft"]["dsp"].get("pipeline_name"))
    vars_scope["khulnasoft"]["dsp"]["pipeline_desc"] = os.environ.get("KHULNASOFT_DSP_PIPELINE_DESC", vars_scope["khulnasoft"]["dsp"].get("pipeline_desc"))
    vars_scope["khulnasoft"]["dsp"]["pipeline_spec"] = os.environ.get("KHULNASOFT_DSP_PIPELINE_SPEC", vars_scope["khulnasoft"]["dsp"].get("pipeline_spec"))

def getESKhulnasoftVariables(vars_scope):
    """
    Get any special Enterprise Security configuration variables
    """
    ssl_enablement_env = os.environ.get("KHULNASOFT_ES_SSL_ENABLEMENT")
    if not ssl_enablement_env and (not "es" in vars_scope["khulnasoft"] or not "ssl_enablement" in vars_scope["khulnasoft"]["es"]):
        # This feature is only for specific versions of ES.
        # if it is missing, don't pass any value in.
        vars_scope["es_ssl_enablement"] = ""
    else:
        # Use the environment variable unless the ssl enablement value is present
        ssl_enablement = ssl_enablement_env or vars_scope["khulnasoft"]["es"]["ssl_enablement"]
        # Build the flag in it's entirety here
        if ssl_enablement not in ["auto", "strict", "ignore"]:
            raise Exception("Invalid ssl_enablement flag {0}".format(ssl_enablement))
        vars_scope["es_ssl_enablement"] = "--ssl_enablement {0}".format(ssl_enablement)

def overrideEnvironmentVars(vars_scope):
    vars_scope["khulnasoft"]["user"] = os.environ.get("KHULNASOFT_USER", vars_scope["khulnasoft"]["user"])
    vars_scope["khulnasoft"]["group"] = os.environ.get("KHULNASOFT_GROUP", vars_scope["khulnasoft"]["group"])
    vars_scope["cert_prefix"] = os.environ.get("KHULNASOFT_CERT_PREFIX", vars_scope.get("cert_prefix", "https"))
    vars_scope["khulnasoft"]["root_endpoint"] = os.environ.get('KHULNASOFT_ROOT_ENDPOINT', vars_scope["khulnasoft"]["root_endpoint"])
    vars_scope["khulnasoft"]["svc_port"] = os.environ.get('KHULNASOFT_SVC_PORT', vars_scope["khulnasoft"]["svc_port"])
    vars_scope["khulnasoft"]["khulnasoft_http_enabled"] = os.environ.get('ENABLE_TCP_MODE', vars_scope["khulnasoft"]["enable_tcp_mode"])
    vars_scope["khulnasoft"]["s2s"]["port"] = int(os.environ.get('KHULNASOFT_S2S_PORT', vars_scope["khulnasoft"]["s2s"]["port"]))
    vars_scope["khulnasoft"]["enable_service"] = os.environ.get('KHULNASOFT_ENABLE_SERVICE', vars_scope["khulnasoft"]["enable_service"])
    vars_scope["khulnasoft"]["service_name"] = os.environ.get('KHULNASOFT_SERVICE_NAME', vars_scope["khulnasoft"]["service_name"])
    vars_scope["khulnasoft"]["allow_upgrade"] = os.environ.get('KHULNASOFT_ALLOW_UPGRADE', vars_scope["khulnasoft"]["allow_upgrade"])
    vars_scope["khulnasoft"]["appserver"]["port"] = os.environ.get('KHULNASOFT_APPSERVER_PORT', vars_scope["khulnasoft"]["appserver"]["port"])
    vars_scope["khulnasoft"]["kvstore"]["port"] = os.environ.get('KHULNASOFT_KVSTORE_PORT', vars_scope["khulnasoft"]["kvstore"]["port"])
    vars_scope["khulnasoft"]["connection_timeout"] = int(os.environ.get('KHULNASOFT_CONNECTION_TIMEOUT', vars_scope["khulnasoft"]["connection_timeout"]))

    if vars_scope["khulnasoft"]["khulnasoft_http_enabled"] == "false" and "forwarder" not in vars_scope["khulnasoft"]["role"].lower():
        vars_scope["khulnasoft"]["khulnasoft_http_enabled"] = "true"
    # Set set_search_peers to False to disable peering to indexers when creating multisite topology
    if os.environ.get("KHULNASOFT_SET_SEARCH_PEERS", "").lower() == "false":
        vars_scope["khulnasoft"]["set_search_peers"] = False

def getDFS(vars_scope):
    """
    Parse and set parameters to configure Data Fabric Search
    """
    if "dfs" not in vars_scope["khulnasoft"]:
        vars_scope["khulnasoft"]["dfs"] = {}
    dfs_vars = vars_scope["khulnasoft"]["dfs"]
    dfs_vars["enable"] = bool(os.environ.get("KHULNASOFT_ENABLE_DFS", dfs_vars.get("enable")))
    dfs_vars["dfw_num_slots"] = int(os.environ.get("KHULNASOFT_DFW_NUM_SLOTS", dfs_vars.get("dfw_num_slots", 10)))
    dfs_vars["dfc_num_slots"] = int(os.environ.get("KHULNASOFT_DFC_NUM_SLOTS", dfs_vars.get("dfc_num_slots", 4)))
    dfs_vars["dfw_num_slots_enabled"] = bool(os.environ.get('KHULNASOFT_DFW_NUM_SLOTS_ENABLED', dfs_vars.get("dfw_num_slots_enabled")))
    dfs_vars["spark_master_host"] = os.environ.get("SPARK_MASTER_HOST", dfs_vars.get("spark_master_host", "127.0.0.1"))
    dfs_vars["spark_master_webui_port"] = int(os.environ.get("SPARK_MASTER_WEBUI_PORT", dfs_vars.get("spark_master_webui_port", 8080)))

def getUFKhulnasoftVariables(vars_scope):
    """
    Set or override specific environment variables for universal forwarders
    """
    if os.environ.get("KHULNASOFT_DEPLOYMENT_SERVER"):
        vars_scope["khulnasoft"]["deployment_server"] = os.environ.get("KHULNASOFT_DEPLOYMENT_SERVER")
    if os.environ.get("KHULNASOFT_ADD"):
        vars_scope["khulnasoft"]["add"] = os.environ.get("KHULNASOFT_ADD").split(",")
    if os.environ.get("KHULNASOFT_BEFORE_START_CMD"):
        vars_scope["khulnasoft"]["before_start_cmd"] = os.environ.get("KHULNASOFT_BEFORE_START_CMD").split(",")
    if os.environ.get("KHULNASOFT_CMD"):
        vars_scope["khulnasoft"]["cmd"] = os.environ.get("KHULNASOFT_CMD").split(",")
    if os.environ.get("KHULNASOFT_DEPLOYMENT_CLIENT_NAME"):
        vars_scope["khulnasoft"]["deployment_client"] = {
            "name": os.environ.get("KHULNASOFT_DEPLOYMENT_CLIENT_NAME")
        }

def getRandomString():
    """
    Generate a random string consisting of characters + digits
    """
    char_set = string.ascii_uppercase + string.digits
    return ''.join(random.sample(char_set * 6, 6))

def parseUrl(url, vars_scope):
    """
    Parses role URL to handle non-default schemes, ports, etc. 
    """
    if not url:
        return ""
    scheme = vars_scope.get("cert_prefix", "https")
    port = vars_scope["khulnasoft"].get("svc_port", 8089)
    parsed = urlparse(url)
    # If netloc exists, we should consider the url provided well-formatted w/ scheme provided
    if parsed.netloc:
        # Strip auth info, if it exists
        netloc = parsed.netloc.split("@", 1)[-1]
        if ":" not in netloc:
            return "{}://{}:{}".format(parsed.scheme, netloc, port)
        return "{}://{}".format(parsed.scheme, netloc)
    # Strip auth info, if it exists
    parsed = url.split("@", 1)[-1]
    # Strip path, if it exists
    parsed = parsed.split("/", 1)[0]
    # Extract hostname and port
    parsed = parsed.split(":", 1)
    hostname = parsed[0]
    if len(parsed) == 2:
        port = parsed[1]
    return "{}://{}:{}".format(scheme, hostname, port)

def merge_dict(dict1, dict2, path=None):
    """
    Merge two dictionaries such that all the keys in dict2 overwrite those in dict1
    """
    if path is None: path = []
    for key in dict2:
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                merge_dict(dict1[key], dict2[key], path + [str(key)])
            elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                dict1[key] += dict2[key]
            else:
                dict1[key] = dict2[key]
        else:
            dict1[key] = dict2[key]
    return dict1

def mergeDefaults(vars_scope, key, src):
    """
    Helper method to fetch defaults from various sources/other methods
    """
    if not src or not src.strip():
        return vars_scope
    src = src.strip().lower()
    if src.startswith("file://"):
        src = src[7:]
    if src.startswith(("http://", "https://")):
        headers = None
        verify = False
        if vars_scope.get("config") and vars_scope["config"].get(key):
            headers = vars_scope["config"][key].get("headers")
            verify = bool(vars_scope["config"][key].get("verify"))
        vars_scope = mergeDefaultsFromURL(vars_scope, src, headers, verify)
    else:
        vars_scope = mergeDefaultsFromFile(vars_scope, src)
    return vars_scope

def mergeDefaultsFromURL(vars_scope, url, headers=None, verify=False):
    """
    Fetch defaults from a URL and merge them into a single dict
    """
    if not url:
        return vars_scope
    if not headers:
        headers = {}
    max_retries = int(os.environ.get("KHULNASOFT_DEFAULTS_HTTP_MAX_RETRIES", vars_scope["config"].get("max_retries")))
    max_delay = int(os.environ.get("KHULNASOFT_DEFAULTS_HTTP_MAX_DELAY", vars_scope["config"].get("max_delay")))
    max_timeout = int(os.environ.get("KHULNASOFT_DEFAULTS_HTTP_MAX_TIMEOUT", vars_scope["config"].get("max_timeout")))
    auth = os.environ.get("KHULNASOFT_DEFAULTS_HTTP_AUTH_HEADER")
    if auth:
        headers["Authorization"] = auth
    unlimited_retries = (max_retries == -1)
    current_retry = 0
    while True:
        try:
            resp = requests.get(url.format(hostname=HOSTNAME, platform=PLATFORM),
                                headers=headers, timeout=max_timeout, verify=verify)
            resp.raise_for_status()
            output = resp.content
            if isinstance(output, bytes):
                output = output.decode("utf-8", "ignore")
            vars_scope = merge_dict(vars_scope, yaml.load(output, Loader=yaml.Loader))
            break
        except Exception as err:
            if unlimited_retries or current_retry < max_retries:
                current_retry += 1
                print('URL request #{0} failed, sleeping {1} seconds and retrying'.format(current_retry, max_delay))
                sleep(max_delay)
                continue
            raise err
    return vars_scope

def mergeDefaultsFromFile(vars_scope, file):
    """
    Fetch defaults from a file and merge them into a single dict
    """
    if not file:
        return vars_scope
    if os.path.exists(file):
        with open(file, "r") as f:
            vars_scope = merge_dict(vars_scope, yaml.load(f.read(), Loader=yaml.Loader))
    return vars_scope

def loadDefaults():
    """
    Generate a consolidated map containing variables used to drive Ansible functionality.
    Defaults are loaded in a particular order such that latter overrides former.
    """
    # Load base defaults from khulnasoft-ansible repository
    base = loadBaseDefaults()
    if not base.get("config"):
        return base
    # Add "baked" files to array
    for yml in loadBakedDefaults(base.get("config")):
        base = mergeDefaults(base, yml["key"], yml["src"])
    # Add "env" files to array
    for yml in loadEnvDefaults(base.get("config")):
        base = mergeDefaults(base, yml["key"], yml["src"])
    # Add "host" files to array
    for yml in loadHostDefaults(base.get("config")):
        base = mergeDefaults(base, yml["key"], yml["src"])
    return base

def loadBaseDefaults():
    """
    Load the base defaults shipped in khulnasoft-ansible
    """
    yml = {}
    filename = "khulnasoft_defaults_{}.yml".format(PLATFORM)
    if os.environ.get("KHULNASOFT_ROLE") == "khulnasoft_universal_forwarder":
        filename = "khulnasoftforwarder_defaults_{}.yml".format(PLATFORM)
    with open(os.path.join(HERE, filename), "r") as yaml_file:
        yml = yaml.load(yaml_file, Loader=yaml.Loader)
    return yml

def loadBakedDefaults(config):
    """
    Load the defaults in "baked" key of the configuration.
    """
    if not config or not config.get("baked"):
        return []
    files = config["baked"].split(",")
    default_dir = config.get("defaults_dir", "")
    return [{"key": "baked", "src": os.path.join(default_dir, f.strip())} for f in files]

def loadEnvDefaults(config):
    """
    Load the defaults in "env" key of the configuration.
    """
    if not config or not config.get("env") or not config["env"].get("var"):
        return []
    urls = os.environ.get(config["env"]["var"], "")
    if not urls:
        return []
    return [{"key": "env", "src": url} for url in urls.split(",")]

def loadHostDefaults(config):
    """
    Load the defaults in "host" key of the configuration.
    """
    if not config or not config.get("host") or not config["host"].get("url"):
        return []
    urls = config["host"]["url"].split(",")
    return [{"key": "host", "src": url} for url in urls]

def obfuscate_vars(inventory):
    """
    Remove sensitive variables when dumping inventory out to stdout or file
    """
    stars = "*"*14
    khulnasoftVars = inventory.get("all", {}).get("vars", {}).get("khulnasoft", {})
    if khulnasoftVars.get("password"):
        khulnasoftVars["password"] = stars
    if khulnasoftVars.get("pass4SymmKey"):
        khulnasoftVars["pass4SymmKey"] = stars
    if khulnasoftVars.get("shc") and khulnasoftVars["shc"].get("secret"):
        khulnasoftVars["shc"]["secret"] = stars
    if khulnasoftVars.get("shc") and khulnasoftVars["shc"].get("pass4SymmKey"):
        khulnasoftVars["shc"]["pass4SymmKey"] = stars
    if khulnasoftVars.get("idxc") and khulnasoftVars["idxc"].get("secret"):
        khulnasoftVars["idxc"]["secret"] = stars
    if khulnasoftVars.get("idxc") and khulnasoftVars["idxc"].get("pass4SymmKey"):
        khulnasoftVars["idxc"]["pass4SymmKey"] = stars
    if khulnasoftVars.get("smartstore") and khulnasoftVars["smartstore"].get("index"):
        khulnasoftIndexes = khulnasoftVars["smartstore"]["index"]
        for idx in range(0, len(khulnasoftIndexes)):
            if khulnasoftIndexes[idx].get("s3"):
                if khulnasoftIndexes[idx]["s3"].get("access_key"):
                    khulnasoftIndexes[idx]["s3"]["access_key"] = stars
                if khulnasoftIndexes[idx]["s3"].get("secret_key"):
                    khulnasoftIndexes[idx]["s3"]["secret_key"] = stars
    return inventory

def create_parser():
    """
    Create an argparser to control dynamic inventory execution
    """
    parser = argparse.ArgumentParser(description='Return Ansible inventory defined in the environment.')
    parser.add_argument('--list', action='store_true', default=True, help='List all hosts (default: True)')
    parser.add_argument('--host', action='store', help='Only get information for a specific host.')
    parser.add_argument('--write-to-file', action='store_true', default=False, help='Write to file for debugging')
    parser.add_argument('--write-to-stdout', action='store_true', default=False, help='create a default.yml file shown on stdout from current vars')
    return parser

def prep_for_yaml_out(inventory):
    """
    Prune the inventory by removing select keys before printing/writing to file
    """
    inventory_to_dump = inventory["all"]["vars"]

    keys_to_del = ["ansible_ssh_user",
                   "apps_location",
                   "build_location",
                   "hostname",
                   "role",
                   "preferred_captaincy",
                   "license_uri"]
    for key in keys_to_del:
        if key in inventory_to_dump:
            del inventory_to_dump[key]
        if key in inventory_to_dump["khulnasoft"]:
            del inventory_to_dump["khulnasoft"][key]
        if key in inventory_to_dump["khulnasoft"]["app_paths"]:
            del inventory_to_dump["khulnasoft"]["app_paths"][key]
        if key in inventory_to_dump["khulnasoft"]["shc"]:
            del inventory_to_dump["khulnasoft"]["shc"][key]
        if key in inventory_to_dump["khulnasoft"]["idxc"]:
            del inventory_to_dump["khulnasoft"]["idxc"][key]
    #remove extra stuff when we know it's the forwarder
    if inventory_to_dump["khulnasoft"]["home"] == "/opt/khulnasoftforwarder":
        del inventory_to_dump["khulnasoft"]["idxc"]
        del inventory_to_dump["khulnasoft"]["shc"]
    return inventory_to_dump

def main():
    """
    Primary entrypoint to dynamic inventory script
    """
    parser = create_parser()
    args = parser.parse_args()

    getKhulnasoftInventory(inventory)
    if args.write_to_file:
        with open(os.path.join("/opt/container_artifact", "ansible_inventory.json"), "w") as outfile:
            json.dump(obfuscate_vars(inventory), outfile, sort_keys=True, indent=4, ensure_ascii=False)
    elif args.write_to_stdout:
        #remove keys we don't want to print
        inventory_to_dump = prep_for_yaml_out(inventory)
        print("---")
        print(yaml.dump(inventory_to_dump, default_flow_style=False))
    else:
        print(json.dumps(inventory))


if __name__ == "__main__":
    main()
