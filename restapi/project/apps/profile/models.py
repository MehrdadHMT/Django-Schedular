from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from logging import getLogger

from project.apps.profile.v1.validators import phone_regex_validator

logger = getLogger(__name__)


class User(AbstractBaseUser):
    ADMIN_USER = 1
    NORMAL_USER = 2
    USER_TYPES = [
        (ADMIN_USER, 'admin'),
        (NORMAL_USER, 'normal')
    ]

    first_name = models.CharField(_('first_name'), max_length=32)
    last_name = models.CharField(_('last_name'), max_length=32)
    email = models.EmailField(_('email address'), unique=True, blank=False, null=False)
    phone_number = models.CharField(validators=[phone_regex_validator], unique=True, blank=True, null=True, max_length=11)
    permission = models.SmallIntegerField(choices=USER_TYPES, default=NORMAL_USER)

    def save(self, *args, **kwargs):
        if not self.phone_number:
            self.phone_number = None

        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.email

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
