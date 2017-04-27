# -*- coding: UTF-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required,user_passes_test

from creditmeter.daemons.utils import *

import os,logging,time,json,sys,urllib.request
import xmlrpc.client

FORMAT = 'VIEW: %(message)s'

RLOG_FULL_PATH='./meter.log'
logging.basicConfig(filename=RLOG_FULL_PATH,level=logging.DEBUG, format=FORMAT)
mylogger = logging.getLogger('django')

def logout_view(request):
    logging.debug("logout_view")
    empty_session_id=logout(request)
    logging.debug("empty_session_id: %s"%empty_session_id)
    request.session.delete()
    return HttpResponseRedirect("/meter")

def home(request):
	mylogger.debug("home");
	if request.user.is_authenticated():
		mylogger.debug("already authenticated:"+request.user.username)
		return app(request)
	else:
		ip=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
		mylogger.debug("not authenticated: %s"%(ip))
		if request.method == 'POST':
			mylogger.debug(request.POST["pyld"])
			pyld=json.loads(request.POST["pyld"])
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

	return render(
		request,'device-login.html',#login.html
		context
	)

@login_required
def app(request):
	mylogger.debug("HOME")
	if request.method=='POST':
		try:
			mylogger.debug("POST")
			str_pyld=request.POST["pyld"]
			json_pyld=json.loads(str_pyld)
			mylogger.debug(str_pyld)
			s=xmlrpc.client.Server("http://192.168.22.1:8210")

			if json_pyld['action']=='update_remote_balance':
				mylogger.debug("update_remote_balance")
				#rval=s.update_remote_balance(request.user.username,request.user.userprofile.remote_username,request.user.userprofile.remote_password);
				url='http://feeder.asymptopia.org/get?request=update&username=%s&password=%s'%(request.user.userprofile.remote_username,request.user.userprofile.remote_password)
				mylogger.debug(url)
				with urllib.request.urlopen(url) as response:
					remote_balance = int(response.read())
				#response.close()
				rval={'remote_balance':remote_balance}

			elif json_pyld['action']=='transfer_remote_balance':
				mylogger.debug("transfer_remote_balance")
				url='http://feeder.asymptopia.org/get?request=transfer&username=%s&password=%s'%(request.user.userprofile.remote_username,request.user.userprofile.remote_password)
				mylogger.debug(url)
				with urllib.request.urlopen(url) as response:
					transfer_amount=int(response.read())
				remote_balance=0#it must if no errors
				#response.close()
				request.user.userprofile.credit_balance+=transfer_amount
				request.user.userprofile.save()
				mylogger.debug("userprofile updated by: "+str(transfer_amount))
				rval={
					'local_balance':request.user.userprofile.credit_balance,
					'transfer_amount':transfer_amount,
					'remote_balance':remote_balance,
				}

			else:
				rval="unk"

			mylogger.debug(rval)
			return HttpResponse(json.dumps(rval))

		except:
			pass
			#mylogger.exception("Something wrong ...")
			#they're logged-in so give em the default page.  If they got here
			#it's because POST=login in this case.

	context={
		'title':'CreditMeter',
		'username':request.user.username,
		'is_parent':request.user.userprofile.is_parent,
		'credit_balance':request.user.userprofile.credit_balance,
		'remote_username':request.user.userprofile.remote_username,
		'remote_password':request.user.userprofile.remote_password,
	}
	return render(request,'creditmeter.html',context)
