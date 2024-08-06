from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.prefetch import GenericPrefetch
from django.db import connection
from django.db.models import Count
from django.test import TestCase

from .models import CharTag, Comment, Post, Tenant, User


class CompositePKGenericTests(TestCase):
    POST_1_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    @classmethod
    def setUpTestData(cls):
        cls.tenant_1 = Tenant.objects.create()
        cls.tenant_2 = Tenant.objects.create()
        cls.user_1 = User.objects.create(
            tenant=cls.tenant_1,
            id=1,
            email="user0001@example.com",
        )
        cls.user_2 = User.objects.create(
            tenant=cls.tenant_1,
            id=2,
            email="user0002@example.com",
        )
        cls.comment_1 = Comment.objects.create(id=1, user=cls.user_1)
        cls.comment_2 = Comment.objects.create(id=2, user=cls.user_1)
        cls.post_1 = Post.objects.create(tenant=cls.tenant_1, id=UUID(cls.POST_1_ID))
        cls.chartag_1 = CharTag.objects.create(name="a", content_object=cls.comment_1)
        cls.chartag_2 = CharTag.objects.create(name="b", content_object=cls.post_1)
        cls.comment_ct = ContentType.objects.get_for_model(Comment)
        cls.post_ct = ContentType.objects.get_for_model(Post)
        post_1_id = cls.POST_1_ID
        if not connection.features.has_native_uuid_field:
            post_1_id = cls.POST_1_ID.replace("-", "")
        cls.post_1_fk = f'[{cls.tenant_1.id}, "{post_1_id}"]'
        cls.comment_1_fk = f"[{cls.tenant_1.id}, {cls.comment_1.id}]"

    def test_fields(self):
        tag_1 = CharTag.objects.get(pk=self.chartag_1.pk)
        self.assertEqual(tag_1.content_type, self.comment_ct)
        self.assertEqual(tag_1.object_id, self.comment_1_fk)
        self.assertEqual(tag_1.content_object, self.comment_1)

        tag_2 = CharTag.objects.get(pk=self.chartag_2.pk)
        self.assertEqual(tag_2.content_type, self.post_ct)
        self.assertEqual(tag_2.object_id, self.post_1_fk)
        self.assertEqual(tag_2.content_object, self.post_1)

        post_1 = Post.objects.get(pk=self.post_1.pk)
        self.assertSequenceEqual(post_1.chartags.all(), (self.chartag_2,))

    def test_cascade_delete_if_generic_relation(self):
        Post.objects.get(pk=self.post_1.pk).delete()
        self.assertFalse(CharTag.objects.filter(pk=self.chartag_2.pk).exists())

    def test_no_cascade_delete_if_no_generic_relation(self):
        Comment.objects.get(pk=self.comment_1.pk).delete()
        tag_1 = CharTag.objects.get(pk=self.chartag_1.pk)
        self.assertIsNone(tag_1.content_object)

    def test_tags_clear(self):
        post_1 = Post.objects.get(pk=self.post_1.pk)
        post_1.chartags.clear()
        self.assertEqual(post_1.chartags.count(), 0)
        self.assertFalse(CharTag.objects.filter(pk=self.chartag_2.pk).exists())

    def test_tags_remove(self):
        post_1 = Post.objects.get(pk=self.post_1.pk)
        post_1.chartags.remove(self.chartag_2)
        self.assertEqual(post_1.chartags.count(), 0)
        self.assertFalse(CharTag.objects.filter(pk=self.chartag_2.pk).exists())

    def test_tags_create(self):
        tag_count = CharTag.objects.count()

        post_1 = Post.objects.get(pk=self.post_1.pk)
        post_1.chartags.create(name="c")
        self.assertEqual(post_1.chartags.count(), 2)
        self.assertEqual(CharTag.objects.count(), tag_count + 1)

        tag_3 = CharTag.objects.get(name="c")
        self.assertEqual(tag_3.content_type, self.post_ct)
        self.assertEqual(tag_3.object_id, self.post_1_fk)
        self.assertEqual(tag_3.content_object, post_1)

    def test_tags_add(self):
        tag_count = CharTag.objects.count()
        post_1 = Post.objects.get(pk=self.post_1.pk)

        tag_3 = CharTag(name="c")
        post_1.chartags.add(tag_3, bulk=False)
        self.assertEqual(post_1.chartags.count(), 2)
        self.assertEqual(CharTag.objects.count(), tag_count + 1)

        tag_3 = CharTag.objects.get(name="c")
        self.assertEqual(tag_3.content_type, self.post_ct)
        self.assertEqual(tag_3.object_id, self.post_1_fk)
        self.assertEqual(tag_3.content_object, post_1)

        tag_4 = CharTag.objects.create(name="d", content_object=self.comment_2)
        post_1.chartags.add(tag_4)
        self.assertEqual(post_1.chartags.count(), 3)
        self.assertEqual(CharTag.objects.count(), tag_count + 2)

        tag_4 = CharTag.objects.get(name="d")
        self.assertEqual(tag_4.content_type, self.post_ct)
        self.assertEqual(tag_4.object_id, self.post_1_fk)
        self.assertEqual(tag_4.content_object, post_1)

    def test_tags_set(self):
        tag_count = CharTag.objects.count()
        tag_1 = CharTag.objects.get(name="a")
        post_1 = Post.objects.get(pk=self.post_1.pk)
        post_1.chartags.set([tag_1])
        self.assertEqual(post_1.chartags.count(), 1)
        self.assertEqual(CharTag.objects.count(), tag_count - 1)
        self.assertFalse(CharTag.objects.filter(pk=self.chartag_2.pk).exists())

    def test_tags_get_or_create(self):
        post_1 = Post.objects.get(pk=self.post_1.pk)

        tag_2, created = post_1.chartags.get_or_create(name="b")
        self.assertFalse(created)
        self.assertEqual(tag_2.pk, self.chartag_2.pk)
        self.assertEqual(tag_2.content_type, self.post_ct)
        self.assertEqual(tag_2.object_id, self.post_1_fk)
        self.assertEqual(tag_2.content_object, post_1)

        tag_3, created = post_1.chartags.get_or_create(name="c")
        self.assertTrue(created)
        self.assertEqual(tag_3.content_type, self.post_ct)
        self.assertEqual(tag_3.object_id, self.post_1_fk)
        self.assertEqual(tag_3.content_object, post_1)

    def test_tags_update_or_create(self):
        post_1 = Post.objects.get(pk=self.post_1.pk)

        tag_2, created = post_1.chartags.update_or_create(
            name="b", defaults={"name": "b2"}
        )
        self.assertFalse(created)
        self.assertEqual(tag_2.pk, self.chartag_2.pk)
        self.assertEqual(tag_2.name, "b2")
        self.assertEqual(tag_2.content_type, self.post_ct)
        self.assertEqual(tag_2.object_id, self.post_1_fk)
        self.assertEqual(tag_2.content_object, post_1)

        tag_3, created = post_1.chartags.update_or_create(name="c")
        self.assertTrue(created)
        self.assertEqual(tag_3.content_type, self.post_ct)
        self.assertEqual(tag_3.object_id, self.post_1_fk)
        self.assertEqual(tag_3.content_object, post_1)

    def test_filter_by_related_query_name(self):
        self.assertSequenceEqual(
            CharTag.objects.filter(post__id=self.post_1.id), (self.chartag_2,)
        )

    def test_aggregate(self):
        self.assertEqual(
            Post.objects.aggregate(Count("chartags")), {"chartags__count": 1}
        )

    def test_generic_prefetch(self):
        chartag_1, chartag_2 = CharTag.objects.prefetch_related(
            GenericPrefetch(
                "content_object", [Post.objects.all(), Comment.objects.all()]
            )
        ).order_by("pk")

        self.assertEqual(chartag_1, self.chartag_1)
        self.assertEqual(chartag_2, self.chartag_2)

        with self.assertNumQueries(0):
            self.assertEqual(chartag_1.content_object, self.comment_1)
        with self.assertNumQueries(0):
            self.assertEqual(chartag_2.content_object, self.post_1)
