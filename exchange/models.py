from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

# Create your models here.
class Exchange(models.Model):
	nation_code = models.CharField(max_length=30)
	exData = models.TextField()
	created_date = models.DateTimeField(blank=True, null=True)

	def publish(self):
		self.created_date = timezone.now()
		self.save()

	def __str__(self):
		return self.nation_code.encode('utf-8')