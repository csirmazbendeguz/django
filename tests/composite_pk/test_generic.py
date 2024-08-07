from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from .models import Comment, Post, Tag, Tenant, User


class CompositePKGenericTests(TestCase):
    POST_1_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    @classmethod
    def setUpTestData(cls):
        cls.tenant_1 = Tenant.objects.create()
        cls.tenant_2 = Tenant.objects.create()
        cls.tenant_3 = Tenant.objects.create()
        cls.user_1 = User.objects.create(tenant=cls.tenant_1, id=1)
        cls.user_2 = User.objects.create(tenant=cls.tenant_1, id=2)
        cls.user_3 = User.objects.create(tenant=cls.tenant_2, id=3)
        cls.user_4 = User.objects.create(tenant=cls.tenant_3, id=4)
        cls.comment_1 = Comment.objects.create(id=1, user=cls.user_1)
        cls.comment_2 = Comment.objects.create(id=2, user=cls.user_1)
        cls.comment_3 = Comment.objects.create(id=3, user=cls.user_2)
        cls.comment_4 = Comment.objects.create(id=4, user=cls.user_3)
        cls.comment_5 = Comment.objects.create(id=5, user=cls.user_1)
        cls.post_1 = Post.objects.create(tenant=cls.tenant_1, id=UUID(cls.POST_1_ID))
        cls.tag_1 = Tag.objects.create(name="a", content_object=cls.comment_1)
        cls.tag_2 = Tag.objects.create(name="b", content_object=cls.post_1)
        cls.comment_ct = ContentType.objects.get_for_model(Comment)
        cls.post_ct = ContentType.objects.get_for_model(Post)

    def test_fields(self):
        tag_1 = Tag.objects.get(pk=self.tag_1.pk)
        self.assertEqual(tag_1.content_type, self.comment_ct)
        self.assertEqual(tag_1.object_id, f"[{self.tenant_1.id}, {self.comment_1.id}]")
        self.assertEqual(tag_1.content_object, self.comment_1)

        tag_2 = Tag.objects.get(pk=self.tag_2.pk)
        self.assertEqual(tag_2.content_type, self.post_ct)
        self.assertEqual(tag_2.object_id, f'[{self.tenant_1.id}, "{self.POST_1_ID}"]')
        self.assertEqual(tag_2.content_object, self.post_1)

        post_1 = Post.objects.get(pk=self.post_1.pk)
        self.assertSequenceEqual(post_1.tags.all(), (self.tag_2,))

    def test_cascade_delete_if_generic_relation(self):
        Post.objects.get(pk=self.post_1.pk).delete()
        self.assertFalse(Tag.objects.filter(pk=self.tag_2.pk).exists())

    def test_no_cascade_delete_if_no_generic_relation(self):
        Comment.objects.get(pk=self.comment_1.pk).delete()
        tag_1 = Tag.objects.get(pk=self.tag_1.pk)
        self.assertIsNone(tag_1.content_object)

    def test_tags_clear(self):
        post_1 = Post.objects.get(pk=self.post_1.pk)
        post_1.tags.clear()
        self.assertEqual(post_1.tags.count(), 0)
        self.assertFalse(Tag.objects.filter(pk=self.tag_2.pk).exists())

    def test_tags_remove(self):
        post_1 = Post.objects.get(pk=self.post_1.pk)
        post_1.tags.remove(self.tag_2)
        self.assertEqual(post_1.tags.count(), 0)
        self.assertFalse(Tag.objects.filter(pk=self.tag_2.pk).exists())

    def test_tags_create(self):
        tag_count = Tag.objects.count()

        post_1 = Post.objects.get(pk=self.post_1.pk)
        post_1.tags.create(name="c")
        self.assertEqual(post_1.tags.count(), 2)
        self.assertEqual(Tag.objects.count(), tag_count + 1)

        tag_3 = Tag.objects.get(name="c")
        self.assertEqual(tag_3.content_type, self.post_ct)
        self.assertEqual(tag_3.object_id, f'[{self.tenant_1.id}, "{self.POST_1_ID}"]')
        self.assertEqual(tag_3.content_object, post_1)
