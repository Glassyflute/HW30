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
                    "id": category.id,
                    "name": category.name
                }
            )

        response = {
            "items": categories,
            "num_pages": paginator.num_pages,
            "total": paginator.count
        }

        return JsonResponse(response, safe=False)


class CategoryDetailView(DetailView):
    """
    Детальная информация по выбранной категории
    """
    model = Category

    def get(self, request, *args, **kwargs):
        category = self.get_object()

        return JsonResponse({
            "id": category.id,
            "name": category.name
        })


@method_decorator(csrf_exempt, name="dispatch")
class CategoryCreateView(CreateView):
    """
    Создание новой категории
    """
    model = Category
    fields = ["name"]

    def post(self, request, *args, **kwargs):
        category_data = json.loads(request.body)
        category_new = Category.objects.create(**category_data)
        # get_or_create? to check for already existing categories. if exists,
        # return with warning

        return JsonResponse({
            "id": category_new.id,
            "name": category_new.name
        })


@method_decorator(csrf_exempt, name="dispatch")
class CategoryUpdateView(UpdateView):
    """
    Обновление данных по категории
    """
    model = Category
    fields = ["name", "is_active"]

    def post(self, request, *args, **kwargs):
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
            "id": self.object.id,
            "name": self.object.name,
            "is_active": self.object.is_active
        })

        # category = Category.objects.create(
        #     name=category_data["name"],
        #     is_active=category_data["is_active"],
        # )

        # category = Category.objects.update_or_create(
        #     name=category_data["name"],
        #     is_active=category_data["is_active"]
        # )
        # may remove is_active -- table -set as default?
        # update_or_create(**category_data)?




@method_decorator(csrf_exempt, name="dispatch")
class CategoryDeleteView(DeleteView):
    """
    Удаление объявления
    """
    model = Category
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)

        return JsonResponse({"status": "ok"}, status=200)







class AdListView(ListView):
    """
    Список всех объявлений, с сортировкой по цене объявления по убыванию, с пагинатором и
    итоговой информацией
    """
    model = Ad

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        self.object_list = self.object_list.order_by("-name")

        paginator = Paginator(self.object_list, settings.TOTAL_ON_PAGE)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        ads = []
        for ad in page_obj:
            ads.append(
                {
                    "id": ad.id,
                    "name": ad.name,
                    "price": ad.price,
                    "description": ad.description,
                    "image": ad.image,
                    "is_published": ad.is_published,
                    "author_id": ad.author_id,
                    "location_name": ad.location_name,
                    "categories": list(map(str, ad.categories.all()))
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
            "id": ad.id,
            "name": ad.name,
            "price": ad.price,
            "description": ad.description,
            "image": ad.image,
            "is_published": ad.is_published,
            "author_id": ad.author_id,
            "location_name": ad.location_name,
            "categories": list(map(str, ad.categories.all()))
        })


@method_decorator(csrf_exempt, name="dispatch")
class AdCreateView(CreateView):
    """
    Создание нового объявления
    """
    model = Ad
    fields = ["name", "price", "description", "is_published", "author_id", "location_name", "categories"]
    # removed image from fields

    def post(self, request, *args, **kwargs):
        ad_data = json.loads(request.body)
        ad_new = Ad.objects.create(
            name=ad_data["name"],
            price=ad_data["price"],
            description=ad_data["description"],
            # image=ad_data["image"],
            is_published=ad_data["is_published"]
        )

        #remove image field here and upload via separate URL?

        location_data = Location.objects.create(name=ad_data["location_name"])
        # get_or_create?
        # ad_new.location_name = get_object_or_404(Location, name=ad_data["location_name"])

        ad_new.author_id = get_object_or_404(AdUser, pk=ad_data["author_id"])

        for category in ad_data["categories"]:
            category_obj, created = Category.objects.get_or_create(
                name=category,
                defaults={
                    "is_active": True
                }
            )
            ad_new.categories.add(category_obj)

        ad_new.save()

        return JsonResponse({
            "id": ad_new.id,
            "name": ad_new.name,
            "price": ad_new.price,
            "description": ad_new.description,
            # "image": ad_new.image,
            "is_published": ad_new.is_published,
            "author_id": ad_new.author_id,
            "location_name": location_data.name,
            "categories": list(map(str, ad_new.categories.all()))
        })


