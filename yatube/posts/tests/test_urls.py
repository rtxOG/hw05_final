from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse

from posts.models import Group, Post, User


class URLTests(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.author = User.objects.create_user(username='testauthor')
        self.group = Group.objects.create(
            title='TestGroup',
            slug='groupslug',
            description='Test',
        )
        self.post = Post.objects.create(
            group=URLTests.group,
            text="Testing",
            author=self.author,
        )
        self.user = User.objects.create_user(username='testuser')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """Проверка соответствия URL-адреса и соответствующего ему шаблона."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=[self.group.slug]):
                'posts/group_list.html',
            reverse('posts:profile', args=[self.user.username]):
                'posts/profile.html',
            reverse('posts:post_detail', args=[self.post.pk]):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', args=[self.post.pk]):
                'posts/create_post.html',
            'qwe123': 'core/404.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template(self):
        """Reverse возвращает ожидаемые пути."""
        url_names = {
            reverse('posts:index'): '/',
            reverse('posts:group_list', args=[self.group.slug]):
                '/group/groupslug/',
            reverse('posts:profile', args=[self.user.username]):
                '/profile/testuser/',
            reverse('posts:post_detail', args=[self.post.pk]):
                f'/posts/{self.post.pk}/',
            reverse('posts:post_create'): '/create/',
            reverse('posts:post_edit', args=[self.post.pk]):
                f'/posts/{self.post.pk}/edit/',
        }
        for reverse_url, correct_url in url_names.items():
            with self.subTest(url=reverse_url):
                self.assertEqual(reverse_url, correct_url)

    def test_urls_list(self):
        """
        Тестирование страниц, доступных не авторизованному пользователю
        """
        url_response_status_code = {
            '/': HTTPStatus.OK,
            '/group/groupslug/': HTTPStatus.OK,
            '/profile/testuser/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, status_code in url_response_status_code.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_user_urls(self):
        """
        Тестирование страниц, доступных авторизованному пользователю
        """
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_urls(self):
        """
        Тестирование страницы редактирования для автора поста
        """
        response = self.authorized_client_author.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_urls(self):
        """
        Тестирование перенаправления пользователей
        """
        response = self.guest_client.get(
            reverse('posts:post_create'), follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        response = self.guest_client.get(
            reverse('posts:add_comment', args=[self.post.pk]), follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.pk]), follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.pk}/')
