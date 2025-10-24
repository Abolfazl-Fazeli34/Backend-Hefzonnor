from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, PhoneVerification


# ---------------------------
# Inline نمایش پروفایل در صفحه کاربر
# ---------------------------
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "پروفایل"
    fk_name = "user"
    extra = 0


# ---------------------------
# مدیریت مدل کاربر
# ---------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("phone_number", "get_first_name", "get_last_name", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "date_joined")
    search_fields = ("phone_number", "profile__first_name", "profile__last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("دسترسی‌ها", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("تاریخ‌ها", {"fields": ("date_joined", "last_login")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "password1", "password2", "is_active", "is_staff"),
        }),
    )

    inlines = [ProfileInline]

    # نمایش نام و نام‌خانوادگی از مدل Profile
    def get_first_name(self, obj):
        return getattr(obj.profile, 'first_name', None)
    get_first_name.short_description = "نام"

    def get_last_name(self, obj):
        return getattr(obj.profile, 'last_name', None)
    get_last_name.short_description = "نام خانوادگی"


# ---------------------------
# مدیریت مدل پروفایل
# ---------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "province", "avatar_preview", "avatar_thumbnail_preview")
    search_fields = ("user__phone_number", "first_name", "last_name")
    list_filter = ("province", "gender", "level")

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 8px;" />',
                obj.avatar.url
            )
        return "—"
    avatar_preview.short_description = "آواتار"

    def avatar_thumbnail_preview(self, obj):
        if obj.avatar_thumbnail:
            return format_html(
                '<img src="{}" width="40" height="40" style="object-fit: cover; border-radius: 6px;" />',
                obj.avatar_thumbnail.url
            )
        return "—"
    avatar_thumbnail_preview.short_description = "تصویر بندانگشتی"


# ---------------------------
# مدیریت مدل تأیید شماره تلفن
# ---------------------------
@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "expires_at", "used", "is_expired_display")
    list_filter = ("used", "created_at")
    search_fields = ("user__phone_number", "code")

    def is_expired_display(self, obj):
        return obj.is_expired
    is_expired_display.boolean = True
    is_expired_display.short_description = "منقضی شده؟"
