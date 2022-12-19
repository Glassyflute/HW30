from django.contrib import admin

# Register your models here.
from ads.models import Ad, Category, Location, AdUser

admin.site.register(Ad)
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(AdUser)


