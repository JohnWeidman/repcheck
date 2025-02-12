from django.contrib import admin
from .models import Congress, Member, Membership
# Register your models here.

admin.site.register(Congress)
admin.site.register(Member)
admin.site.register(Membership)
