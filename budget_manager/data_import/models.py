from django.db import models


class ImportFile(models.Model):
    filename = models.CharField(max_length=128)
    headers = models.JSONField(null=True)
    content = models.JSONField(null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.filename} ({self.date_added})'
