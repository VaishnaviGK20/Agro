from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from agro import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),

    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('reg/', views.reg, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),

    path('home/', views.home, name='home_alt'),
    path('seller/', views.seller, name='seller'),
    path('farmerpage/', views.farmerpage, name='farmerpage'),
    path('home1/', views.home1, name='home1'),
    path('add_item/', views.add_item, name='add_item'),
    path('delete1/<str:name>/', views.delete1, name='delete1'),
    path('upload-location/', views.upload_location, name='upload_location'),

    path('cart/', views.view_cart, name='view_cart'),
    path('cart/<str:name>/<str:price>/', views.cart, name='cart'),
    path('delete/<str:name>/', views.delete_cart_item, name='delete_cart'),

    path('info/', views.info, name='info'),
    path('order/', views.order, name='order'),
    path('order-history/', views.order_history, name='order_history'),
    path('user-orders/', views.user_order, name='user_order'),

    path('search/', views.search, name='search'),
    path('contactus/', views.contactus, name='contactus'),
    path('aboutus/', views.aboutus, name='aboutus'),

    path('payment/', views.payment_page, name='payment'),
    path('create_order/', views.create_order, name='create_order'),
    path('verify_payment/', views.verify_payment, name='verify_payment'),
    path('get_cart_total/', views.get_cart_total, name='get_cart_total'),

    path('admin-login/', views.admin_login, name='admin_login'),
    path('admins/', views.admins, name='admins'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('view-requests/', views.view_requests, name='view_requests'),
    path('tables/', views.display_tables, name='display_tables'),

    # Legacy redirects for old broken URLs
    path('home/reg/', views.reg),
    path('home/reg/login/', views.user_login),
    path('reg/login/', views.user_login),
    path('home2/', views.home2),
    path('logout', views.logout_view),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
