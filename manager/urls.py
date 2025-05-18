from django.contrib import admin
from django.urls import path
from manager import views  # Update with your actual app name
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include

urlpatterns = [
    path('manager/',views.manager,name="manager"),
    path('delete-car/<int:car_id>/', views.delete_car, name='delete_car'),
    path('edit-car/<int:car_id>/', views.edit_car, name='edit_car'),
    path('available_car_manager/', views.available_cars_manager, name='available_car_manager'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)