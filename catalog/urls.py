from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.decorators.cache import cache_page

from .views import CategoryView, ProductView

app_name = 'catalog'
urlpatterns = [
    # path('<slug:slug>/', cache_page(600)(CategoryView.as_view()), name='category'),
    # path('<slug:slug>/', CategoryView.as_view(), name='category'),
    # path('product/<slug:slug>/', ProductView.as_view(), name='product')
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
