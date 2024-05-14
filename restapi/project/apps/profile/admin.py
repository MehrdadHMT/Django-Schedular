from django import forms
from django.contrib import admin, messages
from django.db.models import Q
from django.contrib.auth.admin import UserAdmin

from project.apps.forms import user_choice
from project.apps.profile.forms import CustomUserChangeForm, CustomUserCreationForm
from project.apps.profile.models import User, Contact, now, TokenMetaData


class ActivationListFilter(admin.SimpleListFilter):
    title = 'Activation'
    parameter_name = 'active_at'

    def lookups(self, request, model_admin):
        return (
            ('YES', 'Active'),
            ('NO', 'Blocked'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'YES':
            return queryset.filter(Q(active_at__lt=now()) | Q(active_at__isnull=True))
        if self.value() == 'NO':
            return queryset.filter(Q(active_at__gt=now()) & Q(active_at__isnull=False))
        else:
            return queryset.all()


class LiveListFilter(admin.SimpleListFilter):
    title = 'Ended or Expired'
    parameter_name = 'active_at'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Ended'),
            ('2', 'Expired'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(end_time__isnull=False)
        if self.value() == '2':
            return queryset.filter(exp_time__lte=now())
        return queryset.all()


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('id', 'phone', 'name', 'is_staff', 'is_active', 'is_vip')
    list_filter = ('is_staff', 'is_active', 'is_vip')

    fieldsets = (
        (None, {'fields': ('phone', 'name', 'picture', 'description', 'banner_url', 'password', 'created_at', 'rsa_pub', 'rsa_priv',
                           'updated_at', 'object_last_modified',  'channel_name', 'used_quota', 'base_plan_expiration', 'total_quota',
                           'quota_renew_time', 'total_gift', 'gift_renew_time', 'crm_free_order_id', 'searchable',)}),
        ('Wallet', {'fields': ('withdrawable_balance', 'gifted_balance')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_vip')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2', 'name', 'is_staff', 'is_vip')
        }),
    )
    search_fields = ('phone', 'name')
    ordering = ('phone',)
    readonly_fields = ('picture', 'created_at', 'updated_at', 'object_last_modified', )


@admin.action(description='Set expiration as end time.')
def set_end(modeladmin, request, queryset):
    for obj in queryset:
        obj.end_time = obj.exp_time
    queryset.bulk_update(queryset, fields=['end_time'])
    messages.success(request, f'{queryset.count()} object\'s end time has been set.')


@admin.action(description='Force active client(s).')
def force_active(modeladmin, request, queryset):
    queryset.update(active_at=None)
    messages.success(request, 'Activation completed successfully.')


@admin.action(description='Force block client(s).')
def force_block(modeladmin, request, queryset):
    blocked = [cli.set_block() for cli in queryset]
    messages.success(request, f'{len(blocked)} clients blocked successfully.')


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = '__all__'

    user = user_choice
    contact = user_choice


class ContactAdmin(admin.ModelAdmin):
    form = ContactForm


class TokenMetaDataAdmin(admin.ModelAdmin):
    list_display = ('token', 'user_agent', 'ip', 'user_device', 'last_used',)
    search_fields = ('token', )
    list_filter = ('user_agent', )


admin.site.register(User, CustomUserAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(TokenMetaData, TokenMetaDataAdmin)
