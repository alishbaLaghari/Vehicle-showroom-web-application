import datetime
import os  # Add this line
from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from mysite.settings import MEDIA_ROOT
from django.http import HttpResponse

# Create your views here.
def manager(request):
    with connection.cursor() as cursor:
        # Count total cars
        cursor.execute("SELECT COUNT(*) FROM Car")
        car_count = cursor.fetchone()[0]
        
        # Count sold cars
        cursor.execute("SELECT COUNT(*) FROM sold_cars")
        sold_car_count = cursor.fetchone()[0]
    
    # Set manager and admin count (hardcoded to 1)
    manager_count = 1
    admin_count = 1

    return render(request, 'manager.html', {
        'car_count': car_count,
        'sold_car_count': sold_car_count,
        'manager_count': manager_count,
        'admin_count': admin_count
    })




def available_cars_manager(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.id, c.name, c.details, c.discount, c.price, c.image, 
                   COALESCE(s.sold, FALSE) AS sold,
                   s.sold_date
            FROM Car c
            LEFT JOIN sold_cars s ON c.id = s.car_id
        """)
        cars = cursor.fetchall()

    return render(request, 'available_cars_manager.html', {'cars': cars, 'MEDIA_URL': settings.MEDIA_URL})



def add_car(request):
    if request.method == "POST":
        car_name = request.POST.get('name')
        car_details = request.POST.get('details')
        car_discount = request.POST.get('discount')
        car_price = request.POST.get('price')
        car_image = request.FILES.get('image')

        if car_image:
            # Create the full path for the image
            image_path = os.path.join('uploaded_images', car_image.name)

            # Save the car details into the database with the relative image path
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Car (name, details, discount, price, image)
                    VALUES (%s, %s, %s, %s, %s)
                """, [car_name, car_details, car_discount, car_price, image_path])

            # Save the image to the uploaded_images folder
        with open(os.path.join(MEDIA_ROOT, image_path), 'wb+') as destination:
            for chunk in car_image.chunks():
               destination.write(chunk)

        return HttpResponseRedirect(reverse('available_cars'))

    return render(request, 'add_car.html')

def edit_car(request, car_id):
    if request.method == "POST":
        car_name = request.POST.get('name')
        car_details = request.POST.get('details')
        car_discount = request.POST.get('discount')
        car_price = request.POST.get('price')
        car_image = request.FILES.get('image')

        with connection.cursor() as cursor:
            if car_image:
                # Update the image if a new one is uploaded
                cursor.execute("""
                    UPDATE Car
                    SET name=%s, details=%s, discount=%s, price=%s, image=%s
                    WHERE id=%s
                """, [car_name, car_details, car_discount, car_price, car_image.name, car_id])

                # Save the new image
                with open(os.path.join(settings.MEDIA_ROOT, car_image.name), 'wb+') as destination:
                    for chunk in car_image.chunks():
                        destination.write(chunk)
            else:
                # Update without changing the image
                cursor.execute("""
                    UPDATE Car
                    SET name=%s, details=%s, discount=%s, price=%s
                    WHERE id=%s
                """, [car_name, car_details, car_discount, car_price, car_id])

        return redirect('available_car_manager')  # Update to redirect to the available cars manager

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Car WHERE id=%s", [car_id])
        car = cursor.fetchone()

    return render(request, 'edit_car.html', {'car': car, 'MEDIA_URL': settings.MEDIA_URL})

def delete_car(request, car_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM Car WHERE id=%s", [car_id])
    return redirect('available_cars_manager')
