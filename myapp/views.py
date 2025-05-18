import os  # Add this line
from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from mysite.settings import MEDIA_ROOT
from django.http import HttpResponse
import datetime
from django.db import connection
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password


def signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        dob = request.POST.get('dob', '')
        gender = request.POST.get('gender', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')  # Ensure this is email
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Check if the passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        with connection.cursor() as cursor:
            # Check if the email is already registered
            cursor.execute("SELECT * FROM customer_signin WHERE email = %s", [email])
            if cursor.fetchone():
                messages.error(request, "Email already in use.")
                return render(request, 'signup.html')

            # Insert customer data into signup table
            cursor.execute(
                "INSERT INTO customer_details (full_name, dob, gender, phone, email) VALUES (%s, %s, %s, %s, %s)",
                [full_name, dob, gender, phone, email]
            )

            # Get the ID of the newly created signup entry
            signup_id = cursor.lastrowid

            # Insert email, password, and foreign key reference into customer_signin table
            cursor.execute(
                "INSERT INTO customer_signin (email, password, signup_id) VALUES (%s, %s, %s)",
                [email, password, signup_id]
            )

            messages.success(request, "Signup successful! Please log in.")
            return redirect('signin')

    return render(request, 'signup.html')


def signin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM customer_signin WHERE email = %s AND password = %s",
                [email, password]
            )
            user = cursor.fetchone()

            if user:
                signup_id = user[3]  # Assuming signup_id is the 4th column
                if signup_id is None:
                    messages.error(request, "Signup ID not found.")
                    return render(request, 'signin.html')

                # Store the signup_id in the session
                request.session['signup_id'] = signup_id

                cursor.execute("SELECT full_name FROM customer_details WHERE id = %s", [signup_id])
                full_name_result = cursor.fetchone()
                full_name = full_name_result[0] if full_name_result else None
                
                if full_name:
                    messages.success(request, "Login successful! Welcome, {}.".format(full_name))
                    return redirect('home', full_name=full_name)  # Pass full name here
                else:
                    messages.error(request, "Full name not found.")
            else:
                messages.error(request, "Invalid email or password.")

    return render(request, 'signin.html')



from django.core.files.storage import FileSystemStorage

def customer_detail(request, signup_id):
    # Fetch user details from the database
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM customer_details WHERE id = %s", [signup_id])
        user = cursor.fetchone()  # Fetch user details

    if user:
        if request.method == 'POST':
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            profile_photo_url = user[6]  # Keep the old profile photo URL by default

            # Handle profile photo upload if it exists
            if 'profile_photo' in request.FILES:
                profile_photo = request.FILES['profile_photo']
                fs = FileSystemStorage()  # Create a FileSystemStorage instance
                filename = fs.save(profile_photo.name, profile_photo)  # Save the file
                profile_photo_url = fs.url(filename)  # Get the URL of the saved file

            # Update only editable fields in the database
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE customer_details SET full_name = %s, phone = %s, email = %s, profile_photo = %s WHERE id = %s",
                    [full_name, phone, email, profile_photo_url, signup_id]
                )
            
            messages.success(request, "Profile updated successfully.")
            return redirect('customer_detail', signup_id=signup_id)

        # Render user details to the template
        return render(request, 'customer_details.html', {
            'user': {
                'full_name': user[1],  # Assuming full_name is the second column
                'gender': user[3],      # Assuming gender is the fourth column
                'dob': user[2],         # Assuming dob is the third column
                'phone': user[4],       # Assuming phone is the fifth column
                'email': user[5],       # Assuming email is the sixth column
                'profile_photo': user[6] # Assuming profile_photo is the seventh column
            }
        })
    else:
        messages.error(request, "User not found.")
        return redirect('home')


