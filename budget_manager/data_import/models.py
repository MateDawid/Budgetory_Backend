from django.core.validators import FileExtensionValidator
from django.db import models


class ImportFile(models.Model):
    file = models.FileField(
        upload_to='import_files', null=True, validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )
    headers = models.JSONField(null=True)
    content = models.JSONField(null=True)
    date_added = models.DateTimeField(auto_now_add=True)
