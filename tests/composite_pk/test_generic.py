from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from .models import Comment, TaggedItem, Tenant, User


class CompositePKGenericTests(TestCase):
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
        cls.tag_1 = TaggedItem.objects.create(tag="a", content_object=cls.comment_1)

    def test_fields(self):
        obj = TaggedItem.objects.get(id=self.tag_1.id)
        comment_ct = ContentType.objects.get_for_model(Comment)
        self.assertEqual(obj.content_type, comment_ct)
        self.assertEqual(obj.object_id, f"[{self.tenant_1.id}, {self.comment_1.id}]")
        self.assertEqual(obj.content_object, self.comment_1)

    def
