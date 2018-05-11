from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^index', views.index, name='index'),
	url(r'^webscraping', views.webscraping, name='webscraping'),
	url(r'^(?P<taskId>[\w-]+)/$', views.getWebscrapingTask, name='getWebscrapingTask')
]