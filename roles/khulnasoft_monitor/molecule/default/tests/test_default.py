#!/usr/bin/env python
#
# These tests specifically exercise the following:
# - Multiple platform support (centos, debian, redhat)
# - Khulnasoft version 8.0.3
# - Normal khulnasoft_monitor with minimal option set

from __future__ import absolute_import
import os
import json

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

KHULNASOFT_HOME = "/opt/khulnasoft"
KHULNASOFT_EXEC = "{}/bin/khulnasoft".format(KHULNASOFT_HOME)
KHULNASOFT_USER = KHULNASOFT_GROUP = "khulnasoft"


def test_khulnasoft_user_group(host):
    user = host.user(KHULNASOFT_USER)
    assert user.name == KHULNASOFT_USER
    assert user.group == KHULNASOFT_GROUP

def test_khulnasoft_installation(host):
    d = host.file(KHULNASOFT_HOME)
    assert d.is_directory
    assert d.user == KHULNASOFT_USER
    assert d.group == KHULNASOFT_GROUP
    f = host.file(KHULNASOFT_EXEC)
    assert f.is_file
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP

def test_khulnasoft_running(host):
    output = host.run("{} status".format(KHULNASOFT_EXEC))
    assert "running" in output.stdout

def test_ui_login(host):
    f = host.file("{}/etc/.ui_login".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP

def test_khulnasoft_pid(host):
    f = host.file("{}/var/run/khulnasoft/khulnasoftd.pid".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP

def test_mongod_lock(host):
    f = host.file("{}/var/lib/khulnasoft/kvstore/mongo/mongod.lock".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP

def test_bin_khulnasoft(host):
    f = host.file("{}".format(KHULNASOFT_EXEC))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP

def test_khulnasoft_ports(host):
    output = host.run("netstat -tuln")
    assert "0.0.0.0:8000" in output.stdout
    assert "0.0.0.0:8089" in output.stdout

def test_monitor(host):
    output = host.run("curl -k https://localhost:8089/servicesNS/nobody/khulnasoft_monitoring_console/configs/conf-khulnasoft_monitoring_console_assets/settings \
        -u admin:helloworld -d output_mode=json")
    output = json.loads(output.stdout)
    assert output["entry"][0]["content"]["disabled"] == False
