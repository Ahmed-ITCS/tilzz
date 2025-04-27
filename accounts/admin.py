from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Organization, Follow

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'organization')
    list_filter = ('role', 'organization')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'bio', 'profile_picture', 'organization')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Organization)
admin.site.register(Follow)
