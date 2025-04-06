# In clinic/permissions.py
from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Custom permission to only allow users with 'admin' role.
    """
    message = "Access denied. User must have the 'admin' role."

    def has_permission(self, request, view):
        # Check if user is authenticated and has the role 'admin'
        return request.user and request.user.is_authenticated and request.user.role == 'admin'