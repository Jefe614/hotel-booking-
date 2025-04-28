# restaurant/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('book/', views.book_table, name='book_table'),
    path('book/success/<int:reservation_id>/', views.booking_success, name='booking_success'),
    path('manage/', views.manage, name='manage'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('mpesa/stkpush/', views.mpesa_stk_push, name='mpesa_stk_push'),

]