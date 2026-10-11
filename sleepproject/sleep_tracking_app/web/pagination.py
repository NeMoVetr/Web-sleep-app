"""Shared cursor pagination for authenticated statistics pages."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from cursor_pagination import CursorPaginator, InvalidCursor
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.views import View


@dataclass(frozen=True)
class CursorPage:
    items: Any
    page_size: int
    next_cursor: str | None
    prev_cursor: str | None


class CursorPaginatedView(LoginRequiredMixin, View, ABC):
    ordering: tuple[str, ...] = ()
    default_page_size = 7
    max_page_size = 100
    http_method_names = ["get", "head", "options"]

    @abstractmethod
    def get_queryset(self, request):
        """Return records scoped to the authenticated user."""
        raise NotImplementedError

    @abstractmethod
    def render_page(self, request, pagination: CursorPage):
        """Build the page's existing HTML or JSON response."""
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        try:
            page_size = int(request.GET.get("page_size", self.default_page_size))
        except (ValueError, TypeError):
            return HttpResponseBadRequest("Некорректный размер страницы.")
        if not 1 <= page_size <= self.max_page_size:
            return HttpResponseBadRequest("Размер страницы должен быть от 1 до 100.")
        before, after = request.GET.get("before"), request.GET.get("after")
        if before and after:
            return HttpResponseBadRequest("Укажите только один курсор: before или after.")
        queryset = self.get_queryset(request)
        paginator = CursorPaginator(queryset, ordering=self.ordering)
        try:
            cursor = before or after
            if cursor:
                positions = paginator.decode_cursor(cursor)
                if len(positions) != len(self.ordering):
                    raise InvalidCursor("Invalid number of cursor fields")
                for ordering, value in zip(self.ordering, positions):
                    model_field = queryset.model._meta.get_field(ordering.lstrip("-"))
                    if value is None and not model_field.null:
                        raise InvalidCursor("Null cursor position for a required field")
                    model_field.to_python(value)
            page = (paginator.page(last=page_size, before=before) if before
                    else paginator.page(first=page_size, after=after))
        except (InvalidCursor, ValidationError, ValueError, TypeError):
            return HttpResponseBadRequest("Некорректный курсор страницы.")
        pagination = CursorPage(
            items=page,
            page_size=page_size,
            next_cursor=paginator.cursor(page[-1]) if page and page.has_next else None,
            prev_cursor=paginator.cursor(page[0]) if page and page.has_previous else None,
        )
        return self.render_page(request, pagination)
