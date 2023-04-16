"""Shop_DJ URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from baton.autodiscover import admin
from django.conf import settings
from django.conf.urls.static import static
# from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Снип-Сноп'
admin.site.site_title = "Главная страница"
admin.site.index_title = 'Панель администрирования интернет-магазина "Снип-Сноп"'

urlpatterns = [

    path("select2/", include("django_select2.urls")),
    path('admin/', admin.site.urls),
    path("dynamic-admin-form/", include("dynamic_admin_forms.urls")),
    path('baton/', include('baton.urls')),
    path('accounts/', include('allauth.urls')),
    path('finance/', include('finance.urls')),
    path('nova_poshta', include('nova_poshta.urls')),
    path('root_app/', include('ROOTAPP.urls')),
    path('orders/', include('orders.urls')),
    path('', include('main_page.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('_nested_admin/', include('nested_admin.urls')),
    # path('__debug__/', include('debug_toolbar.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
