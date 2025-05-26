from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Кастомный пагинатор с изменением названия поля размера страницы."""
    page_size_query_param = 'limit'
    page_size = 6