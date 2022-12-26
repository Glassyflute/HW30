from rest_framework import serializers

from ads.models import AdUser, Location


# class LocationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Location
#         fields = '__all__'


class AdUserListSerializer(serializers.ModelSerializer):
    location_names = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )
    total_ads = serializers.IntegerField()

    class Meta:
        model = AdUser
        exclude = ['password']
        # fields = '__all__'


class AdUserDetailSerializer(serializers.ModelSerializer):
    location_names = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )

    class Meta:
        model = AdUser
        exclude = ['password']
        # fields = '__all__'
#
#
# class VacancyCreateSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(required=False)
#     skills = serializers.SlugRelatedField(
#         required=False,
#         many=True,
#         queryset=Skill.objects.all(),
#         slug_field="name"
#     )
#
#     class Meta:
#         model = Vacancy
#         fields = '__all__'
#
#     def is_valid(self, raise_exception=False):
#         self._skills = self.initial_data.pop("skills")
#         return super().is_valid(raise_exception=raise_exception)
#
#     def create(self, validated_data):
#         vacancy = Vacancy.objects.create(**validated_data)
#
#         for skill in self._skills:
#             skill_obj, _ = Skill.objects.get_or_create(name=skill)
#             vacancy.skills.add(skill_obj)
#
#         vacancy.save()
#         return vacancy
#
#
# class VacancyUpdateSerializer(serializers.ModelSerializer):
#     skills = serializers.SlugRelatedField(
#         required=False,
#         many=True,
#         queryset=Skill.objects.all(),
#         slug_field="name"
#     )
#     user = serializers.PrimaryKeyRelatedField(read_only=True)
#     created = serializers.DateField(read_only=True)
#
#     class Meta:
#         model = Vacancy
#         fields = ["id", "text", "slug", "status", "created", "skills", "user"]
#
#     def is_valid(self, raise_exception=False):
#         self._skills = self.initial_data.pop("skills")
#         return super().is_valid(raise_exception=raise_exception)
#
#     def save(self):
#         vacancy = super().save()
#
#         for skill in self._skills:
#             skill_obj, _ = Skill.objects.get_or_create(name=skill)
#             vacancy.skills.add(skill_obj)
#
#         vacancy.save()
#         return vacancy
#
#
# class VacancyDestroySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Vacancy
#         fields = ["id"]
