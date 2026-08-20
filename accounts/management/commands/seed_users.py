from django.core.management.base import BaseCommand
from accounts.models import User
from accounts.utils import hash_pin


class Command(BaseCommand):
    help = 'Seed admin user into the database.'

    def handle(self, *args, **kwargs):
        users = [
            {
                'email': 'cascallensteve@gmail.com',
                'username': 'mkusdachurch',
                'first_name': 'MKUS',
                'last_name': 'Treasury',
                'password': 'treasury2026',
                'pin': '0000',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        ]

        for data in users:
            email = data['email']
            username = data['username']

            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.filter(username=username).first()

            if user:
                password = data.get('password')
                pin = data.get('pin')
                if password:
                    user.set_password(password)
                if pin:
                    user.pin = hash_pin(pin)
                    user.pin_setup_complete = True
                user.is_staff = data.get('is_staff', user.is_staff)
                user.is_superuser = data.get('is_superuser', user.is_superuser)
                user.is_active = data.get('is_active', user.is_active)
                user.save()
                self.stdout.write(self.style.WARNING(f'Updated user: {email}'))
            else:
                password = data.pop('password')
                pin = data.pop('pin')
                user = User(**data)
                user.set_password(password)
                user.pin = hash_pin(pin)
                user.pin_setup_complete = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created admin: {email}'))