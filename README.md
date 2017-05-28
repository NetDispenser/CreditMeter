# CreditMeter
#Raspberry-Pi 3 Debian Files for CreditMeter

This repository contains various configuration files and other source code used
to build the Raspberry-Pi 3 CreditMeter device.

##Getting Started

###Installation of base Debian 7 (Jessie) system
Download the official Raspbian Jessie Lite (February 2017) from the
[raspberrypi.org website] (https://www.raspberrypi.org/downloads/raspbian/).  
The Lite version does not have a Desktop or X-Windows system.
Use at least an 8G micro SD card to install the image.  

##Web Server(s)
Install nginx as the default system web server. We will also configure uwsgi
as the communication layer between nginx and Django, the Python web framework.
```
apt-get install nginx uwsgi
```


We tell the system to start nginx at boot:
```
root@raspberrypi:/var/www# systemctl enable nginx
Synchronizing state for nginx.service with sysvinit using update-rc.d...
Executing /usr/sbin/update-rc.d nginx defaults
Executing /usr/sbin/update-rc.d nginx enable
```


Verify that the default nginx page is working on port 80.


###CreditMeter Interface
The CreditMeter interface is installed inside a python (3.5) virtualenv at /var/www/meter
as follows:
```
apt-get install python3-virtualenv
cd /var/www
virtualenv meter
cd meter
source bin/activate
pip2 install django
django-admin startproject meter .
chmod +x ./manage.py
./manage.py startapp creditmeter
```


###Configuring nginx, uwsgi and django

Here are the two resources used to configure uwsgi and django:
* [How to use Django with uWSGI](https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/uwsgi/)
* [Setting up Django and your web server with uWSGI and nginx](http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html)


Here are the important configuration files from this repository:
* /etc/nginx/sites-available/ndjinx_nginx.conf
* /var/www/ev/uwsgi_params
* /var/www/ev/nginx_uwsgi.ini


The last file, nginx_uwsgi.ini, refers to a socket at /var/www/ev/ndjinx.sock
which should be created manually with permissions 666.
```
root@raspberrypi:/var/www# ls -l /var/www/ev/ndjinx.sock
srw-rw-rw- 1 www-data www-data 0 Mar  2 13:17 /var/www/ev/ndjinx.sock
```


The uwsgi daemon is started from /etc/rc.local, which can be copied from this
repository.  Important Note:  The default /etc/rc.local has "#!/bin/sh -x" at
the top.  This needs to be replaced with "#!/bin/bash" else scripts fail.  The
copy from this repository contains the change, but in case you have chosen to
edit /etc/rc.local, rather than copying-in, then this is important to know!
```
/usr/local/bin/uwsgi --emperor /etc/uwsgi/vassals --uid www-data --gid www-data --touch-reload /var/www/meter/creditmeter/views.py --daemonize /var/log/uwsgi-emperor.log
```


The above command uses the --touch-reload flag, which tells uwsgi to reload
whenever the creditmeter's views.py file is modified or touched, which is important
during development.  


###Design of the website

The default Django webpage should be viewable at http://192.168.22.1.  
The website is a standard Django website in which requests are routed according
to the urls.py file, which sends each request to the appropriate handler of a
views.py file. Here is the essential file structure from the repository:
```
meter/
+-- __init__.py
+-- settings.py
+-- urls.py
+-- wsgi.py
creditmeter/
+-- daemon
|   +-- daemon.py
|   +-- creditmeterd
+-- meter.log
+-- __init__.py
+-- models.py
+-- static
|   +-- creditmeter
|       +-- css
|       |   +-- creditmeter.css
|       +-- images
|           +-- logo.png
+-- templates
|   +-- device_login.html
|   +-- parent_app.html
|   +-- student_app.html
+-- views.py
```

The Django backend cannot issue the system-wide configuration commands such 
as the iptables commands necessary to control the firewall.
For this we use a daemon and send commands to it using RPC (Remote Procedure
Calls) on port 8007 (arbitrary and hard-coded at the moment).  

The daemon is located in /var/www/meter/creditmeter/daemon/creditmeterd and derives from the
daemon.py in the same directory.  The daemon is started by /etc/rc.local, the
same place that we started the uwsgi daemon.  

The running of /etc/rc.local during startup is actually a service which is
managed like so:
```
systemctl enable (disable) rc.local
```

###settings.py and urls.py

In settings.py you should edit ALLOWED_HOSTS, INSTALLED_APPLICATIONS and
STATIC_ROOT.  The rest should be covered by defaults.  
```
INSTALLED_APPS = [
    ...
    'creditmeter',
]
ALLOWED_HOSTS = [192.168.22.1,]
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/meter/static/'
```

Make sure the directory /var/www/meter/static is defined.  
Also ensure that permissions are sufficient by issuing
"chown -R www-data /var/wwww/meter".

In urls.py needs to contain the following:
```
urlpatterns = [
    url(r'^load_student$',creditmeter_views.load_student,name='load_student'),
    url(r'^save_student$',creditmeter_views.save_student,name='save_student'),
    url(r'^status_update$',creditmeter_views.status_update,name='status_update'),
    url(r'^logout$',creditmeter_views.logout_view,name='logout'),
    url(r'^keepalive$',creditmeter_views.keepalive,name='keepalive'),
    url(r'^get$',creditmeter_views.get,name='creditmeter_get'),
    url(r'^$',creditmeter_views.home,name='home'),
]
```

###Database

The CreditMeter website adds a userprofile to the default Django user model:
```
class UserProfile(models.Model):
	user = models.OneToOneField(User, unique=True, on_delete=models.CASCADE)
	is_parent = models.BooleanField(default=False)
	credit_balance = models.IntegerField(default=1000)
	remote_username = models.CharField(max_length=20,blank=False)
	remote_password = models.CharField(max_length=20,blank=False)
	mac_addrs=PickledObjectField(default=[])

	def __unicode__(self):
		return self.user.username
```


The database is initialized using Django's ./manage.py script.
From within the virtualenv perform initial migration Django's database:
```
cd /var/www/meter
chmod +x ./manage.py
./manage.py makemigrations
./manage.py migrate
./manage.py createsuperuser
...<follow prompts>...
```

The above will initialize the database and create a table for the userprofile model.


###Static files

Django has a convention for managing static files.  Once the static file
pointers and locations have been created and specified (above) you need to
collect the static files using ./manage.py like this:
```
cd /var/www/meter
./manage.py collectstatic
```


<img src='screenshots/credit-meter-051117a.png'/>
<img src='screenshots/meterlogin.png'/>
<img src='screenshots/parent02.png'/>
<img src='screenshots/lanwatch2017g.png'/>
