from django.core.paginator import Paginator


ORDER_COUNT = 10


def pagination(DataSet, request):
    paginator = Paginator(DataSet, ORDER_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_obj': page_obj
    }
