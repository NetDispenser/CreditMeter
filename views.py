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

CREDITMETER_LOG_FULL_PATH='./meter.log'
logging.basicConfig(filename=CREDITMETER_LOG_FULL_PATH,level=logging.DEBUG, format=FORMAT)
mylogger = logging.getLogger('django')

def logout_view(request):
    logging.debug("logout_view")
    empty_session_id=logout(request)
    logging.debug("empty_session_id: %s"%empty_session_id)
    request.session.delete()
    return HttpResponseRedirect("/")

def keepalive(request):
	ip=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
	mylogger.debug("keepalive "+ip)
	#mylogger.debug('old '+request.POST['old'])
	return HttpResponse(int(random.random()*5000.))

def home(request):
	mylogger.debug("home");
	if request.user.is_authenticated():
		mylogger.debug("already authenticated:"+request.user.username)
		return app(request)

	ip=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
	mylogger.debug("not authenticated: %s"%(ip))
	if request.method == 'POST':
		mylogger.debug("getting login_pyld from post ...")
		mylogger.debug(request.POST["login_pyld"])
		pyld=json.loads(request.POST["login_pyld"])
		try:
			x=User.objects.get(username=pyld['device_name'])
			mylogger.debug("got user")
			login(request,x)
			mylogger.debug("logged-in user")
			return app(request)
		except:
			mylogger.debug("creating new account ...")
			acct=User.objects.create_user(username=pyld['device_name'],password='pycon2017')
			acct.userprofile.is_parent=False
			acct.userprofile.remote_username="guest"
			acct.userprofile.remote_password="pycon2017"
			acct.userprofile.save()
			acct.save()
			mylogger.debug("logging-in ...")
			login(request,acct)
			return app(request)

	mylogger.debug("home, not a post")
	device_options=mkDeviceOptions()
	IP=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
	opt=device_options[IP]
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
	credit_feeder_url="http://feeder.asymptopia.org/"
	try:
		qs=request.META['QUERY_STRING']

		if qs=='local_balance':
			rval=request.user.userprofile.credit_balance

		elif qs=='remote_balance':
			url='%sget?request=update&username=%s&password=%s'%(credit_feeder_url,request.user.userprofile.remote_username,request.user.userprofile.remote_password)
			with urllib.request.urlopen(url) as response:
				remote_balance = int(response.read())
			rval=remote_balance

		elif qs=='transfer_balance':
			url='%sget?request=transfer&username=%s&password=%s'%(credit_feeder_url,request.user.userprofile.remote_username,request.user.userprofile.remote_password)
			mylogger.debug(url)
			with urllib.request.urlopen(url) as response:
				transfer_amount=int(response.read())
			request.user.userprofile.credit_balance+=transfer_amount
			request.user.userprofile.save()
			rval=transfer_amount

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
