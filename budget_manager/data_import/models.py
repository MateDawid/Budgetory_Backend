from django.core.validators import FileExtensionValidator
from django.db import models


class ImportFile(models.Model):
    file = models.FileField(
        upload_to='import_files', null=True, validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )
    filename = models.CharField(max_length=128)
    headers = models.JSONField(null=True)
    content = models.JSONField(null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.filename} ({self.date_added})'
