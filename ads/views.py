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
from rest_framework.viewsets import ModelViewSet

from ads.models import Category, Ad, AdUser, Location
from ads.serializers import AdUserDetailSerializer, AdUserListSerializer, AdUserDestroySerializer, \
    AdUserCreateSerializer, AdUserUpdateSerializer, AdDetailSerializer, LocationModelSerializer
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


#########################################
# Ad


class AdDetailView(RetrieveAPIView):
    """
    Детальная информация по выбранному объявлению
    """
    queryset = Ad.objects.all()
    serializer_class = AdDetailSerializer


class AdListView(ListView):
    """
    Список всех объявлений, с сортировкой по цене объявления по убыванию, с пагинатором и
    итоговой информацией
    """

    model = Ad

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        self.object_list = self.object_list.select_related("author").order_by("-price")

        # переопределяем queryset
        categories = request.GET.getlist("cat", None)
        if categories:
            self.object_list = self.object_list.filter(category_id__in=categories)
        # if getlist, then can input several categories in list

        # поиск по вхождению слова в название объявления, без учета регистра
        text = request.GET.get("text")
        if text:
            self.object_list = self.object_list.filter(name__icontains=text)

        location = request.GET.get("loc")
        if location:
            self.object_list = self.object_list.filter(author__location_names__name__icontains=location)

        price_from = request.GET.get("price_from")
        if price_from:
            self.object_list = self.object_list.filter(price__gte=price_from)
        price_to = request.GET.get("price_to")
        if price_to:
            self.object_list = self.object_list.filter(price__lte=price_to)

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


####################
# User

class LocationViewSet(ModelViewSet):
    """
    Класс с адресами на основе ViewSet с использованием Router и сериализатора
    """
    queryset = Location.objects.all()
    serializer_class = LocationModelSerializer


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


class AdUserCreateView(CreateAPIView):
    """
    Создание нового пользователя
    """
    queryset = AdUser.objects.all()
    serializer_class = AdUserCreateSerializer


class AdUserUpdateView(UpdateAPIView):
    """
    Обновление данных по пользователю
    """
    queryset = AdUser.objects.all()
    serializer_class = AdUserUpdateSerializer


class AdUserDeleteView(DestroyAPIView):
    """
    Удаление пользователя
    """
    queryset = AdUser.objects.all()
    serializer_class = AdUserDestroySerializer


