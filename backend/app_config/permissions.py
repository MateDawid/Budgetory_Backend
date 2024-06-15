from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class UserBelongsToBudgetPermission(permissions.BasePermission):
    """Permission class for checking User access to Budget."""

    message: str = 'User does not have access to Budget.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Checks if User is owner or member of Budget passed in URL.

        Args:
            request [Request]: User request.
            view [APIView]: View on which request was made.

        Returns:
            bool: True if User is owner or member of Budget, else False.
        """
        budget = getattr(view, 'budget', None)
        return bool(budget and request.user and (request.user == budget.owner or request.user in budget.members.all()))
