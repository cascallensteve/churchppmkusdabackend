from django.db import models
from django.conf import settings


class DonationType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='donation_types')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def update_balance(self):
        from payments.models import Transaction
        total = Transaction.objects.filter(
            donation_type=self,
            status=Transaction.SUCCESS
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        self.balance = total
        self.save(update_fields=['balance'])
