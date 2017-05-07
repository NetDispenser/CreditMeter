import time,os,datetime

CREDITMETER_LOG_FULL_PATH='/var/www/meter/creditmeter/meter.log'
CREDITMETERD_PORT=8210
CREDIT_FEEDER_URL="http://feeder.asymptopia.org/"
CREDITMETER_PID='/var/run/creditmeter.pid'
CREDITMETER_HOSTNAME="192.168.22.1"

LAN0="eth0"
LAN1="wlan1"
WAN="wlan0"

def mktstamp():
	tstamp="%s"%datetime.datetime.now()
	truncated=tstamp.split(".")[0]
	return  truncated

def mkDeviceOptions():
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
		key=opt['device_ip']
		opts[key]=opt
		opts['keys'].append(key)

	return opts

def getAirOnly():
	air_only=[
		"iptables -A FORWARD  -m mac --mac-source B8:E8:56:26:E4:B0 -j ACCEPT"
	]
	return air_only

def getMACOnly(MAC):

	mac_only=[
		"iptables -A FORWARD -i %s -m mac --mac-source %s -j ACCEPT"%(LAN0,MAC),
		"iptables -A FORWARD -i %s -m mac --mac-source %s -j ACCEPT"%(LAN1,MAC),
		"iptables -A FORWARD -i %s -m mac --mac-source %s -j ACCEPT"%(WAN,MAC),
	]
	return mac_only

def getCommon():
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
	#	"iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT",
	return common

def getWideOpen():
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

def getWideClosed():
	wide_closed=[
		"iptables -F",
		"iptables -t nat -F",
		"iptables -P INPUT ACCEPT",
		"iptables -P OUTPUT ACCEPT",
		"iptables -P FORWARD DROP",
		"iptables -I INPUT 1 -i %s -j ACCEPT"%(LAN1),
		"iptables -I INPUT 1 -i lo -j ACCEPT",
		"iptables -A INPUT -p UDP --dport bootps ! -i %s -j REJECT"%(LAN1),
		"iptables -A INPUT -p UDP --dport domain ! -i %s -j REJECT"%(LAN1),
		"iptables -A INPUT -p TCP ! -i %s -d 0/0 --dport 0:1023 -j DROP"%(LAN1),
		"iptables -A INPUT -p UDP ! -i %s -d 0/0 --dport 0:1023 -j DROP"%(LAN1),
		"iptables -t nat -A POSTROUTING -o %s -j MASQUERADE"%(WAN),
	]
	return wide_closed

def setWideOpen():
	wide_open=getWideOpen()
	for gidx in range(len(wide_open)):
		ip_cmd=wide_open[gidx]
		print(ip_cmd)
		os.system(ip_cmd)
	os.system('iptables -S')
	return 'success'

def setWideClosed():
	wide_closed=getWideClosed()
	for gidx in range(len(wide_closed)):
		ip_cmd=wide_closed[gidx]
		print(ip_cmd)
		os.system(ip_cmd)
	os.system('iptables -S')
	return 'success'
