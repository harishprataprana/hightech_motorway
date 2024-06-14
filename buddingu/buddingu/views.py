from django.core.mail.backends import console
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render,redirect
from app.models import Categories, Course, Level, Author, Video, UserCourse, CustomUser, Payment, Lesson, ratesEUR
from django.template.loader import render_to_string
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .settings import *
import razorpay
from time import time
# from django.contrib.gis.geoip2 import GeoIP2
import json
from django.http import HttpResponse
# import geoip2.database
import requests
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def BASE(request):
    return render(request, 'base.html')


def HOME(request):
    login_status = False
    if request.user.is_authenticated:
        login_status = True
    currency_symbol = '₹'
    currency_code = 'inr'
    country_code = 'in'
    multiplier = 1
    if request.method == "POST":
        country_data = request.POST.get('textarea')
        country_dict = json.loads(country_data)
        currency_symbol = country_dict['currency_symbol']
        currency_code = country_dict['currency_code']
        country_code = country_dict['country_code']
        rate = ratesEUR.objects.values_list(currency_code, flat=True)
        multiplier = rate[0]

    category = Categories.objects.all().order_by('id')[0:5]
    course = Course.objects.filter(status='PUBLISH').order_by('id')
    print('Course:',course)
    context = {
        'category': category,
        'course': course,
        'currency_symbol': currency_symbol,
        'currency_code': currency_code,
        'country_code': country_code,
        'multiplier': multiplier,
        'login_status': login_status,
    }
    return render(request, 'Main/home.html', context)


def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    author = Author.objects.all()
    level = Level.objects.all()
    course = Course.objects.all()
    number_of_courses = 0

    all_courses = Course.objects.all()
    # Number of courses to display per page
    courses_per_page = 2
    # Create a Paginator object
    paginator = Paginator(all_courses, courses_per_page)

    # Get the current page number from the request's GET parameters
    page = request.GET.get('page')

    try:
        # Get the courses for the requested page
        courses = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        courses = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page
        courses = paginator.page(paginator.num_pages)


    if course:
        number_of_courses = course.count()
    FreeCourse_count = Course.objects.filter(price = 0).count()
    PaidCourse_count = Course.objects.filter(price__gte = 1).count()

    context = {
        'category': category,
        'author': author,
        'level': level,
        'course': courses,
        # 'courses': courses,
        'FreeCourse_count': FreeCourse_count,
        'PaidCourse_count': PaidCourse_count,
        'number_of_courses': number_of_courses,
    }

    return render(request, 'Main/single_course.html', context)


def filter_data(request):
    category = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')

    if price == ['PriceFree']:
        course = Course.objects.filter(price=0)
    elif price == ['PricePaid']:
        course = Course.objects.filter(price__gte=1)
    elif price == ['PriceAll']:
        course = Course.objects.all()
    elif category:
        course = Course.objects.filter(category__id__in = category).order_by('-id')
    elif level:
        course = Course.objects.filter(level__id__in = level).order_by('-id')
    else:
        course = Course.objects.all().order_by('-id')

    context = {
        'course':course
    }
    t = render_to_string('ajax/course.html', context)
    return JsonResponse({'data':t})


def CONTACT_US(request):
    category = Categories.get_all_category(Categories)
    context = {
        'category':category
    }
    return render(request, 'Main/contact_us.html', context)


def ABOUT_US(request):
    category = Categories.get_all_category(Categories)
    context = {
        'category':category
    }
    return render(request, 'Main/about_us.html', context)


def SEARCH_COURSE(request):
    category = Categories.get_all_category(Categories)
    query = request.GET['query']
    course = Course.objects.filter(title__icontains = query)
    context = {
        'course': course,
        'category': category,
    }
    return render(request, 'search/search.html', context)


def COURSE_DETAILS(request, slug):
    category = Categories.get_all_category(Categories)
    course = Course.objects.filter(slug = slug)
    time_duration = Video.objects.filter(course__slug = slug).aggregate(sum=Sum('time_duration'))
    print("*****************")
    print(time_duration['sum'])
    time_duration_string = '0'
    if time_duration['sum']:
        time_duration_string = str(time_duration['sum'])+" "+"mins" if time_duration['sum'] < 60 else str(time_duration['sum'] // 60)+" " + "hrs"+ " "+str(time_duration['sum'] % 60)+" "+ "mins"

    course_id = Course.objects.get(slug = slug)
    print("Request: ",request.user.is_authenticated)
    if request.user.is_authenticated:
        login_status = True
        try:
            check_enrollment = UserCourse.objects.get(user = request.user, course = course_id)
        except UserCourse.DoesNotExist:
            check_enrollment = None

        if course.exists():
            course = course.first()
        else:
            return redirect('404')
        context = {
            'course': course,
            'category': category,
            'time_duration_string': time_duration_string,
            'check_enrollment': check_enrollment,
            'login_status': login_status,
            }
        return render(request, 'course/course_details.html', context)
    login_status = False
    if course.exists():
        course = course.first()
    else:
        return redirect('404')
    context = {
        'course': course,
        'category': category,
        'time_duration_string': time_duration_string,
        'login_status': login_status,
        }
    return render(request, 'course/course_details.html', context)


def PAGE_NOT_FOUND(request):
    category = Categories.get_all_category(Categories)
    context = {
        'category':category
    }
    return render(request, 'error/404.html', context)


client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))


