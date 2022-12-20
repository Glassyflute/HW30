import json

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, UpdateView, ListView, CreateView, DeleteView

from ads.models import Category, Ad, AdUser, Location
from avito import settings


def root(request):
    return JsonResponse({
        "status": "ok"
    })


class CategoryListView(ListView):
    """
    Список категорий, с сортировкой по названию категории, с пагинатором и
    итоговой информацией
    """
    model = Category

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        self.object_list = self.object_list.order_by("name")

        paginator = Paginator(self.object_list, settings.TOTAL_ON_PAGE)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        categories = []
        for category in page_obj:
            categories.append(
                {
                    "id": category.pk,
                    "name": category.name
                }
            )

        response = {
            "items": categories,
            "num_pages": paginator.num_pages,
            "total": paginator.count
        }

        return JsonResponse(response, safe=False)
# id or pk?

class CategoryDetailView(DetailView):
    """
    Детальная информация по выбранной категории
    """
    model = Category

    def get(self, request, *args, **kwargs):
        category = self.get_object()

        return JsonResponse({
            "id": category.pk,
            "name": category.name
        })


@method_decorator(csrf_exempt, name="dispatch")
class CategoryCreateView(CreateView):
    """
    Создание новой категории
    """
    model = Category
    # fields здесь и далее не критичен, т.к. не используем templates.
    fields = "__all__"

    def post(self, request, *args, **kwargs):
        category_data = json.loads(request.body)
        category_new = Category.objects.create(**category_data)

        return JsonResponse({
            "id": category_new.pk,
            "name": category_new.name
        })


@method_decorator(csrf_exempt, name="dispatch")
class CategoryUpdateView(UpdateView):
    """
    Обновление данных по категории
    """
    model = Category
    fields = "__all__"

    def patch(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        category_data = json.loads(request.body)

        self.object.name = category_data["name"]
        self.object.is_active = category_data["is_active"]

        try:
            self.object.full_clean()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=422)

        self.object.save()

        return JsonResponse({
            "id": self.object.pk,
            "name": self.object.name,
            "is_active": self.object.is_active
        })


@method_decorator(csrf_exempt, name="dispatch")
class CategoryDeleteView(DeleteView):
    """
    Удаление объявления
    """
    model = Category
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        categ = self.get_object()
        categ_pk = categ.pk
        super().delete(request, *args, **kwargs)
        return JsonResponse({"id deleted": categ_pk}, status=200)







class AdListView(ListView):
    """
    Список всех объявлений, с сортировкой по цене объявления по убыванию, с пагинатором и
    итоговой информацией
    """
    model = Ad

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        self.object_list = self.object_list.select_related("author").order_by("-price")

        paginator = Paginator(self.object_list, settings.TOTAL_ON_PAGE)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        ads = []
        for ad in page_obj:
            ads.append(
                {
                    "id": ad.pk,
                    "name": ad.name,
                    "price": ad.price,
                    "description": ad.description,
                    "image": ad.image.url if ad.image else None,
                    "is_published": ad.is_published,
                    "author": ad.author.username,
                    "category": ad.category.name,
                    # "location_names": ad.author.location_names.name
                    "location_names": list(map(str, ad.author.location_names.all()))
                }
            )

        response = {
            "items": ads,
            "num_pages": paginator.num_pages,
            "total": paginator.count
        }

        return JsonResponse(response, safe=False)


class AdDetailView(DetailView):
    """
    Детальная информация по выбранному объявлению
    """
    model = Ad

    def get(self, request, *args, **kwargs):
        ad = self.get_object()

        return JsonResponse({
            "id": ad.pk,
            "name": ad.name,
            "price": ad.price,
            "description": ad.description,
            "image": ad.image.url if ad.image else None,
            "is_published": ad.is_published,
            "author": ad.author.username,
            "category": ad.category.name,
            # "location_names": ad.author.location_names.name
            "location_names": list(map(str, ad.author.location_names.all()))
            # "location_names": [location_name for location_name in ad.author.location_names.all()]
        })

# ad.author.username
# ad.author.location_names
# ad.author.location_names.name
# [location_name.name for location_name in ad.author.location_names.all()]
# location names is null everywhere

