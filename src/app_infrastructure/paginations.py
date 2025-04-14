from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    page_size = None  # None value enables to return all objects when no pagination params passed.
    page_size_query_param = "page_size"
    max_page_size = 1000
