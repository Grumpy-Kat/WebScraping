from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^webscraping/', views.webscraping, name='webscraping')
]