from django.db import models
from django.dispatch import receiver
from django.dispatch import dispatcher
from django.db.models.signals import post_save
from django.contrib.auth.models import User

class UserProfile(models.Model):
	user = models.OneToOneField(User, unique=True, on_delete=models.CASCADE)
	is_parent = models.BooleanField(default=False)
	credit_balance = models.IntegerField(default=1000)
	remote_username = models.CharField(max_length=20,blank=False)
	remote_password = models.CharField(max_length=20,blank=False)
	#NEED:mac addrs

def user_post_save(sender, instance, signal, *args, **kwargs):
	profile, new = UserProfile.objects.get_or_create(user=instance)

models.signals.post_save.connect(user_post_save, sender=User)
