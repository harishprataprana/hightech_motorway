from django.contrib import admin
from django.urls import path, include, re_path
from .import views, user_login
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin', admin.site.urls),

    path('base', views.BASE, name='base'),
    path('404', views.PAGE_NOT_FOUND, name='404'),

    path('', views.HOME, name='home'),

    path('courses', views.SINGLE_COURSE, name='single_course'),
    path('courses/filter-data',views.filter_data,name="filter-data"),
    path('course/<slug:slug>', views.COURSE_DETAILS, name="course_details"),
    path('search', views.SEARCH_COURSE, name="search_course"),


    path('contact', views.CONTACT_US, name='contact_us'),

    path('about', views.ABOUT_US, name='about_us'),

    path('accounts/register', user_login.REGISTER, name='register'),

    path('verify/<str:token>', user_login.verify),
    # path('verification/', include('verify_email.urls')),

    path('accounts/', include('django.contrib.auth.urls')),
    # path('accounts/', include('allauth.urls')),

    path('doLogin', user_login.DO_LOGIN, name='doLogin'),

    path('accounts/profile', user_login.PROFILE, name='profile'),

    path('accounts/profile/update', user_login.PROFILE_UPDATE, name='profile_update'),
    path('checkout/<slug:slug>', views.CHECKOUT, name='checkout'),
    path('my-course', views.MY_COURSE, name='my-course'),
    path('verify_payment', views.VERIFY_PAYMENT, name='verify_payment'),
    path('course/watch-course/<slug:slug>', views.WATCH_COURSE, name='watch_course'),

    path('update-currencies', views.UPDATE_CURRENCIES, name='update_currencies'),

    # path('password-reset/',
    #     PasswordResetView.as_view(
    #         template_name='passwordReset/password_reset.html',
    #         html_email_template_name='emailTemplates/forget_password.html'
    #     ),
    #     name='password-reset'
    # ),
    # path('password-reset/done/', PasswordResetDoneView.as_view(template_name='passwordReset/password_reset_done.html'),name='password_reset_done'),
    # path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='passwordReset/password_reset_confirm.html'),name='password_reset_confirm'),
    # path('password-reset-complete/',PasswordResetCompleteView.as_view(template_name='passwordReset/password_reset_complete.html'),name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
