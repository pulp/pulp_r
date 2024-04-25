from django.urls import include, path
from rest_framework import routers

from pulp_r.app import viewsets

router = routers.DefaultRouter()
router.register(r'packages', viewsets.CRANPackageViewSet)
router.register(r'remotes', viewsets.CRANRemoteViewSet)
router.register(r'repositories', viewsets.CRANRepositoryViewSet)
router.register(r'publications', viewsets.CRANPublicationViewSet)
router.register(r'distributions', viewsets.CRANDistributionViewSet)

urlpatterns = [
    path('pulp/api/v3/', include(router.urls)),
]