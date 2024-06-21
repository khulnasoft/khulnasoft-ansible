#!/usr/bin/env python
#
# These tests specifically exercise the following:
# - Multiple platform support (centos, debian, redhat)
# - Khulnasoft version 7.3.1.1
# - khulnasoft.forward_servers allows for manually inserting forwarding destinations

from __future__ import absolute_import
import os

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

def test_user_seed(host):
    f = host.file("{}/etc/system/local/user-seed.conf".format(KHULNASOFT_HOME))
    assert not f.exists

def test_ui_login(host):
    f = host.file("{}/etc/.ui_login".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP

def test_khulnasoft_version(host):
    f = host.file("{}/etc/khulnasoft.version".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP
    assert f.contains("VERSION=7.3.1.1")

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

def test_khulnasoft_hec_inputs(host):
    f = host.file("{}/etc/apps/khulnasoft_httpinput/local/inputs.conf".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP
    assert f.contains("[http]")
    assert f.contains("disabled = 0")
    assert f.contains("[http://khulnasoft_hec_token]")
    assert f.contains("token = abcd1234")

def test_inputs_conf(host):
    f = host.file("{}/etc/system/local/inputs.conf".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP
    assert f.contains("[khulnasofttcp://9997]")
    assert f.contains("disabled = 0")

def test_khulnasoft_ports(host):
    output = host.run("netstat -tuln")
    assert "0.0.0.0:8000" in output.stdout
    assert "0.0.0.0:8089" in output.stdout
    assert "0.0.0.0:8088" in output.stdout
    assert "0.0.0.0:8191" in output.stdout
    assert "0.0.0.0:9997" in output.stdout
    assert "127.0.0.1:8065" in output.stdout

def test_khulnasoft_hec(host):
    output = host.run('curl -k https://localhost:8088/services/collector/event \
        -H "Authorization: Khulnasoft abcd1234" -d \'{"event": "helloworld"}\'')
    assert "Success" in output.stdout

def test_khulnasoftd(host):
    output = host.run("curl -k https://localhost:8089/services/server/info \
        -u admin:helloworld")
    assert "Khulnasoft" in output.stdout

def test_outputs_conf(host):
    f = host.file("{}/etc/system/local/outputs.conf".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP
    assert f.contains("[indexAndForward]")
    assert f.contains("index = false")

def test_forward_servers(host):
    f = host.file("{}/etc/system/local/outputs.conf".format(KHULNASOFT_HOME))
    assert f.exists
    assert f.user == KHULNASOFT_USER
    assert f.group == KHULNASOFT_GROUP
    assert f.contains("\\[tcpout-server://forwarder1.test.com:9997\\]")
    assert f.contains("\\[tcpout-server://forwarder2.test.com:9997\\]")
    assert f.contains("\\[tcpout:default-autolb-group\\]")
    assert f.contains("server = forwarder1.test.com:9997,forwarder2.test.com:9997")
