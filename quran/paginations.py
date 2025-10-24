from rest_framework.pagination import PageNumberPagination


class StandardResultSetPagination(PageNumberPagination):
    """
    Custom pagination class for Quran API views.

    Attributes:
        page_size (int): Default number of items per page.
        page_size_query_param (str): Query parameter name to set page size.
        max_page_size (int): Maximum allowed page size.

    Usage example:
        ?page=1&page-size=10
    """
    page_size: int = 10
    page_size_query_param: str = 'page-size'
    max_page_size: int = 50


class QuranResultPagination(PageNumberPagination):
    """
    Pagination class with smaller default page size for Quran results.

    Attributes:
        page_size (int): Default items per page (2).
        page_size_query_param (str): Query parameter to set page size.
        max_page_size (int): Maximum allowed page size (5).
    """
    page_size: int = 2
    page_size_query_param: str = 'page-size'
    max_page_size: int = 5


class VersePagination(PageNumberPagination):
    """
    Pagination class for paginating verses.

    Attributes:
        page_size (int): Default items per page.
        page_size_query_param (str): Query parameter name to set page size.
        page_query_param (str): Query parameter name for page number.
    """
    page_size: int = 10
    page_size_query_param: str = 'verse_page_size'
    page_query_param: str = 'verse_page'


class WordPagination(PageNumberPagination):
    """
    Pagination class for paginating words.

    Attributes:
        page_size (int): Default items per page.
        page_size_query_param (str): Query parameter name to set page size.
        page_query_param (str): Query parameter name for page number.
    """
    page_size: int = 10
    page_size_query_param: str = 'word_page_size'
    page_query_param: str = 'word_page'



from rest_framework.response import Response

class PagePagination(PageNumberPagination):
    page_size = 2

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })



class SearchPagination(PageNumberPagination):
    page_size = 8         
    page_size_query_param = 'page_size' 
    max_page_size = 50         
