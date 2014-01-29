#! /usr/bin/python

import random
import xmlrpclib
import argparse
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser()

    # Global arguments
    parser.add_argument("-u","--username",
            type=str,
            required=True,
            help="cobble api user")
    parser.add_argument("-p", "--password",
            type=str,
            required=True,
            help="cobbler api user password")
    parser.add_argument("-s","--cobbler_server",
            type=str,
            required=True,
            help="cobbler server")
    parser.add_argument("-H", "--hostname",
            type=str,
            required=True,
            help="the system hostname")
    parser.add_argument("-R", "--realm",
            type=str,
            required=True,
            help="the rest of the hosts FQDN") 
    parser.add_argument("-k","--kvm_host",
            type=str,
            required=True,
            help="name of the host system")

    subparsers = parser.add_subparsers(dest='subparser_name')

    # "create" parser
    create_parser = subparsers.add_parser('create')
    create_parser.add_argument("-P","--profile",
            type=str,
            required=True,
            help="cobbler profile to use")
    create_parser.add_argument("-e0","--eth0",
            type=str,
            required=True,
            help="network inerface properties")
    create_parser.add_argument("-g0","--gw0",
            type=str,
            required=True,
            help="eth0 gateway")
    create_parser.add_argument("-d","--disk",
            type=str,
            required=False,
            help="disk space in GB to allocate VM")
    create_parser.add_argument("-m","--ram",
            type=str,
            required=False,
            help="memory in MB to allocate VM")

    # "create_dual" parser
    create_dual_parser = subparsers.add_parser('create-dual')
    create_dual_parser.add_argument("-P","--profile",
            type=str,
            required=True,
            help="cobbler profile to use")
    create_dual_parser.add_argument("-e0","--eth0",
            type=str,
            required=True,
            help="network inerface properties")
    create_dual_parser.add_argument("-g0","--gw0",
            type=str,
            required=True,
            help="eth0 gateway")
    create_dual_parser.add_argument("-e1","--eth1",
            type=str,
            required=True,
            help="network inerface properties")
    create_dual_parser.add_argument("-g1","--gw1",
            type=str,
            required=True,
            help="eth0 gateway")
    create_dual_parser.add_argument("-d","--disk",
            type=str,
            required=False,
            help="disk space in GB to allocate VM")
    create_dual_parser.add_argument("-m","--ram",
            type=str,
            required=False,
            help="memory in MB to allocate VM")

    destroy_dual_parser = subparsers.add_parser('destroy')

    gchurn_parser = subparsers.add_parser('gchurn')
    gchurn_parser.add_argument("-e","--email",
            type=str,
            required=True,
            help="The gmail account that will be used to access the spreadsheet")
    gchurn_parser.add_argument("-p","--passwd",
            type=str,
            required=True,
            help="The password associated with the gmail account")
    gchurn_parser.add_argument("-s","--spreadsheet",
            type=str,
            required=True,
            help="ID of the spreadsheet,Find this value in the url with 'key=XXX' and enter 'XXX'")

    return parser.parse_args()

def dispatch(args):
    function_map = {
        "create": cobblerize,
        "create-dual": cobblerize_dual,
        "destroy" : cobbler_delete,
        "gchurn" : cobbler_gchurn,
    }
    func = function_map[args.subparser_name]
    return func(args)

#get a mac address for your interface
def cobblerize(arg):
    if args.eth0:
        genmac0 = mac_generator()

#set FQDN, turn the hostname into an FQND
    fqdn = args.hostname + . + realm

#setup your cobbler session wth the cobbler server
    cobbler_server_api = 'http://' + args.cobbler_server + '/cobbler_api'
    server  = xmlrpclib.Server(cobbler_server_api)
    token = server.login(args.username,args.password)

