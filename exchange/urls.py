from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name="show_exchangeRate"),
	url(r'^store/$', views.store, name="store_exchangeRate"),
]