@method_decorator(csrf_exempt, name="dispatch")
class AdCreateView(CreateView):
    """
    Создание нового объявления
    """
    model = Ad
    fields = "__all__"

    def post(self, request, *args, **kwargs):
        ad_data = json.loads(request.body)

        # проверка на существование пользователя
        author = get_object_or_404(AdUser, username=ad_data["author"])
        category = get_object_or_404(Category, pk=ad_data["category"])

        ad_new = Ad.objects.create(
            name=ad_data.get("name"),
            price=ad_data.get("price"),
            description=ad_data.get("description"),
            is_published=ad_data.get("is_published"),
            author=author
        )

        # возможность добавлять новый адрес при необходимости
        locations = ad_data.get("location_names")
        for location in locations:
            location_obj, _ = Location.objects.get_or_create(name=location)
        ad_new.location_names.add(location_obj)
        locations_all_qs = ad_new.location_names.all()

        # возможность добавить новую категорию при необходимости (неактивные категории потенциально можно
        # использовать для фильтрации)
        for category in ad_data["category"]:
            category_obj, created = Category.objects.get_or_create(
                name=category,
                defaults={
                    "is_active": True
                }
            )
            ad_new.category.add(category_obj)

        image_data = ad_data["image"]

        ad_new.save()

        return JsonResponse({
            "id": ad_new.pk,
            "name": ad_new.name,
            "price": ad_new.price,
            "description": ad_new.description,
            "image": image_data.url if image_data else None,
            "is_published": ad_new.is_published,
            "author": ad_new.author.username,
            "category": ad_new.category.name,
            # "location_names": location_data.name if location_data else None
            "location_names": [location_elem.name for location_elem in locations_all_qs]
        })


@method_decorator(csrf_exempt, name="dispatch")
class AdUpdateView(UpdateView):
    """
    Обновление данных по выбранному объявлению
    """
    model = Ad
    fields = "__all__"

    def patch(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        ad_data = json.loads(request.body)

        # проверка на существование пользователя
        author = get_object_or_404(AdUser, username=ad_data["author"])

        ad_new = Ad.objects.create(
            name=ad_data.get("name"),
            price=ad_data.get("price"),
            description=ad_data.get("description"),
            is_published=ad_data.get("is_published"),
            author=author
        )

        # возможность добавлять новый адрес при необходимости
        locations = ad_data.get("location_names")
        for location in locations:
            location_obj, _ = Location.objects.get_or_create(name=location)
        ad_new.location_names.add(location_obj)
        locations_all_qs = ad_new.location_names.all()

        # возможность добавить новую категорию при необходимости (неактивные категории потенциально можно
        # использовать для фильтрации)
        for category in ad_data["category"]:
            category_obj, created = Category.objects.get_or_create(
                name=category,
                defaults={
                    "is_active": True
                }
            )
            ad_new.category.add(category_obj)


        # if "name" in ad_data:
        #     self.object.name = ad_data["name"]
        # if "price" in ad_data:
        #     self.object.price = ad_data["price"]
        # if "description" in ad_data:
        #     self.object.description = ad_data["description"]
        # if "is_published" in ad_data:
        #     self.object.is_published = ad_data["is_published"]
        # if "location_names" in ad_data:
        #     location_data = Location.objects.create(name=ad_data["location_names"])
        #
        # for category in ad_data["category"]:
        #     category_obj, created = Category.objects.get_or_create(
        #         name=category,
        #         defaults={
        #             "is_active": True
        #         }
        #     )
        #     self.object.category.add(category_obj)

        # self.object.author_id = get_object_or_404(AdUser, pk=ad_data["author_id"])
        # self.object.author_id = ad_data["author_id"]

        try:
            self.object.full_clean()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=422)

        self.object.save()

        return JsonResponse({
                    "id": self.object.pk,
                    "name": self.object.name,
                    "price": self.object.price,
                    "description": self.object.description,
                    "is_published": self.object.is_published,
                    "author": self.object.author.name,
                    "category": self.object.category.name,
                    "location_names": [location_elem.name for location_elem in locations_all_qs]
                })


@method_decorator(csrf_exempt, name="dispatch")
class AdImageView(UpdateView):
    """
    Добавление/обновление картинки в объявлении
    """
    model = Ad
    fields = "__all__"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.image = request.FILES.get("image")
        self.object.save()

        return JsonResponse({
                    "id": self.object.pk,
                    "name": self.object.name,
                    "image": self.object.image.url if self.object.image else None
                })


@method_decorator(csrf_exempt, name="dispatch")
class AdDeleteView(DeleteView):
    """
    Удаление объявления
    """
    model = Ad
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        ad_ = self.get_object()
        ad_pk = ad_.pk
        super().delete(request, *args, **kwargs)
        return JsonResponse({"id deleted": ad_pk}, status=200)






class AdUserListView(ListView):
    """
    Список пользователей, с сортировкой по username, с пагинатором и
    итоговой информацией
    """
    model = AdUser

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        # self.object_list = self.object_list.order_by("username")
        self.object_list = self.object_list.select_related("ad").filter(is_published=True).count().order_by("username")
        # total_ads_by_user = AdUser.objects.select_related("ad").filter(is_published=True).count()
        # "total_ads": ad_user.ad_set.filter(is_published=True).count()
        # ad_set == обратное обращение к таблице ad из aduser

        paginator = Paginator(self.object_list, settings.TOTAL_ON_PAGE)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        ad_users = []
        for ad_user in page_obj:
            ad_users.append(
                {
                    "id": ad_user.pk,
                    "first_name": ad_user.first_name,
                    "last_name": ad_user.last_name,
                    "username": ad_user.username,
                    "role": ad_user.role,
                    "age": ad_user.age,
                    # "total_ads": ad_user.ad_set.filter(is_published=True).count()
                    "total_ads_by_user": total_ads_by_user,
                    "location_names": list(map(str, ad_user.location_names.all()))
                }
            )

        # добавить сумму опубликованных объявл total_ads по каждому пользователю publ-true == annotate?
        response = {
            "items": ad_users,
            "num_pages": paginator.num_pages,
            "total": paginator.count
        }

        return JsonResponse(response, safe=False)


