from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=200, null=True)
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True)

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"

    def __str__(self):
        return self.name


class AdUser(models.Model):
    ROLES = [
        ("member", "Участник"),
        ("moderator", "Модератор"),
        ("admin", "Админ")
    ]

    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20, null=True)
    username = models.SlugField(max_length=30, unique=True)
    password = models.SlugField(max_length=30)
    role = models.CharField(max_length=15, choices=ROLES, default="member")
    age = models.PositiveSmallIntegerField()
    location_names = models.ManyToManyField(Location)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Ad(models.Model):
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField()
    description = models.TextField(max_length=1000, null=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    is_published = models.BooleanField(default=False)
    author = models.ForeignKey(AdUser, related_name="ads", on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"

    def __str__(self):
        return self.name