def CHECKOUT(request, slug):
    course = Course.objects.get(slug=slug)
    courseTitle = course.title
    form_action = request.GET.get('action')
    order = None
    if course.price == 0:
        course = UserCourse(
            user=request.user,
            course=course,
        )
        course.save()
        messages.success(request, f'Successfully enrolled for FREE course - {courseTitle}!')
        return redirect('my-course')

    elif form_action == 'create_payment':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        country = request.POST.get('country')
        address_1 = request.POST.get('address_1')
        address_2 = request.POST.get('address_2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postcode = request.POST.get('postcode')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        order_comments = request.POST.get('order_comments')

        amount_cal = course.price - (course.price * course.discount / 100)
        amount = int(amount_cal)*100

        currency = "INR"
        notes = {
            "name": f'{first_name} {last_name}',
            "country": country,
            "address": f'{address_1} {address_2}',
            "city": city,
            "state": state,
            "postcode": postcode,
            "phone": phone,
            "email": email,
            "order_comments": order_comments,
        }
        receipt = f"Skola-{int(time())}"
        order = client.order.create(
            {
                'receipt': receipt,
                'notes': notes,
                'amount': amount,
                'currency': currency,
            }
        )
        payment = Payment(
            course=course,
            user=request.user,
            order_id=order.get('id')
        )
        payment.save()
    context = {
        'course': course,
        'order': order,
    }
    return render(request, 'checkout/checkout.html', context)


def MY_COURSE(request):
    course = UserCourse.objects.filter(user = request.user)
    number_of_enrolled_courses = 0
    if course:
        number_of_enrolled_courses = course.count()
    context = {
        'course': course,
        'number_of_enrolled_courses': number_of_enrolled_courses,
    }
    return render(request, 'course/my-course.html', context)


@csrf_exempt
def VERIFY_PAYMENT(request):
    if request.method == "POST":
        data = request.POST

        try:
            client.utility.verify_payment_signature(data)
            razorpay_order_id = data['razorpay_order_id']
            razorpay_payment_id = data['razorpay_order_id']

            payment = Payment.objects.get(order_id = razorpay_order_id)
            payment.payment_id = razorpay_payment_id

            if payment.status is False:
                payment.status = True

                usercourse = UserCourse(
                    user = payment.user,
                    course = payment.course,
                    is_payment_done = True,
                )
                usercourse.save()
                payment.user_course = usercourse
                print("PAYMENT DATE: ", payment.date)
                payment.save()

                context = {
                    'data':data,
                    'payment':payment,
                }
                return render(request, 'verify_payment/success.html', context)
            else:
                return render(request, 'verify_payment/go_to_enrolled_courses.html')
        except:
            return render(request, 'verify_payment/fail.html')


def WATCH_COURSE(request, slug):
    course = Course.objects.filter(slug=slug)
    lecture = request.GET.get('lecture')

    if lecture is None:
        lecture = 1
    video = Video.objects.get(id=lecture)
    if course.exists():
        course = course.first()
    else:
        return redirect('404')
    context = {
        'course': course,
        'video': video,
    }
    return render(request, 'course/watch-course.html', context)


def UPDATE_CURRENCIES(request):
    try:
        response = requests.get("http://data.fixer.io/api/latest?access_key=c66feea8f8e355fd0afddb9bed95119c")
        rates_EUR = json.loads(response.content.decode('utf-8'))
        base = rates_EUR['base']
        rates = rates_EUR['rates']

        eqv_inr = rates_EUR['rates']['INR']
        eqv_inr = 1/eqv_inr

        aud = rates_EUR['rates']['AUD']
        aud = eqv_inr*aud

        print("aud: ",aud)

        cad = rates_EUR['rates']['CAD']
        cad = eqv_inr*cad

        print("cad: ",cad)

        inr = 1
        print("inr: ",inr)

        gbp = rates_EUR['rates']['GBP']
        gbp = eqv_inr*gbp

        print("gbp: ",gbp)

        usd = rates_EUR['rates']['USD']
        usd = eqv_inr*usd

        print("usd: ",usd)

        aud = aud
        cad = cad
        inr = inr
        gbp = gbp
        usd = usd
        print('rates: ',rates)
        rates_new = ratesEUR(base=base, aud=aud, cad=cad, inr=inr, gbp=gbp, usd=usd, rates=rates)
        print("rates_new", rates_new)
        rates_new.save()
        return HttpResponse("Thanks Admin for updating me..!! :)")
    except:
        return redirect('404')



def UPDATE_CURRENCY_SYMBOL(request):
    if request.method == "POST":
        country_name = request.POST.get('country_name')
        country_code = request.POST.get('country_code')
        print("COUNTRY_Name_is : ", country_name)
        pass


