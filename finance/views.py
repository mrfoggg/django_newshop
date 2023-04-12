from django.shortcuts import render
from jsonview.decorators import json_view


# Create your views here.

@json_view
def update_prices_ajax_for_order_admin(request):
    return {'info': 'info'}
