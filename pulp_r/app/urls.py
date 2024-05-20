from django.urls import include, path
from rest_framework import routers

from pulp_r.app import viewsets

router = routers.DefaultRouter()
router.register(r'packages', viewsets.RPackageViewSet)
router.register(r'remotes', viewsets.RRemoteViewSet)
router.register(r'repositories', viewsets.RRepositoryViewSet)
router.register(r'publications', viewsets.RPublicationViewSet)
router.register(r'distributions', viewsets.RDistributionViewSet)

urlpatterns = [
    path('pulp/api/v3/r/', include((router.urls, 'r'), namespace='r')),
    path('pulp/api/v3/content/r/src/contrib/PACKAGES/<str:pk>/', viewsets.RDistributionViewSet.as_view({'get': 'packages'}), name='r-distribution-packages'),
]