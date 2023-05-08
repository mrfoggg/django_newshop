from django.urls import path

from orders.views import (cancel_oneclick, create_one_click_order,
                          oneclick_add_comment, pre_create_order, get_person_info_ajax,
                          get_persons_and_contacts_by_phone_ajax, button_add_number_to_person_ajax)

urlpatterns = [
    path('by_one_click/', create_one_click_order, name='by_one_click'),
    path('oneclick_add_comment', oneclick_add_comment, name='oneclick_add_comment'),
    path('cancel_oneclick', cancel_oneclick, name='cancel_oneclick'),
    path('pre_create_order', pre_create_order, name='pre_create_order'),
    path('get_person_info_ajax', get_person_info_ajax, name='get_person_info_ajax'),
    path('get_persons_and_contacts_by_phone_ajax', get_persons_and_contacts_by_phone_ajax,
         name='get_persons_and_contacts_by_phone_ajax'),
    path('button_add_number_to_person_ajax', button_add_number_to_person_ajax, name='button_add_number_to_person_ajax'),
]
app_name = 'orders'
