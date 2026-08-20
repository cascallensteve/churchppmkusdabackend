from django.urls import path
from accounts import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('account/me/', views.account_me_view, name='account_me'),
    path('account/profile/', views.profile_view, name='profile'),
    path('account/set-pin/', views.set_pin_view, name='set_pin'),
    path('account/change-password/', views.change_password_view, name='change_password'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),
]
