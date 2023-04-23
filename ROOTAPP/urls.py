from django.urls import path

from ROOTAPP.views import (ByNowView, CheckoutView, ProductActionsView,
                           add_email, del_user_phone,
                           get_and_check_registration_phone,
                           get_registration_name, google_response, logout_view,
                           regenerate_sms_token, request_google_auth,
                           update_user_personal, update_user_phones,
                           verify_sms_token, get_settlement_info, ajax_updates_person_phones_info)

app_name = 'root_app'
urlpatterns = [
    path('product_actions/', ProductActionsView.as_view(), name='product_actions'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('by_now/', ByNowView.as_view(), name='by_now'),
    path('get_and_check_registration_phone/', get_and_check_registration_phone, name='get_and_check_registration_phone'),
    path('get_registration_name/', get_registration_name, name='get_registration_name'),
    path('regenerate_sms_token/', regenerate_sms_token, name='regenerate_sms_token'),
    path('verify_sms_token/', verify_sms_token, name='verify_sms_token'),
    path('logout/', logout_view, name='logout'),
    path('add_email/', add_email, name='add_email'),
    path('update_user_personal/', update_user_personal, name='update_user_personal'),
    path('update_user_phones/', update_user_phones, name='update_user_phones'),
    path('del_user_phone/', del_user_phone, name='del_user_phone'),
    path('get_settlement_info/', get_settlement_info, name='get_settlement_info'),
    path('ajax_updates_person_phones_info/', ajax_updates_person_phones_info, name='ajax_updates_person_phones_info'),
    # path('request_google_auth/', request_google_auth, name='request_google_auth'),
    # path('google_response/', google_response, name='google_response'),
]
