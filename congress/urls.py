from django.urls import path
from .views import house_not_home, i_am_the_senate

urlpatterns = [
   path("/house", house_not_home, name="house"),
   path("/senate", i_am_the_senate, name="senate"),
]
