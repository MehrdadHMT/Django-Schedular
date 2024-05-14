from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# See: https://docs.djangoproject.com/en/dev/ref/contrib/admin/#hooking-adminsite-instances-into-your-urlconf
admin.autodiscover()

SpectacularAPIView.permission_classes = []
SpectacularAPIView.authentication_classes = []
SpectacularRedocView.permission_classes = []
SpectacularRedocView.authentication_classes = []
SpectacularSwaggerView.permission_classes = []
SpectacularSwaggerView.authentication_classes = []


def health(request):
    return HttpResponse("OK")


urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('__debug__/', include('debug_toolbar.urls')),
    path('admin/', admin.site.urls),
    path('liveness/', health),
    path('readiness/', health),

    # Supported version1 routes
    path('api/v1/tasks/', include("apps.tasks.v1.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
