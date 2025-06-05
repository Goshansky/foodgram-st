from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from rest_framework.response import Response


class RecipePagination(PageNumberPagination):
    page_size = settings.RECIPES_PER_PAGE
    page_size_query_param = settings.PAGE_SIZE_QUERY_PARAM
    max_page_size = settings.MAX_PAGE_SIZE

    # Для тестов в postman
    def get_paginated_response(self, data):
        for item in data:
            if "image" in item and item["image"] is None:
                item["image"] = ""

        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