# create new system in cobbler and commit sync
    system_id = server.new_system(token)
    server.modify_system(system_id,"name",args.hostname,token)
    server.modify_system(system_id,"hostname",fqdn,token)
    server.modify_system(system_id,"kernel_options","kotps=serial console=ttyS0,115200",token)
    server.modify_system(system_id,"kernel_options","kotps-post=serial console=ttyS0,115200",token)
    server.modify_system(system_id,"virt_file_size",args.disk,token)
    server.modify_system(system_id,"virt_ram",args.ram,token)
    server.modify_system(system_id,'modify_interface', {
        "macaddress-eth0" : genmac0 ,
        "ipaddress-eth0" : args.eth0 ,
        "netmask-eth0" : "255.255.255.0",
        "gateway-eth0" : args.gw0,
        "virtualbridge-eth0" : "br0",
        "static-eth0" : "1",
        },token)
    server.modify_system(system_id,"profile",args.profile,token)
    server.save_system(system_id,token)
    server.sync(token)
    koan(args.cobbler_server, args.hostname, args.kvm_host)

def cobblerize_dual(arg):
    if args.eth0:
        genmac0 = mac_generator()
    if args.eth1:
        genmac1 = mac_generator()

#set FQDN, turn the hostname into an FQND
    fqdn = args.hostname + . + realm

#setup your cobbler session wth the cobbler server
    cobbler_server_api = 'http://' + args.cobbler_server + '/cobbler_api'
    server  = xmlrpclib.Server(cobbler_server_api)
    token = server.login(args.username,args.password)

# create new system in cobbler and commit sync
    system_id = server.new_system(token)
    server.modify_system(system_id,"name",args.hostname,token)
    server.modify_system(system_id,"hostname",fqdn,token)
    server.modify_system(system_id,"kernel_options","kotps=serial console=ttyS0,115200",token)
    server.modify_system(system_id,"kernel_options","kotps-post=serial console=ttyS0,115200",token)
    server.modify_system(system_id,"virt_file_size",args.disk,token)
    server.modify_system(system_id,"virt_ram",args.ram,token)
    server.modify_system(system_id,'modify_interface', {
        "macaddress-eth0" : genmac0 ,
        "ipaddress-eth0" : args.eth0 ,
        "netmask-eth0" : "255.255.255.0",
        "staticroutes":"10.0.0.0/8:" + args.gw0, 
        "virtualbridge-eth0" : "br0",
        "static-eth0" : "1",
        },token)
    server.modify_system(system_id,'modify_interface', {
        "macaddress-eth1" : genmac1 ,
        "ipaddress-eth1" : args.eth1 ,
        "netmask-eth1" : "255.255.255.0",
        "gateway-eth1" : args.gw1,
        "virtualbridge-eth1" : "br1",
        "static-eth1" : "1",
        },token)
    server.modify_system(system_id,"profile",args.profile,token)
    server.save_system(system_id,token)
    server.sync(token)
    koan(args.cobbler_server, args.hostname, args.kvm_host)

#Function to churn multiple VMs from CSV file
def cobbler_gchurn(args):
    pass

# Send the command to the KVM server to spin up the guest
def koan(cobbler_server, hostname, kvm_host):
    command = "koan " + " --server=" + args.cobbler_server + " --system=" + args.hostname + " --virt" +" --force-path" 
    print command
    ssh = subprocess.Popen(["ssh","root@" "%s" % args.kvm_host, command],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == [ ]:
        error =  ssh.stderr.readlines()
        print >> sys.stderr, "ERROR: %s" % error
    else:
        print result

#Function that removes a cobbler system
def cobbler_delete(args):
    cobbler_server_api = 'http://' + args.cobbler_server + '/cobbler_api'
    server  = xmlrpclib.Server(cobbler_server_api)
    token = server.login(args.username,args.password)

    server.system_remove(args.hostname,token)
    if server.find_system({"hostname":hostname}):
        print "system deleted"
    else:
        print "error, system has not been removed"

#Function to generate random mac address for virtual machine
def mac_generator():
    mac = [ 0x00, 0x16, 0x3e,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff) ]
    X = ':'.join(map(lambda x: "%02x" % x, mac))
    return(X.upper())

if __name__ == "__main__" :
    args = parse_args()
    dispatch(args)
