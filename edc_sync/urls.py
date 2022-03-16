from django.urls import  include, path
from edc_constants.constants import UUID_PATTERN
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .admin import edc_sync_admin
from .views import DumpToUsbView, HomeView, RenderView
from .views import OutgoingTransactionViewSet, IncomingTransactionViewSet
from .views import TransactionCountView, SyncReportView


router = DefaultRouter()
router.register(r'outgoingtransaction', OutgoingTransactionViewSet)
router.register(r'incomingtransaction', IncomingTransactionViewSet)

app_name = 'edc_sync'

urlpatterns = [
    path('admin/', edc_sync_admin.urls),
    path('api/transaction-count/$',
        TransactionCountView.as_view(), name='transaction-count'),
    path('dump-to-usb/$',
        DumpToUsbView.as_view(), name='dump-to-usb'),
    path('sync-report/$',
        SyncReportView.as_view(), name='sync-report'),
    path('api/', include(router.urls)),
    path('api-token-auth/', obtain_auth_token),
    path('render/(?P<model_name>\w+)/(?P<pk>{})/'.format(UUID_PATTERN.pattern),
        RenderView.as_view(), name='render_url'),
    path('', HomeView.as_view(), name='home_url'),
]
