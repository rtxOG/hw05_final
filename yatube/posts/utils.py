from django.core.paginator import Paginator


ORDER_COUNT = 10


def pagination(request, posts, number_of_posts):
    paginator = Paginator(posts, number_of_posts)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