@method_decorator(csrf_exempt, name="dispatch")
class AdUpdateView(UpdateView):
    """
    Обновление данных по выбранному объявлению
    """
    model = Ad
    fields = ["name", "price", "description", "is_published", "author_id", "location_name", "categories"]

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        ad_data = json.loads(request.body)

        self.object.name = ad_data["name"]
        self.object.price = ad_data["price"]
        self.object.description = ad_data["description"]
        self.object.is_published = ad_data["is_published"]
        self.object.location_name = ad_data["location_name"]

        for category in ad_data["categories"]:
            category_obj, created = Category.objects.get_or_create(
                name=category,
                defaults={
                    "is_active": True
                }
            )
            self.object.categories.add(category_obj)

        self.object.author_id = get_object_or_404(AdUser, pk=ad_data["author_id"])
        # self.object.author_id = ad_data["author_id"]

        try:
            self.object.full_clean()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=422)

        self.object.save()

        # ad_upd = Ad.objects.create(
        #     name=ad_data["name"],
        #     price=ad_data["price"],
        #     description=ad_data["description"],
        #     is_published=ad_data["is_published"],
        #     location_name=ad_data["location_name"]
        # )

        return JsonResponse({
                    "id": self.object.id,
                    "name": self.object.name,
                    "price": self.object.price,
                    "description": self.object.description,
                    "is_published": self.object.is_published,
                    "author_id": self.object.author_id,
                    "location_name": self.object.location_name,
                    "categories": list(map(str, self.object.categories.all()))
                })


@method_decorator(csrf_exempt, name="dispatch")
class AdImageView(UpdateView):
    """
    Добавление/обновление картинки в объявлении
    """
    model = Ad
    fields = ["name", "image"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.image = request.FILES["image"]

        self.object.save()

        return JsonResponse({
                    "id": self.object.id,
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
        super().delete(request, *args, **kwargs)

        return JsonResponse({"status": "ok"}, status=200)






class AdUserListView(ListView):
    """
    Список пользователей, с сортировкой по username, с пагинатором и
    итоговой информацией
    """
    model = AdUser

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        self.object_list = self.object_list.order_by("username")

        paginator = Paginator(self.object_list, settings.TOTAL_ON_PAGE)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        ad_users = []
        for ad_user in page_obj:
            ad_users.append(
                {
                    "id": ad_user.id,
                    "first_name": ad_user.first_name,
                    "last_name": ad_user.last_name,
                    "username": ad_user.username,
                    "password": ad_user.password,
                    "role": ad_user.role,
                    "age": ad_user.age,
                    "location_name": ad_user.location_name
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
            "id": ad_user.id,
            "first_name": ad_user.first_name,
            "last_name": ad_user.last_name,
            "username": ad_user.username,
            "password": ad_user.password,
            "role": ad_user.role,
            "age": ad_user.age,
            "location_name": ad_user.location_name
        })


@method_decorator(csrf_exempt, name="dispatch")
class AdUserCreateView(CreateView):
    """
    Создание нового пользователя
    """
    model = AdUser
    fields = ["first_name", "last_name", "username", "password", "role", "age", "location_name"]

    def post(self, request, *args, **kwargs):
        ad_user_data = json.loads(request.body)
        ad_user_new = AdUser.objects.create(**ad_user_data)

        # location вводят текстом, после в виде ИД?

        return JsonResponse({
            "id": ad_user_new.id,
            "first_name": ad_user_new.first_name,
            "last_name": ad_user_new.last_name,
            "username": ad_user_new.username,
            "password": ad_user_new.password,
            "role": ad_user_new.role,
            "age": ad_user_new.age,
            "location_name": ad_user_new.location_name
        })


@method_decorator(csrf_exempt, name="dispatch")
class AdUserUpdateView(UpdateView):
    """
    Обновление данных по пользователю
    """
    model = AdUser
    fields = ["first_name", "last_name", "username", "password", "role", "age", "location_name"]

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        ad_user_data = json.loads(request.body)

        self.object.first_name = ad_user_data["first_name"]
        self.object.last_name = ad_user_data["last_name"]
        self.object.role = ad_user_data["role"]
        self.object.age = ad_user_data["age"]
        self.object.location_name = ad_user_data["location_name"]

        self.object.username = get_object_or_404(AdUser, username=ad_user_data["username"])
        if self.object.username:
            # exists????
            self.object.password = ad_user_data["password"]

        try:
            self.object.full_clean()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=422)

        self.object.save()

        # user_upd = AdUser.objects.create(
        #     first_name=ad_user_data["first_name"],
        #     last_name=ad_user_data["last_name"],
        #     role=ad_user_data["role"],
        #     age=ad_user_data["age"],
        #     location_name=ad_user_data["location_name"]
        # )
        # location вводят текстом, после в виде ИД?
        # # pk должен получить цифру
        # user_upd.username = get_object_or_404(AdUser, username=ad_user_data["username"])
        # #
        # print(user_upd.username)
        # if user_upd.username:
        #     # exists????
        #     user_upd.password = ad_user_data["password"]
        #     # update_or_create????

        return JsonResponse({
                    "id": self.object.id,
                    "first_name": self.object.first_name,
                    "last_name": self.object.last_name,
                    "username": self.object.username,
                    "password": self.object.password,
                    "role": self.object.role,
                    "age": self.object.age,
                    "location_name": self.object.location_name
                })


@method_decorator(csrf_exempt, name="dispatch")
class AdUserDeleteView(DeleteView):
    """
    Удаление пользователя
    """
    model = AdUser
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)

        return JsonResponse({"status": "ok"}, status=200)



### select_relation ???? select_related(”user”) - foreign key