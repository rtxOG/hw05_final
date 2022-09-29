from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


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

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.user = User.objects.create_user(username='testuser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """Проверка соответствия URL-адреса и соответствующего ему шаблона."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/groupslug/': 'posts/group_list.html',
            '/profile/testuser/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            'qwe123': 'core/404.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)

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
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/comment/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )
