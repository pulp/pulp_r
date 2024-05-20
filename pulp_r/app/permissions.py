from rest_framework.permissions import BasePermission


class PackagesPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'packages':
            return True
        return False