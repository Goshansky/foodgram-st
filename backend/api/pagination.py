from rest_framework.pagination import PageNumberPagination
from django.conf import settings


class RecipePagination(PageNumberPagination):
    page_size = settings.RECIPES_PER_PAGE
    page_size_query_param = settings.PAGE_SIZE_QUERY_PARAM
    max_page_size = settings.MAX_PAGE_SIZE
