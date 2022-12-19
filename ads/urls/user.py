from django.urls import path

from ads import views

urlpatterns = [
    path('', views.AdUserListView.as_view()),
    path('<int:pk>/', views.AdUserDetailView.as_view()),
    path('create/', views.AdUserCreateView.as_view()),
    path('<int:pk>/update/', views.AdUserUpdateView.as_view()),
    path('<int:pk>/delete/', views.AdUserDeleteView.as_view()),
]

