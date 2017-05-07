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
	dt=s.keepalive(request.user.userprofile.mac_addrs)
	mylogger.debug("ahh :)")
	request.user.userprofile.credit_balance-=dt
	request.user.userprofile.save()

	return HttpResponse(request.user.userprofile.credit_balance)

def home(request):
	mylogger.debug("home");
	if request.user.is_authenticated():
		mylogger.debug("already authenticated:"+request.user.username)
		return app(request)

	IP=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
	mylogger.debug("not authenticated: %s"%(IP))
	device_options=mkDeviceOptions()
	opt=device_options[IP]

	if request.method == 'POST':
		mylogger.debug("getting login_pyld from post ...")
		mylogger.debug(request.POST["login_pyld"])
		pyld=json.loads(request.POST["login_pyld"])
		try:
			uname=pyld['device_name']+"_STUDENT"
			if pyld["account_type"]=="parent":uname=pyld['device_name']+"_PARENT"
			x=User.objects.get(username=uname)
			mylogger.debug("got user")
			login(request,x)
			mylogger.debug("logged-in user")
			return app(request)
		except:
			mylogger.debug("creating new account ...")
			new_uname=pyld['device_name']+"_STUDENT"
			if pyld["account_type"]=="parent":new_uname=pyld['device_name']+"_PARENT"
			acct=User.objects.create_user(username=new_uname,password='pycon2017')
			acct.userprofile.is_parent=False
			if pyld["account_type"]=="parent":acct.userprofile.is_parent=True
			acct.userprofile.remote_username="guest"#change via /admin (i.e. django admin)
			acct.userprofile.remote_password="pycon2017"#for demo purposes everyone takes credits from same remote account (guest, pycon2017)
			acct.userprofile.mac_addrs.append(opt['device_mac'])#initialize with mac of device being used to create account
			acct.userprofile.save()
			acct.save()

			mylogger.debug("logging-in ...")
			login(request,acct)
			return app(request)

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

		elif qs=='json_status_report':
			s=xmlrpc.client.Server(server_str)
			mylogger.debug("calling daemon for status_report")
			rval=s.json_status_report()

		elif qs=='wide_open':
			s=xmlrpc.client.Server(server_str)
			rval=s.wide_open()

		elif qs=='wide_closed':
			s=xmlrpc.client.Server(server_str)
			rval=s.wide_closed()

	except:mylogger.exception("UhOh")
	return HttpResponse(rval);

@login_required
def app(request):
	mylogger.debug("app")
	context={
		'title':'CreditMeter',
		'username':request.user.username,
		'is_parent':request.user.userprofile.is_parent,
		'credit_balance':request.user.userprofile.credit_balance,
		'remote_username':request.user.userprofile.remote_username,
		'remote_password':request.user.userprofile.remote_password,
	}
	return render(request,'creditmeter.html',context)
