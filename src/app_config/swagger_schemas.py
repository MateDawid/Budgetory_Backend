from drf_yasg.inspectors import SwaggerAutoSchema

KEYS_TO_OMIT: tuple[str] = ("users", "categories")


class CustomAutoSchema(SwaggerAutoSchema):
    """Custom Swagger schema."""

    def get_tags(self, operation_keys: tuple | None = None) -> list[str]:  # pragma: no cover
        """
        Prepares more detailed tags.

        Args:
            operation_keys:  An array of keys derived from the path describing the hierarchical layout
            of this view in the API; e.g. ``('wallets', 'deposits', 'list')``, etc.

        Returns:
            list[str]: List of tags.
        """
        operation_keys = operation_keys or self.operation_keys

        tags = self.overrides.get("tags")
        if not tags:
            if len(operation_keys) == 1 or operation_keys[0] in KEYS_TO_OMIT:
                tags = [operation_keys[0]]
            else:
                tags = [" ".join(operation_keys[:-1])]
        return tags
