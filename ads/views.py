import json

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Max, Min, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, UpdateView, ListView, CreateView, DeleteView
from rest_framework.generics import RetrieveAPIView, ListAPIView, DestroyAPIView, CreateAPIView, UpdateAPIView

from ads.models import Category, Ad, AdUser, Location
from ads.serializers import AdUserDetailSerializer, AdUserListSerializer, AdUserDestroySerializer, \
    AdUserCreateSerializer, AdUserUpdateSerializer
from avito import settings


def root(request):
    return JsonResponse({
        "status": "ok"
    })


# Category
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


# Ad
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
            "location_names": list(map(str, ad.author.location_names.all()))
        })


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
        # создание объявления по username пользователю и id категории
        author = get_object_or_404(AdUser, username=ad_data["author"])

        category = get_object_or_404(Category, pk=ad_data["category"])

        ad_new = Ad.objects.create(
            name=ad_data.get("name"),
            price=ad_data.get("price"),
            description=ad_data.get("description"),
            is_published=ad_data.get("is_published", False),
            author=author,
            category=category
        )

        locations_all_qs = ad_new.author.location_names.all()

        return JsonResponse({
            "id": ad_new.pk,
            "name": ad_new.name,
            "price": ad_new.price,
            "description": ad_new.description,
            "image": ad_new.image.url if ad_new.image else None,
            "is_published": ad_new.is_published,
            "author": ad_new.author.username,
            "category": ad_new.category.name,
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

        if "name" in ad_data:
            self.object.name = ad_data["name"]
        if "price" in ad_data:
            self.object.price = ad_data["price"]
        if "description" in ad_data:
            self.object.description = ad_data["description"]
        if "is_published" in ad_data:
            self.object.is_published = ad_data["is_published"]

        if "category" in ad_data:
            self.object.category.pk = ad_data["category"]
        if "author" in ad_data:
            self.object.author.pk = ad_data["author"]

        # проверка на существование пользователя
        # обновление данных по пользователю и категории через id
        author = get_object_or_404(AdUser, pk=ad_data["author"])
        category = get_object_or_404(Category, pk=ad_data["category"])

        locations_all_qs = self.object.author.location_names.all()

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
                    "image": self.object.image.url if self.object.image else None,
                    "is_published": self.object.is_published,
                    "author": self.object.author.username,
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


# User


# class AdUserListView(ListView):
#     """
#     Список пользователей, с сортировкой по username, с пагинатором и
#     итоговой информацией
#     """
#     model = AdUser
#
#     def get(self, request, *args, **kwargs):
#         super().get(request, *args, **kwargs)
#
#         self.object_list = self.object_list.order_by("username")
#
#
#
#         # paginator = Paginator(self.object_list, settings.TOTAL_ON_PAGE)
#         # page_number = request.GET.get("page")
#         # page_obj = paginator.get_page(page_number)
#
#         ad_users = []
#         # добавлена сумма опубликованных объявлений total_ads по каждому пользователю
#         for ad_user in page_obj:
#             ad_users.append(
#                 {
#                     "id": ad_user.pk,
#                     "first_name": ad_user.first_name,
#                     "last_name": ad_user.last_name,
#                     "username": ad_user.username,
#                     "role": ad_user.role,
#                     "age": ad_user.age,
#                     "location_names": list(map(str, ad_user.location_names.all())),
#                     "total_ads": ad_user.ad_set.filter(is_published=True).count(),
#                     "ad_price_statistics": ad_user.ad_set.aggregate(average_price=Avg("price"),
#                                                                     max_price=Max("price"),
#                                                                     min_price=Min("price"))
#                 }
#             )
#
#         response = {
#             "items": ad_users,
#             "num_pages": paginator.num_pages,
#             "total": paginator.count,
#             "age_statistics": self.object_list.aggregate(average_age=Avg("age"),
#                                                          max_age=Max("age"), min_age=Min("age"))
#         }
#
#         return JsonResponse(response, safe=False)
# AdUserListSerializer


class AdUserListView(ListAPIView):
    """
    Список пользователей, с сортировкой по username. Queryset выводит дополнительно кол-во
    объявлений со статусом is_published по каждому из списка пользователей.
    """
    queryset = AdUser.objects.annotate(
        total_ads=Count("ads", filter=Q(ads__is_published=True))
    ).order_by("username")
    serializer_class = AdUserListSerializer


class AdUserDetailView(RetrieveAPIView):
    """
    Детальная информация по выбранному пользователю
    """
    queryset = AdUser.objects.annotate(
        total_ads=Count("ads", filter=Q(ads__is_published=True))
    )
    serializer_class = AdUserDetailSerializer

    # def get(self, request, *args, **kwargs):
    #     ad_user = self.get_object()

        # total_ads показывает сумму опубликованных объявлений по пользователю, обращаясь к таблице ad

        # return JsonResponse(AdUserDetailSerializer(ad_user).data)


        # return JsonResponse({
        #     "id": ad_user.pk,
        #     "first_name": ad_user.first_name,
        #     "last_name": ad_user.last_name,
        #     "username": ad_user.username,
        #     "role": ad_user.role,
        #     "age": ad_user.age,
        #     "location_names": list(map(str, ad_user.location_names.all())),
        #     "total_ads": ad_user.ad_set.filter(is_published=True).count()
        # })


# @method_decorator(csrf_exempt, name="dispatch")
class AdUserCreateView(CreateAPIView):
    """
    Создание нового пользователя
    """
    queryset = AdUser.objects.all()
    serializer_class = AdUserCreateSerializer

    # model = AdUser
    # fields = "__all__"
    #
    # def post(self, request, *args, **kwargs):
    #     ad_user_data = json.loads(request.body)
    #
    #     ad_user_new = AdUser.objects.create(
    #         first_name=ad_user_data.get("first_name"),
    #         last_name=ad_user_data.get("last_name"),
    #         username=ad_user_data.get("username"),
    #         password=ad_user_data.get("password"),
    #         role=ad_user_data.get("role"),
    #         age=ad_user_data.get("age")
    #     )
    #
    #     locations = ad_user_data.get("location_names")
    #     for location in locations:
    #         location_obj, _ = Location.objects.get_or_create(name=location)
    #         ad_user_new.location_names.add(location_obj)
    #
    #     locations_all_qs = ad_user_new.location_names.all()
    #
    #     return JsonResponse({
    #         "id": ad_user_new.pk,
    #         "first_name": ad_user_new.first_name,
    #         "last_name": ad_user_new.last_name,
    #         "username": ad_user_new.username,
    #         "password": ad_user_new.password,
    #         "role": ad_user_new.role,
    #         "age": ad_user_new.age,
    #         "location_names": [location_elem.name for location_elem in locations_all_qs]
    #     })


# @method_decorator(csrf_exempt, name="dispatch")
class AdUserUpdateView(UpdateAPIView):
    """
    Обновление данных по пользователю
    """
    queryset = AdUser.objects.all()
    serializer_class = AdUserUpdateSerializer


    # model = AdUser
    # fields = "__all__"
    #
    # def patch(self, request, *args, **kwargs):
    #     super().post(request, *args, **kwargs)
    #
    #     ad_user_data = json.loads(request.body)
    #
    #     if "first_name" in ad_user_data:
    #         self.object.first_name = ad_user_data["first_name"]
    #     if "last_name" in ad_user_data:
    #         self.object.last_name = ad_user_data["last_name"]
    #     if "role" in ad_user_data:
    #         self.object.role = ad_user_data["role"]
    #     if "age" in ad_user_data:
    #         self.object.age = ad_user_data["age"]
    #
    #     locations = ad_user_data.get("location_names")
    #     for location in locations:
    #         location_obj, _ = Location.objects.get_or_create(name=location)
    #         self.object.location_names.add(location_obj)
    #     locations_all_qs = self.object.location_names.all()
    #
    #     self.object.username = get_object_or_404(AdUser, username=ad_user_data["username"])
    #     if self.object.username:
    #         self.object.password = ad_user_data["password"]
    #
    #     try:
    #         self.object.full_clean()
    #     except ValidationError as e:
    #         return JsonResponse(e.message_dict, status=422)
    #
    #     self.object.save()
    #
    #     return JsonResponse({
    #                 "id": self.object.pk,
    #                 "first_name": self.object.first_name,
    #                 "last_name": self.object.last_name,
    #                 "username": self.object.username,
    #                 "password": self.object.password,
    #                 "role": self.object.role,
    #                 "age": self.object.age,
    #                 "location_names": [location_elem.name for location_elem in locations_all_qs]
    #             })


# @method_decorator(csrf_exempt, name="dispatch")
class AdUserDeleteView(DestroyAPIView):
    """
    Удаление пользователя
    """
    queryset = AdUser.objects.all()
    serializer_class = AdUserDestroySerializer

    # model = AdUser
    # success_url = "/"
    #
    # def delete(self, request, *args, **kwargs):
    #     user_ = self.get_object()
    #     user_pk = user_.pk
    #     super().delete(request, *args, **kwargs)
    #     return JsonResponse({"id deleted": user_pk}, status=200)

