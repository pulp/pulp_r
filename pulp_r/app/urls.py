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
    path('pulp/api/v3/', include(router.urls)),
]