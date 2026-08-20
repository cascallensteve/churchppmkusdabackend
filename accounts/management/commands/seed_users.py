from django.core.management.base import BaseCommand
from accounts.models import User
from accounts.utils import hash_pin


class Command(BaseCommand):
    help = 'Seed admin user into the database.'

    def handle(self, *args, **kwargs):
        users = [
            {
                'email': 'mkusdachurchtreasry@gmail.com',
                'username': 'mkusdachurchtreasry',
                'first_name': 'MKUSDA',
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
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'User {email} already exists.'))
                continue

            password = data.pop('password')
            pin = data.pop('pin')
            user = User(**data)
            user.set_password(password)
            user.pin = hash_pin(pin)
            user.pin_setup_complete = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin: {email}'))
