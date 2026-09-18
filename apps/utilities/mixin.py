from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PaginationMixin:
    pagination_class = CustomPagination

    def should_paginate(self, request):
        query_params = getattr(request, "query_params", {})
        return any(
            query_params.get(name) is not None
            for name in ("page", "page_size")
        )

    def paginate_query(self, queryset, request, view=None):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=view)
        return paginator, page

    def get_paginated_response(self, paginator, data):
        return paginator.get_paginated_response(data)

    def paginate_list(self, request, queryset, serializer_class, context=None):
        if not self.should_paginate(request):
            serializer = serializer_class(
                queryset,
                many=True,
                context=context or {},
            )
            return Response(serializer.data)

        paginator, page = self.paginate_query(queryset, request, view=self)
        serializer = serializer_class(
            page,
            many=True,
            context=context or {},
        )
        return self.get_paginated_response(paginator, serializer.data)