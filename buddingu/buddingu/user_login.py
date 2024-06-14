from urllib.parse import urlparse, parse_qs

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.models import User,auth
from django.contrib import messages
from app.emailBackend import EmailBackEnd
from django.contrib.auth import authenticate, login, logout
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.mail import send_mail
import uuid
# from verify_email.email_handler import send_verification_email
from app.models import CustomUser, Profile



def send_email_token(email, token):
    try:
        url = f'http://127.0.0.1:8000/verify/{token}'
        print("token = ",token)
        mydict = {'url': url, 'email': email}
        html_template = 'emailTemplates/verify_registration.html'
        html_message = render_to_string(html_template, context=mydict)
        subject = 'Please verify you account'
        email_from = 'portfolioharish@gmail.com'
        recipient_list = [email]
        message = EmailMessage(subject, html_message,
                                   email_from, recipient_list)
        message.content_subtype = 'html'
        message.send()
    except Exception as e:
        return False
    return True


def REGISTER(request):
    if request.method == "POST":
        # username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # check email

        if CustomUser.objects.filter(email=email).exists():
            messages.warning(request, 'Email Already Exists !')
            return redirect('register')

        # check username
        # if CustomUser.objects.filter(username=username).exists():
        #     messages.warning(request, 'Username Already Exists !')
        #     return redirect('register')

        else:

            # send_email_token(email, token)
            #user add to database
            user_obj = CustomUser(email = email)
            user_obj.set_password(password)
            user_obj.save()
            #verifyied token created
            p_obj = Profile.objects.create(
                user = user_obj,
                email_token = str(uuid.uuid4()),
            )
            send_email_token(email, p_obj.email_token)
            return render(request, 'registration/verify_email.html')


            # user = CustomUser.objects.create_user(
            #      password=password, email=email)
            # # mydict = {'username' : username}
            # user.set_password(password)
            # user.save()
            # html_template = 'emailTemplates/success_register.html'
            # html_message = render_to_string(html_template)
            # subject = 'Welcome to Insight Mathematics'
            # email_from = 'portfolioharish@gmail.com'
            # recipient_list = [email]
            # message = EmailMessage(subject, html_message,
            #                        email_from, recipient_list)
            # message.content_subtype = 'html'
            # message.send()
            # return redirect("login")

    return render(request, 'registration/register.html')


def verify(request, token):
    try:
        obj = Profile.objects.get(email_token = token)
        obj.is_verified = True
        obj.save()
        return HttpResponse("Your account is verified")
    except Exception as e:
        return HttpResponse("Invalid Token")



def DO_LOGIN(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            is_verified = Profile.objects.get(user=CustomUser.objects.get(email=email)).is_verified
        except Exception as e:
            messages.error(request, 'Email and Password Are Invalid, Please retry !')
            return redirect('login')

        if is_verified is True:

            user = EmailBackEnd.authenticate(request,
                                         username=email,
                                         password=password)
            if user != None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Email and Password Are Invalid, Please retry !')
                return redirect('login')
        else:
            # messages.error(request, 'Please verify your email')

            return render(request, 'registration/verify_email.html')


def PROFILE(request):
    if request.user.is_authenticated:
        return render(request, 'registration/profile.html')
    return redirect('login')



def PROFILE_UPDATE(request):
    if request.method == "POST":
        # username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        dial_code = request.COOKIES.get('dial_code')
        phone = request.POST.get('phone')
        modified_phone = dial_code+"-"+phone
        print(modified_phone)
        password = request.POST.get('password')

        user_id = request.user.id

        user = CustomUser.objects.get(id=user_id)

        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.modified_phone = modified_phone
        user.email = email


        if password != None and password != "":
            user.set_password(password)
        user.save()
        messages.success(request, 'Profile Successfully Updated. ')
        return redirect('profile')


