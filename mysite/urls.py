from django.contrib import admin
from django.urls import path
from myapp import views  # Update with your actual app name
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include

urlpatterns = [
    path('home/<str:full_name>/', views.home, name='home'),
    path('available-cars/', views.available_cars, name='available_cars'),
    path('car/<int:car_id>/', views.car_details, name='car_details'),
    path('admin/', views.main_admin, name='main_admin'),
    path('delete-car/<int:car_id>/', views.delete_car, name='delete_car'),
    path('edit-car/<int:car_id>/', views.edit_car, name='edit_car'),
    path('add-car/', views.add_car, name='add_car'),
    path('buy-car/<int:car_id>/', views.buy_car, name='buy_car'), 
    path('sold_cars/', views.sold_cars_list, name='sold_cars_list'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('customer/<int:signup_id>/', views.customer_detail, name='customer_detail'),
    path('', include('manager.urls')),
    # Ensure correct naming
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)