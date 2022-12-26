from rest_framework import serializers

from ads.models import AdUser, Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


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


class AdUserDetailSerializer(serializers.ModelSerializer):
    location_names = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )
    total_ads = serializers.IntegerField()

    class Meta:
        model = AdUser
        exclude = ['password']


class AdUserCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    location_names = serializers.SlugRelatedField(
        required=False,
        many=True,
        queryset=Location.objects.all(),
        slug_field="name"
    )

    class Meta:
        model = AdUser
        fields = '__all__'

    def is_valid(self, raise_exception=False):
        self._location_names = self.initial_data.pop("location_names")
        return super().is_valid(raise_exception=raise_exception)

    def create(self, validated_data):
        new_user = AdUser.objects.create(**validated_data)

        for loc_item in self._location_names:
            loc_obj, _ = Location.objects.get_or_create(name=loc_item)
            new_user.location_names.add(loc_obj)

        new_user.save()
        return new_user


class AdUserUpdateSerializer(serializers.ModelSerializer):
    location_names = serializers.SlugRelatedField(
        required=False,
        many=True,
        queryset=Location.objects.all(),
        slug_field="name"
    )

    class Meta:
        model = AdUser
        fields = '__all__'

    def is_valid(self, raise_exception=False):
        self._location_names = self.initial_data.pop("location_names")
        return super().is_valid(raise_exception=raise_exception)

    def save(self):
        user_upd = super().save()

        for loc_item in self._location_names:
            loc_obj, _ = Location.objects.get_or_create(name=loc_item)
            user_upd.location_names.add(loc_obj)

        user_upd.save()
        return user_upd


class AdUserDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdUser
        fields = ["id"]
