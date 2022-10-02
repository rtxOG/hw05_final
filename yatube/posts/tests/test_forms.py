from django.test import TestCase, Client
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


import tempfile
import shutil


class TestCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.author = User.objects.create_user(username='testauthor1')
        cls.group = Group.objects.create(
            title='TestGroup1',
            slug='groupslug1',
            description='Group 1',
        )
        cls.post = Post.objects.create(
            text='Post from Group1',
            author=cls.author
        )
        cls.user = User.objects.create_user(username='testuser')
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_client_cant_create_post(self):
        """Неавторизованный пользователь не может создать пост"""
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Отправить текст',
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)

    def test_form_create(self):
        """Проверка создания нового поста"""
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Отправить текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post_latest = Post.objects.latest('id')
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                args=[self.user]
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(post_latest.text, form_data['text'])
        self.assertEqual(post_latest.group.id, form_data['group'])

    def test_form_update(self):
        """
        Проверка редактирования поста через форму на странице
        """
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        url = reverse('posts:post_edit', args=[1])
        self.authorized_client.get(url)
        group2 = Group.objects.create(
            title='TestGroup2',
            slug='groupslug2',
            description='Group 2',
        )
        form_data = {
            'group': group2.id,
            'text': 'Обновленный текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[1]), data=form_data, follow=True
        )
        post_testing = Post.objects.latest('id')
        self.assertEqual(post_testing.text, form_data['text'])
        self.assertEqual(post_testing.group.id, form_data['group'])
        self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': TestCreateForm.group.slug}
        ))
        self.assertEqual(
            Post.objects.select_related('group').filter(
                group=self.group).count(), 0)

    def test_user_client_cant_edit_post(self):
        """Авторизованный пользователь не может редактировать чужие посты"""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        form_data = {
            'text': 'Отправить текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[1]), data=form_data, follow=True
        )
        post_testing = Post.objects.latest('id')
        self.assertEqual(post_testing.text, self.post.text)

    def test_guest_client_cant_edit_post(self):
        """Неавторизованный пользователь не может редактировать чужие посты"""
        self.guest_client = Client()
        form_data = {
            'text': 'Отправить текст',
        }
        self.guest_client.post(
            reverse('posts:post_edit', args=[1]), data=form_data, follow=True
        )
        post_testing = Post.objects.latest('id')
        self.assertEqual(post_testing.text, self.post.text)

    def test_post_with_picture(self):
        """Проверка создания нового поста с картинкой"""
        count_posts = Post.objects.count()
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
        form_data = {
            'text': 'Пост с картинкой',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.latest('id')
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', args=[self.user]
        ))
        self.assertEqual(post_1.text, form_data['text'])
        self.assertEqual(post_1.author.username, 'testuser')
        self.assertEqual(post_1.group.title, 'TestGroup1')