def home(request, full_name):
    signup_id = request.session.get('signup_id')  # Get signup_id from session
    with connection.cursor() as cursor:
        cursor.execute(""" 
            SELECT c.id, c.name, c.details, c.discount, c.price, c.image, 
                   COALESCE(s.sold, FALSE) AS sold 
            FROM Car c 
            LEFT JOIN sold_cars s ON c.id = s.car_id 
        """)
        cars = cursor.fetchall()

    return render(request, 'home.html', {
        'cars': cars,
        'MEDIA_URL': settings.MEDIA_URL,
        'full_name': full_name,  # Pass the username to the template
        'signup_id': signup_id   # Pass the signup_id to the template
    })


def available_cars(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.id, c.name, c.details, c.discount, c.price, c.image, 
                   COALESCE(s.sold, FALSE) AS sold
            FROM Car c
            LEFT JOIN sold_cars s ON c.id = s.car_id
        """)
        cars = cursor.fetchall()
    
    return render(request, 'available_cars.html', {'cars': cars, 'MEDIA_URL': settings.MEDIA_URL})

def car_details(request, car_id):
    signup_id = request.session.get('signup_id')  # Get signup_id from session
    full_name = None
    
    if signup_id:
        with connection.cursor() as cursor:
            cursor.execute("SELECT full_name FROM customer_details WHERE id = %s", [signup_id])
            full_name_result = cursor.fetchone()
            full_name = full_name_result[0] if full_name_result else None
    
    with connection.cursor() as cursor:
        cursor.execute(""" 
            SELECT c.id, c.name, c.details, c.discount, c.price, c.image, 
                   COALESCE(s.sold, FALSE) AS sold
            FROM Car c
            LEFT JOIN sold_cars s ON c.id = s.car_id
            WHERE c.id = %s
        """, [car_id])
        car = cursor.fetchone()

    return render(request, 'car_details.html', {
        'car': car, 
        'MEDIA_URL': settings.MEDIA_URL,
        'full_name': full_name  # Pass full_name to the template
    })


def main_admin(request):
    with connection.cursor() as cursor:
        # Count total cars
        cursor.execute("SELECT COUNT(*) FROM Car")
        car_count = cursor.fetchone()[0]
        
        # Count sold cars
        cursor.execute("SELECT COUNT(*) FROM sold_cars")
        sold_car_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customer_details")
        customers= cursor.fetchone()[0]
    
    
    # Set manager and admin count (hardcoded to 1)
    admin_count = 1

    return render(request, 'admin_panel.html', {
        'car_count': car_count,
        'sold_car_count': sold_car_count,
        'customers': customers,
        '': admin_count
    })

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
    return redirect('available_cars')

# views.py

from django.utils import timezone

def buy_car(request, car_id):
    if request.method == "POST":
        # Fetch payment details from form
        location = request.POST.get("location")
        card_number = request.POST.get("card_number")
        cvc = request.POST.get("cvc")
        pin = request.POST.get("pin")
        
        customer_id = request.session.get("signup_id")  # Assuming customer ID is in session

        if not customer_id:
            messages.error(request, "You must be logged in to purchase.")
            return redirect("signin")
        
        sold_date = timezone.now()  # Get the current date and time
        
        # Insert data into sold_cars table and mark the car as sold
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sold_cars (car_id, customer_id, location, card_number, cvc, pin, sold, sold_date)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s)
                """,
                [car_id, customer_id, location, card_number, cvc, pin, sold_date]
            )
        
        messages.success(request, "Purchase successful! Car has been marked as sold with the purchase date.")
        return redirect("car_details", car_id=car_id)

    return redirect("car_details", car_id=car_id)

def execute_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchall()
    
def sold_cars_list(request):
    query = """
        SELECT c.name, s.sold_date, cu.full_name, cu.phone, s.location, 
               c.price, c.discount, c.image
        FROM sold_cars s
        JOIN Car c ON s.car_id = c.id
        JOIN customer_details cu ON s.customer_id = cu.id
    """
    sold_cars = execute_query(query)

    return render(request, 'sold_car_details.html', {'sold_cars': sold_cars, 'MEDIA_URL': settings.MEDIA_URL})