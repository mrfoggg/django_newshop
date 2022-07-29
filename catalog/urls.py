from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from .views import MainPageView

app_name = 'category'
urlpatterns = [
    path('<slug:slug>/', MainPageView.as_view(), name='index'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
