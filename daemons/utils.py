import time,os,datetime

CREDITMETER_LOG_FULL_PATH='/var/www/meter/creditmeter/meter.log'
CREDITMETERD_PORT=8210
CREDIT_FEEDER_URL="http://www.creditfeed.me/"
CREDITMETER_PID='/var/run/creditmeter.pid'
CREDITMETER_HOSTNAME="192.168.22.1"

LAN0="eth0"
LAN1="wlan1"
WAN="wlan0"

def mktstamp():
	tstamp="%s"%datetime.datetime.now()
	truncated=tstamp.split(".")[0]
	return  truncated

def mkDeviceOptions(whichkey):#'device_ip','device_mac'
	opts={'keys':[],}
	inf=open('/var/lib/misc/dnsmasq.leases')
	lines=inf.readlines()
	inf.close()
	for line in lines:
		split_line=line.split(" ")
		opt={}
		opt['lease_time']=split_line[0]
		opt['human_lease_time']=time.ctime(eval(split_line[0]))
		opt['device_mac']=split_line[1]
		opt['device_ip']=split_line[2]
		opt['device_name']=split_line[3]
		opt['xtra_mac']=split_line[4]#NEED:lookup (again)
		#opts.append(opt['device_mac'])
		key=opt[whichkey]
		opts[key]=opt
		opts['keys'].append(key)

	return opts

def getDefaultPolicy():
	common=[
		"iptables -F",
		"iptables -t nat -F",
		"iptables -P INPUT ACCEPT",
		"iptables -P OUTPUT ACCEPT",
		"iptables -P FORWARD DROP",
		"iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT",
		"iptables -I INPUT 1 -i %s -j ACCEPT"%(LAN1),
		"iptables -I INPUT 1 -i %s -j ACCEPT"%(LAN0),
		"iptables -I INPUT 1 -i lo -j ACCEPT",
		"iptables -A INPUT -p UDP --dport bootps ! -i wlan0 -j REJECT",
		"iptables -A INPUT -p UDP --dport domain ! -i wlan0 -j REJECT",
		"iptables -A INPUT -p TCP ! -i wlan0 -d 0/0 --dport 0:1023 -j DROP",
		"iptables -A INPUT -p UDP ! -i wlan0 -d 0/0 --dport 0:1023 -j DROP",
		"iptables -A INPUT -p UDP --dport bootps ! -i %s -j REJECT"%(LAN0),
		"iptables -A INPUT -p UDP --dport bootps ! -i %s -j REJECT"%(LAN1),
		"iptables -A INPUT -p UDP --dport domain ! -i %s -j REJECT"%(LAN0),
		"iptables -A INPUT -p UDP --dport domain ! -i %s -j REJECT"%(LAN1),
		"iptables -A INPUT -p TCP --dport ssh -i %s -j ACCEPT"%(WAN),
		"iptables -A POSTROUTING -t nat -o %s -j MASQUERADE"%(WAN),
	]
	whitelist_macs=["B8:E8:56:26:E4:B0",]
	for mac in whitelist_macs:
		cmds=[
			"iptables -I FORWARD -i %s -m mac --mac-source %s -j ACCEPT"%(LAN0,mac),
			"iptables -I FORWARD -i %s -m mac --mac-source %s -j ACCEPT"%(LAN1,mac),
			"iptables -I FORWARD -i %s -m mac --mac-source %s -j ACCEPT"%(WAN,mac),
		]
		common+=cmds

	whitelist_urls=["www.creditfeed.me",]
	for url in whitelist_urls:
		cmds=[
			"iptables -A FORWARD  -p tcp -d %s --dport 80 -j ACCEPT"%(url),
		]
		common+=cmds

	return common

def getWideOpenPolicy():
	wide_open=[
		"iptables -F",
		"iptables -t nat -F",
		"iptables -P INPUT ACCEPT",
		"iptables -P OUTPUT ACCEPT",
		"iptables -P FORWARD ACCEPT",
		#"iptables -P FORWARD ACCEPT",
		"iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT",
		"iptables -I INPUT 1 -i %s -j ACCEPT"%(LAN1),
		"iptables -I INPUT 1 -i %s -j ACCEPT"%(LAN0),
		"iptables -I INPUT 1 -i lo -j ACCEPT",
		"iptables -A INPUT -p UDP --dport bootps ! -i %s -j REJECT"%(LAN0),
		"iptables -A INPUT -p UDP --dport bootps ! -i %s -j REJECT"%(LAN1),
		"iptables -A INPUT -p UDP --dport domain ! -i %s -j REJECT"%(LAN0),
		"iptables -A INPUT -p UDP --dport domain ! -i %s -j REJECT"%(LAN1),
		"iptables -A INPUT -p TCP --dport ssh -i %s -j ACCEPT"%(WAN),
		#
		"iptables -t nat -A POSTROUTING -o %s -j MASQUERADE"%(WAN),
	]
	#	"iptables -t nat -A POSTROUTING -o %s -j MASQUERADE"%(WAN),
	#	"echo 1 > /proc/sys/net/ipv4/ip_forward",
	return wide_open
