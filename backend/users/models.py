from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):

    email = models.EmailField(
        max_length=settings.MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name="Электронная почта",
    )
    first_name = models.CharField(
        max_length=settings.MAX_FIRST_NAME_LENGTH, verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=settings.MAX_LAST_NAME_LENGTH, verbose_name="Фамилия"
    )
    avatar = models.ImageField(
        upload_to="avatars/", blank=True, null=True, verbose_name="Аватар"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
        ]

    def __str__(self):
        return self.username


class Subscription(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following", verbose_name="Автор"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscription"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_subscription",
            ),
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["author"]),
        ]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
