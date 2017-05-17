# -*- coding: UTF-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required,user_passes_test

from creditmeter.daemons.utils import *

import os,logging,time,json,sys,urllib.request,random
import xmlrpc.client

FORMAT = 'VIEW: %(message)s'
logging.basicConfig(filename=CREDITMETER_LOG_FULL_PATH,level=logging.DEBUG, format=FORMAT)
mylogger = logging.getLogger('django')

server_str="http://%s:%d"%(CREDITMETER_HOSTNAME,CREDITMETERD_PORT)
#s=xmlrpc.client.Server(server_str)
#s=xmlrpc.client.Server("http://192.168.22.1:8011")
def logout_view(request):
    logging.debug("logout_view")
    empty_session_id=logout(request)
    logging.debug("empty_session_id: %s"%empty_session_id)
    request.session.delete()
    return HttpResponseRedirect("/")

def keepalive(request):
	ip=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
	if request.user.userprofile.credit_balance<0:
		mylogger.debug("Returning STOP to "+ip)
		return HttpResponse("STOP")
	else:
		mylogger.debug("Balance:%d"%(request.user.userprofile.credit_balance))


	mylogger.debug("keepalive "+ip)
	mylogger.debug(server_str)
	s=xmlrpc.client.Server(server_str)
	mylogger.debug("calling ...")
	mylogger.debug(type(request.user.userprofile.mac_addrs))
	mylogger.debug(len(request.user.userprofile.mac_addrs))
	dt=s.keepalive(request.user.userprofile.mac_addrs)
	mylogger.debug("ahh :)")
	request.user.userprofile.credit_balance-=dt
	request.user.userprofile.save()

	return HttpResponse(request.user.userprofile.credit_balance)

def verify_accounts(device_name,opt):

	student_uname="%s_STUDENT"%(device_name)
	parent_uname="%s_PARENT"%(device_name)

	try:
		acct=User.objects.get(username=student_uname)
		p=acct.userprofile
		if p.mac_addrs.count(opt['device_mac'])==0:
			p.mac_addrs.append(opt['device_mac'])
			p.save()
		mylogger.debug("verified "+student_uname)
	except:
		acct=User.objects.create_user(username=student_uname,password='pycon2017')
		p=acct.userprofile
		p.mac_addrs.append(opt['device_mac'])
		p.save()
		mylogger.debug("verify_accounts created "+student_uname)

	try:
		acct=User.objects.get(username=parent_uname)
		mylogger.debug("verified "+parent_uname)
	except:
		acct=User.objects.create_user(username=parent_uname,password='pycon2017')
		acct.userprofile.is_parent=True
		acct.userprofile.students.append(student_uname)
		acct.userprofile.save()
		acct.save()
		mylogger.debug("verify_accounts created "+parent_uname)

	return 0

def home(request):
	mylogger.debug("home");
	if request.user.is_authenticated():
		mylogger.debug("already authenticated:"+request.user.username)
		if request.user.userprofile.is_parent==True:
			return parent_app(request,request.user.username,{})
		return student_app(request,request.user.username,{})

	IP=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
	mylogger.debug("not authenticated: %s"%(IP))
	device_options=mkDeviceOptions('device_ip')
	opt=device_options[IP]

	if request.method == 'POST':
		mylogger.debug("getting login_pyld from post ...")
		mylogger.debug(request.POST["login_pyld"])
		pyld=json.loads(request.POST["login_pyld"])
		uname=None
		acct=None
		try:
			rval=verify_accounts(pyld['device_name'],opt)
			uname=pyld['device_name']+"_STUDENT"
			if pyld['account_type']=="parent":uname=pyld['device_name']+"_PARENT"
			acct=User.objects.get(username=uname)
			mylogger.debug("got user")
			login(request,acct)
			mylogger.debug("logged-in user "+uname)
			if acct.userprofile.is_parent==True:
				return parent_app(request,uname,pyld)

			return student_app(request,uname,pyld)

		except:
			mylogger.exception("Should not be here now")


	mylogger.debug("home, not a post")
	context={
		'title':'Credit Meter Login',
		'button_text':'Login',
		'lease_time':opt['lease_time'],
		'human_lease_time':opt['human_lease_time'],
		'device_mac':opt['device_mac'],
		'device_ip':opt['device_ip'],
		'device_name':opt['device_name'],
		'xtra_mac':opt['xtra_mac'],
	}
	mylogger.debug(json.dumps(context))
	return render(
		request,'device-login.html',#login.html
		context
	)

@login_required
def get(request):#remote balance query and xfer @here, plus others.
	rval=-999

	try:
		qs=request.META['QUERY_STRING']

		if qs=='local_balance':
			rval=request.user.userprofile.credit_balance

		elif qs=='remote_balance':
			url='%sget?request=update&username=%s&password=%s'%(CREDIT_FEEDER_URL,request.user.userprofile.remote_username,request.user.userprofile.remote_password)
			mylogger.debug(url)
			with urllib.request.urlopen(url) as response:
				remote_balance = int(response.read())
			rval=remote_balance

		elif qs=='transfer_balance':
			url='%sget?request=transfer&username=%s&password=%s'%(CREDIT_FEEDER_URL,request.user.userprofile.remote_username,request.user.userprofile.remote_password)
			mylogger.debug(url)
			with urllib.request.urlopen(url) as response:
				transfer_amount=int(response.read())
			request.user.userprofile.credit_balance+=transfer_amount
			request.user.userprofile.save()
			rval=transfer_amount

		#elif qs=='str_status_report':
		#	s=xmlrpc.client.Server(server_str)
		#	mylogger.debug("calling daemon for status_report")
		#	rval=s.str_status_report()

		elif qs=='wide_open':
			s=xmlrpc.client.Server(server_str)
			rval=s.wide_open()

		elif qs=='wide_closed':
			s=xmlrpc.client.Server(server_str)
			rval=s.write_default_policy()

	except:mylogger.exception("UhOh")
	return HttpResponse(rval);