class AdUserDetailView(DetailView):
    """
    Детальная информация по выбранному пользователю
    """
    model = AdUser

    def get(self, request, *args, **kwargs):
        ad_user = self.get_object()

        return JsonResponse({
            "id": ad_user.pk,
            "first_name": ad_user.first_name,
            "last_name": ad_user.last_name,
            "username": ad_user.username,
            "role": ad_user.role,
            "age": ad_user.age,
            # "location_names": ad_user.location_names
            "location_names": list(map(str, ad_user.location_names.all()))
        })


@method_decorator(csrf_exempt, name="dispatch")
class AdUserCreateView(CreateView):
    """
    Создание нового пользователя
    """
    model = AdUser
    fields = "__all__"

    def post(self, request, *args, **kwargs):
        ad_user_data = json.loads(request.body)

        ad_user_new = AdUser.objects.create(
            first_name=ad_user_data.get("first_name"),
            last_name=ad_user_data.get("last_name"),
            username=ad_user_data.get("username"),
            password=ad_user_data.get("password"),
            role=ad_user_data.get("role"),
            age=ad_user_data.get("age")
        )

        # # location вводят текстом, после в виде ИД?
        locations = ad_user_data.get("location_names")
        for location in locations:
            location_obj, _ = Location.objects.get_or_create(name=location)

        ad_user_new.location_names.add(location_obj)
        locations_all_qs = ad_user_new.location_names.all()
        #
        # ad_user_new.save()

        # self.object.author_id = get_object_or_404(AdUser, pk=ad_data["author_id"])
        # # self.object.author_id = ad_data["author_id"]
        #
        # try:
        #     self.object.full_clean()
        # except ValidationError as e:
        #     return JsonResponse(e.message_dict, status=422)
        #
        # self.object.save()

        return JsonResponse({
            "id": ad_user_new.pk,
            "first_name": ad_user_new.first_name,
            "last_name": ad_user_new.last_name,
            "username": ad_user_new.username,
            "password": ad_user_new.password,
            "role": ad_user_new.role,
            "age": ad_user_new.age,
            # "location_names": [location_elem.name for location_elem in ad_user_new.location_names.all()]
            "location_names": [location_elem.name for location_elem in locations_all_qs]
        })
# [location.name for location in locations_all_qs]

@method_decorator(csrf_exempt, name="dispatch")
class AdUserUpdateView(UpdateView):
    """
    Обновление данных по пользователю
    """
    model = AdUser
    fields = "__all__"

    def patch(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        ad_user_data = json.loads(request.body)

        if "first_name" in ad_user_data:
            self.object.first_name = ad_user_data["first_name"]
        if "last_name" in ad_user_data:
            self.object.last_name = ad_user_data["last_name"]
        if "role" in ad_user_data:
            self.object.role = ad_user_data["role"]
        if "age" in ad_user_data:
            self.object.age = ad_user_data["age"]

        locations = ad_user_data.get("location_names")
        for location in locations:
            location_obj, _ = Location.objects.get_or_create(name=location)
        self.object.location_names.add(location_obj)
        locations_all_qs = self.object.location_names.all()

        self.object.username = get_object_or_404(AdUser, username=ad_user_data["username"])
        if self.object.username:
            # exists????
            self.object.password = ad_user_data["password"]

        try:
            self.object.full_clean()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=422)

        self.object.save()

        return JsonResponse({
                    "id": self.object.pk,
                    "first_name": self.object.first_name,
                    "last_name": self.object.last_name,
                    "username": self.object.username,
                    "password": self.object.password,
                    "role": self.object.role,
                    "age": self.object.age,
                    # "location_names": [location_elem.name for location_elem in self.object.location_names.all()]
                    "location_names": [location_elem.name for location_elem in locations_all_qs]
                })


@method_decorator(csrf_exempt, name="dispatch")
class AdUserDeleteView(DeleteView):
    """
    Удаление пользователя
    """
    model = AdUser
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        user_ = self.get_object()
        user_pk = user_.pk
        super().delete(request, *args, **kwargs)
        return JsonResponse({"id deleted": user_pk}, status=200)



### select_relation ???? select_related(”user”) - foreign key