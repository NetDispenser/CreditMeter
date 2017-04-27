import time
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
