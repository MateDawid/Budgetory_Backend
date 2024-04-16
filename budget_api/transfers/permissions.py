from rest_framework.permissions import BasePermission
from transfers.models.transfer_category import TransferCategory


class IsPersonalTransferCategoryOwnerOrAdmin(BasePermission):
    """Permission to check if user admin or personal TransferCategory owner."""

    message = 'User is not an owner of TransferCategory.'

    def has_permission(self, request, view):
        """Checks if request user is admin or owner of TransferCategory."""
        is_admin = bool(request.user and request.user.is_staff)
        if is_admin:
            return True
        category = TransferCategory.objects.filter(id=request.parser_context.get('kwargs', {}).get('pk'))
        is_owner = bool(
            request.user
            and category.exists()
            and category.first().scope == TransferCategory.PERSONAL
            and category.first().user == request.user
        )
        return is_owner
