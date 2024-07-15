from entities.models.entity import Entity
from rest_framework.permissions import BasePermission


class IsPersonalEntityOwnerOrAdmin(BasePermission):
    """Permission to check if user admin or personal Entity owner."""

    message = 'User is not an owner of Entity.'

    def has_permission(self, request, view):
        """Checks if request user is admin or owner of Entity."""
        entity = Entity.objects.filter(id=request.parser_context.get('kwargs', {}).get('pk'))
        is_admin = bool(request.user and request.user.is_staff)
        is_owner = bool(
            request.user
            and entity.exists()
            and entity.first().type == 'PERSONAL'
            and entity.first().user == request.user
        )
        return is_admin or is_owner
