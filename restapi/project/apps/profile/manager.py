from django.contrib.auth.base_user import BaseUserManager
from django.db.models.manager import Manager
from django.db.models import Q, Count
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from project.settings import VALUES


class UserManager(BaseUserManager):
    def create_user(self, phone, password, name=None, picture=None, **extra_fields):
        if not phone:
            raise ValueError(_("The phone no. must be provided."))
        if len(phone) != 11:
            raise ValueError(_("The Phone No Should be 10 digits long."))
        if not name:
            name = VALUES['DEFAULT_USER_NAME']
        user = self.model(phone=phone, name=name, picture=None, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))

        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))
        super_user = self.create_user(phone, 'default', password, picture=None,  **extra_fields)
        super_user.set_password(password)
        super_user.name = f'Admin-{super_user.id}'
        super_user.save()

        return super_user


class InstaClientManager(Manager):
    def active_filter(self, active=True, *args, **kwargs):
        if active:
            active_filter = self.filter(Q(active_at__lt=now()) | Q(active_at__isnull=True))
        else:
            active_filter = self.filter(Q(active_at__gt=now()) & Q(active_at__isnull=False))
        return active_filter.filter(*args, **kwargs)

    def get_random(self, active=True, number=1, max_followings=VALUES['INSTA_CLIENT_MAX_FOLLOWING']):
        objects = self.active_filter(active=active).annotate(c=Count('followings')).filter(c__lt=max_followings)
        try:
            return objects.order_by('?')[:number]
        except ValueError:
            return objects
