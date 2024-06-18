from django.db.models import Count
from django.test import TestCase

from .models import Comment, Tenant, User


class CompositePKGetTests(TestCase):
    """
    Test the .get(), .get_or_create() methods of composite_pk models.
    """

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.tenant_1 = Tenant.objects.create()
        cls.tenant_2 = Tenant.objects.create()
        cls.user_1 = User.objects.create(tenant=cls.tenant_1, id=1)
        cls.user_2 = User.objects.create(tenant=cls.tenant_1, id=2)
        cls.user_3 = User.objects.create(tenant=cls.tenant_2, id=3)
        cls.comment_1 = Comment.objects.create(id=1, user=cls.user_1)

    def test_get_user(self):
        test_cases = (
            {"pk": self.user_1.pk},
            {"pk": (self.tenant_1.id, self.user_1.id)},
            {"id": self.user_1.id},
        )

        for lookup in test_cases:
            with self.subTest(lookup=lookup):
                self.assertEqual(User.objects.get(**lookup), self.user_1)

    def test_get_comment(self):
        test_cases = (
            {"pk": self.comment_1.pk},
            {"pk": (self.tenant_1.id, self.comment_1.id)},
            {"id": self.comment_1.id},
            {"user": self.user_1},
            {"user_id": self.user_1.id},
            {"user__id": self.user_1.id},
            {"user__pk": self.user_1.pk},
            {"tenant": self.tenant_1},
            {"tenant_id": self.tenant_1.id},
            {"tenant__id": self.tenant_1.id},
            {"tenant__pk": self.tenant_1.pk},
        )

        for lookup in test_cases:
            with self.subTest(lookup=lookup):
                self.assertEqual(Comment.objects.get(**lookup), self.comment_1)

    def test_get_or_create_user(self):
        test_cases = (
            {
                "pk": self.user_1.pk,
                "defaults": {"email": "user9201@example.com"},
            },
            {
                "pk": (self.tenant_1.id, self.user_1.id),
                "defaults": {"email": "user9201@example.com"},
            },
            {
                "tenant": self.tenant_1,
                "id": self.user_1.id,
                "defaults": {"email": "user3512@example.com"},
            },
            {
                "tenant_id": self.tenant_1.id,
                "id": self.user_1.id,
                "defaults": {"email": "user8239@example.com"},
            },
            {
                "primary_key": self.user_1.pk,
                "defaults": {"email": "user5332@example.com"},
            },
        )

        for fields in test_cases:
            with self.subTest(fields=fields):
                count = User.objects.count()
                user, created = User.objects.get_or_create(**fields)
                self.assertFalse(created)
                self.assertEqual(user.id, self.user_1.id)
                self.assertEqual(user.pk, (self.tenant_1.id, self.user_1.id))
                self.assertEqual(user.primary_key, user.pk)
                self.assertEqual(user.tenant_id, self.tenant_1.id)
                self.assertEqual(user.email, self.user_1.email)
                self.assertEqual(count, User.objects.count())

    def test_lookup_errors(self):
        m_tuple = "'%s' lookup of 'primary_key' field must be a tuple or a list"
        m_2_elements = "'%s' lookup of 'primary_key' field must have 2 elements"
        m_tuple_collection = (
            "'in' lookup of 'primary_key' field must be a collection of tuples or lists"
        )
        m_2_elements_each = (
            "'in' lookup of 'primary_key' field must have 2 elements each"
        )
        test_cases = (
            ({"pk": 1}, m_tuple % "exact"),
            ({"pk": (1, 2, 3)}, m_2_elements % "exact"),
            ({"pk__exact": 1}, m_tuple % "exact"),
            ({"pk__exact": (1, 2, 3)}, m_2_elements % "exact"),
            ({"pk__in": 1}, m_tuple % "in"),
            ({"pk__in": (1, 2, 3)}, m_tuple_collection),
            ({"pk__in": ((1, 2, 3),)}, m_2_elements_each),
            ({"pk__gt": 1}, m_tuple % "gt"),
            ({"pk__gt": (1, 2, 3)}, m_2_elements % "gt"),
            ({"pk__gte": 1}, m_tuple % "gte"),
            ({"pk__gte": (1, 2, 3)}, m_2_elements % "gte"),
            ({"pk__lt": 1}, m_tuple % "lt"),
            ({"pk__lt": (1, 2, 3)}, m_2_elements % "lt"),
            ({"pk__lte": 1}, m_tuple % "lte"),
            ({"pk__lte": (1, 2, 3)}, m_2_elements % "lte"),
            ({"primary_key": 1}, m_tuple % "exact"),
            ({"primary_key": (1, 2, 3)}, m_2_elements % "exact"),
            ({"primary_key__exact": 1}, m_tuple % "exact"),
            ({"primary_key__exact": (1, 2, 3)}, m_2_elements % "exact"),
            ({"primary_key__in": 1}, m_tuple % "in"),
            ({"primary_key__in": (1, 2, 3)}, m_tuple_collection),
            ({"primary_key__in": ((1, 2, 3),)}, m_2_elements_each),
            ({"primary_key__gt": 1}, m_tuple % "gt"),
            ({"primary_key__gt": (1, 2, 3)}, m_2_elements % "gt"),
            ({"primary_key__gte": 1}, m_tuple % "gte"),
            ({"primary_key__gte": (1, 2, 3)}, m_2_elements % "gte"),
            ({"primary_key__lt": 1}, m_tuple % "lt"),
            ({"primary_key__lt": (1, 2, 3)}, m_2_elements % "lt"),
            ({"primary_key__lte": 1}, m_tuple % "lte"),
            ({"primary_key__lte": (1, 2, 3)}, m_2_elements % "lte"),
        )

        for kwargs, message in test_cases:
            with (
                self.subTest(kwargs=kwargs),
                self.assertRaisesMessage(ValueError, message),
            ):
                Comment.objects.get(**kwargs)

    def test_get_user_by_comments(self):
        self.assertEqual(User.objects.get(comments=self.comment_1), self.user_1)

    def test_get_user_annotated_with_comments_id_count(self):
        users = User.objects.annotate(comments_count=Count("comments__id"))
        test_cases = (
            (self.user_1.id, 1),
            (self.user_2.id, 0),
            (self.user_3.id, 0),
        )

        for user_id, count in test_cases:
            with self.subTest(user_id=user_id):
                user = users.get(id=user_id)
                self.assertEqual(user.comments_count, count)
