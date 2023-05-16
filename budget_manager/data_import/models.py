from django.db import models


class ImportFile(models.Model):
    file = models.FileField(upload_to=None)
    filename = models.CharField(max_length=128)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.filename} ({self.date_added})'
