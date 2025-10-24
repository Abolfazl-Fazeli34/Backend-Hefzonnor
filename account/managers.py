from django.contrib.auth.base_user import BaseUserManager
import re


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError('phone_number must be set')
        phone = self.normalize_phone(phone_number)
        user = self.model(phone_number=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def normalize_phone(self, phone):
        phone = phone.strip()
        phone = re.sub(r'\D', '', phone)
        if phone.startswith('0'):
            phone = '+98' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+' + phone
        return phone
    
    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone_number, password, **extra_fields)
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        # if extra_fields.get('is_active') is not True:
        #     raise ValueError('Superuser must have is_active=True.')
        return self._create_user(phone_number, password, **extra_fields)
    
    