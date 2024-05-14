from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from logging import getLogger

from project.apps.profile.v1.validators import phone_regex_validator

logger = getLogger(__name__)


class User(AbstractBaseUser):
    email = models.EmailField(_('email address'), unique=True, blank=False, null=False)
    phone_number = models.CharField(validators=[phone_regex_validator], unique=True, blank=True, null=True, max_length=11)

    def save(self, *args, **kwargs):
        if not self.phone_number:
            self.phone_number = None

        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.email

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
