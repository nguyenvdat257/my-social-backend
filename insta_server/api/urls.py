from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.updateProfile, name="update-profile"),
    path('profile/<str:username>', views.getProfile, name="get-profile"),
    path('profile/suggest/', views.getSuggestProfile, name="get-suggest-profile"),
    path('profile/search/<str:keyword>', views.getSearchProfile, name="get-search-profile"),
]