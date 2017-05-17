"""meter URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
import runninglog.views as runninglog_views
import creditmeter.views as creditmeter_views
import xtcpd.views as xtcpd_views

urlpatterns = [
    url(r'^runninglog/logout$',runninglog_views.logout_view,name='logout'),
    url(r'^runninglog/get$',runninglog_views.get,name='runninglog_get'),
    url(r'^runninglog/serve$',runninglog_views.serve,name='serve'),
    url(r'^runninglog/',runninglog_views.home,name='runninglog'),
    url(r'^traffic',xtcpd_views.traffic),
    url(r'^load_student$',creditmeter_views.load_student,name='load_student'),
    url(r'^save_student$',creditmeter_views.save_student,name='save_student'),
    url(r'^status_update$',creditmeter_views.status_update,name='status_update'),
    url(r'^logout$',creditmeter_views.logout_view,name='logout'),
    url(r'^keepalive$',creditmeter_views.keepalive,name='keepalive'),
    url(r'^admin/', admin.site.urls),
    url(r'^lanwatch$',xtcpd_views.lanwatch,name='lanwatch'),
    url(r'^get$',creditmeter_views.get,name='creditmeter_get'),
    url(r'^$',creditmeter_views.home,name='home'),
]
