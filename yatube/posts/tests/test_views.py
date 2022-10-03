from django import forms
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.core.paginator import Page

from posts.models import Group, Post, Comment, Follow, User

import tempfile
import shutil

POSTS_ON_FIRST_PAGE = 10
POSTS_ON_SECOND_PAGE = 3


class ViewTests(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.author = User.objects.create_user(username='testauthor1')
        self.post = Post.objects.create(
            group=Group.objects.create(
                title='TestGroup1',
                slug='groupslug1',
                description='Group 1',
            ),
            text='Post from Group1',
            author=self.author,
            image=uploaded
        )
        self.author2 = User.objects.create_user(username='testauthor2')
        self.post2 = Post.objects.create(
            group=Group.objects.create(
                title='TestGroup2',
                slug='groupslug2',
                description='Group 2',
            ),
            text='Post from Group2',
            author=self.author
        )
        self.user = User.objects.create_user(username='testuser')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""

        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'groupslug1'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'testauthor1'}):
                'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': ViewTests.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': ViewTests.post.pk}):
                'posts/create_post.html',
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertTrue(len(response.context['page_obj']) > 0)
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(
            first_object.author.username, self.post.author.username
        )
        self.assertEqual(first_object.group.title, self.post.group.title)
        self.assertEqual(first_object.image, 'posts/small.gif')

    def test_group_list_show_correct_context(self):
        """Шаблон группы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'groupslug1'}
        ))
        self.assertIn('group', response.context)
        self.assertIsInstance(response.context['group'], Group)
        first_object = response.context['group']
        self.assertEqual(first_object.title, self.post.group.title)
        self.assertEqual(first_object.slug, self.post.group.slug)

    def test_profile_show_correct_context(self):
        """Шаблон профиля сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'testauthor1'}
        ))
        self.assertIn('page_obj', response.context)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertTrue(len(response.context['page_obj']) > 0)
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.image, 'posts/small.gif')
        self.assertEqual(
            response.context['author'].username, self.post.author.username
        )
        self.assertEqual(first_object.text, self.post.text)

    def test_post_not_in_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'groupslug1'}
        ))
        self.assertIn('page_obj', response.context)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertTrue(len(response.context['page_obj']) > 0)
        first_object = response.context['page_obj'][0]
        self.assertTrue(first_object.text, 'Post from Group2')

    def test_post_create_show_correct_context(self):
        """Шаблон создания поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон страницы поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': ViewTests.post.pk}
        ))
        self.assertIn('post', response.context)
        self.assertIsInstance(response.context['post'], Post)
        first_object = response.context['post']
        self.assertEqual(first_object.image, 'posts/small.gif')
        self.assertEqual(first_object.pk, ViewTests.post.pk)

    def test_post_edit_show_correct_context(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': ViewTests.post.pk}
        ))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_add_comment_login_user(self):
        """Проверка успешной отправки комментария"""
        comments_count = Comment.objects.count()
        comment = Comment.objects.create(
            text='TestComm',
            author=self.user,
            post=self.post
        )
        form_data = {
            'text': 'PostText',
            'group': 'groupslug1',
            'comments': comment
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': ViewTests.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(Comment.objects.last(), comment)

    def test_cache_in_index_page(self):
        """Проверяем работу кэша на главной странице"""
        first_state = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.first()
        post_1.text = 'Измененный текст'
        post_1.save()
        second_state = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_state.content, third_state.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug2',
            description='Тестовое описание')
        cls.posts = []
        for i in range(POSTS_ON_FIRST_PAGE + POSTS_ON_SECOND_PAGE):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        cls.user = User.objects.create_user(username='mob2556')
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_posts(self):
        list_urls = {
            reverse('posts:index'): 'index',
            reverse(
                'posts:group_list', kwargs={'slug': 'test_slug2'}
            ): 'group',
            reverse(
                'posts:profile', kwargs={'username': 'test_name'}
            ): 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(
                response.context.get('page_obj').object_list),
                POSTS_ON_FIRST_PAGE)

    def test_second_page_contains_three_posts(self):
        list_urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse(
                'posts:group_list', kwargs={'slug': 'test_slug2'}
            ) + '?page=2': 'group',
            reverse(
                'posts:profile', kwargs={'username': 'test_name'}
            ) + '?page=2': 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(
                response.context.get('page_obj').object_list),
                POSTS_ON_SECOND_PAGE)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}
        ))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}
        ))
        self.client_auth_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_following.username}
        ))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context["page_obj"][0].text
        self.assertEqual(post_text_0, 'Тестовая запись для тестирования ленты')
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response,
                               'Тестовая запись для тестирования ленты')
