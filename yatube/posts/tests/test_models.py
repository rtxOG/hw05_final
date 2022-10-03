from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, составляющий больше 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        self.assertEqual(group.title, str(group))
        post = PostModelTest.post
        self.assertEqual(post.text[:15], str(post))

    def test_title_label(self):
        """verbose_name полей совпадает с ожидаемым."""
        post = PostModelTest.post
        verbose = post._meta.get_field('text').verbose_name
        self.assertEqual(verbose, 'Текст поста')
        verbose = post._meta.get_field('group').verbose_name
        self.assertEqual(verbose, 'Группа')

    def test_title_help_text(self):
        """help_text полей совпадает с ожидаемым."""
        post = PostModelTest.post
        help_text = post._meta.get_field('text').help_text
        self.assertEqual(help_text, 'Введите текст поста')
        help_text = post._meta.get_field('group').help_text
        self.assertEqual(help_text, 'Группа, к которой будет относиться пост')
