from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('collection/<str:collection_name>/', views.view_collection, name='view_collection'),
    path('collection/<str:collection_name>/query/', views.perform_query, name='perform_query'),
]