@login_required
def student_app(request,uname,pyld):
	mylogger.debug("student_app")
	stripped_uname=uname[:12]
	context={
		'title':'Student@CreditMeter',
		'username':stripped_uname,
		'is_parent':request.user.userprofile.is_parent,
		'str_pyld':json.dumps(pyld),
		'credit_balance':request.user.userprofile.credit_balance,
		'remote_username':request.user.userprofile.remote_username,
		'remote_password':request.user.userprofile.remote_password,
	}
	return render(request,'student_app.html',context)

@login_required
def parent_app(request,uname,pyld):
	mylogger.debug("parent_app")
	stripped_uname=uname[:12]

	students=[]#actually gonna be all accounts but matching credit-feeder code @devel
	for u in User.objects.all():
		students.append(u.username)

	context={
		'title':'Parent@CreditMeter',
		'username':stripped_uname,
		'is_parent':request.user.userprofile.is_parent,
		'str_pyld':json.dumps(pyld),
		'str_students':json.dumps(students),
	}
	return render(request,'parent_app.html',context)

@login_required
def status_update(request):
	s=xmlrpc.client.Server(server_str)
	mylogger.debug("calling daemon for status_report")
	rval=s.json_status_report()
	rval['keys']=list(rval.keys())#mac keys
	#"f4:09:d8:65:ab:84": {"t_elapsed_total": 2814.0, "running": false, "t_elapsed": 40, "mac": "f4:09:d8:65:ab:84", "t_last": 1494861316.161425, "t_instantiation": "2017-05-14 20:05:31"},

	IP=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
	mylogger.debug("not authenticated: %s"%(IP))
	device_options=mkDeviceOptions('device_mac')#mac keys
	#['keys'],'lease_time','human_lease_time','device_mac','device_ip','device_name','xtra_mac'

	mylogger.debug("%d"%len(rval['keys']))
	mylogger.debug("%d"%len(device_options['keys']))

	for key in rval['keys']:
		rval[key]['device_name']='unk'
		rval[key]['device_mac']='unk'
		rval[key]['device_ip']='unk'
		rval[key]['lease_time']='unk'
		rval[key]['mac_addrs']=[]
		rval[key]['credits']=-999
		rval[key]['keys']=list(rval[key].keys())
		try:
			opt=device_options[key]
			mylogger.debug("got device_options for %s"%key)
			rval[key]['device_name']=opt['device_name']
			rval[key]['device_mac']=opt['device_mac']
			rval[key]['device_ip']=opt['device_ip']
			rval[key]['lease_time']=opt['lease_time']
			parent_username=opt['device_name']+"_PARENT"
			student_username=opt['device_name']+"_STUDENT"
			#there will be 2x accounts assoc w/ea mac_addr ... we're taking info for student -> parent
			acct=User.objects.get(username=student_username)
			rval[key]['mac_addrs']=acct.userprofile.mac_addrs
			rval[key]['credits']=acct.userprofile.credit_balance
		except:
			mylogger.exception("no device_options for %s"%key)

	return HttpResponse(json.dumps(rval))

@login_required
def save_student(request):
	mylogger.debug("save_student "+request.POST.get('username'))
	mylogger.debug(request.POST)
	try:
		mylogger.debug(request.POST.get('username'))
		mylogger.debug(request.POST.get('password'))
		mylogger.debug(request.POST.get('credit_balance'))
		mylogger.debug(request.POST.get('mac_addrs'))
		mylogger.debug(request.POST.get('is_parent'))
		mylogger.debug(request.POST.get('remote_username'))
		mylogger.debug(request.POST.get('remote_password'))
		acct=User.objects.get(username=request.POST.get('username'))
		if request.POST.get('password')!="******":
			acct.password=request.POST.get('password')
		p=acct.userprofile
		p.credit_balance=int(request.POST.get('credit_balance'))

		p.mac_addrs=[]
		for mac in request.POST.get('mac_addrs').split(','):
			p.mac_addrs.append(mac)
		p.save()
		mylogger.debug(type(p.mac_addrs))

		tf=request.POST.get('is_parent')
		p.is_parent=False;
		if tf=='true' or tf=='True':p.is_parent=True
		p.remote_username=request.POST.get('remote_username')
		p.remote_password=request.POST.get('remote_password')
		p.save()
		acct.save()
	except:
		mylogger.exception("Uhoh")
		return HttpResponse("ERROR SAVING")

	return HttpResponse("Success")

@login_required
def load_student(request):
	#Send a list of assignment sysopses to populate student queue
	str_pyld=request.POST["load_student_pyld"]
	json_pyld=json.loads(str_pyld)
	student_username=json_pyld['student_username']
	acct=User.objects.get(username=student_username)
	student_info={
		'username':acct.username,
		'mac_addrs':acct.userprofile.mac_addrs,
		'credit_balance':acct.userprofile.credit_balance,
		'remote_username':acct.userprofile.remote_username,
		'remote_password':acct.userprofile.remote_password,
		'is_parent':acct.userprofile.is_parent,
	}
	return HttpResponse(json.dumps(student_info))
