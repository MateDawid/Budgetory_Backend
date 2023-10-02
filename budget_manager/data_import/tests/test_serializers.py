import pytest
from data_import.serializers import ImportFileSerializer
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.exceptions import ValidationError


@pytest.mark.django_db
def test_import_file_invalid_extension(txt_file: InMemoryUploadedFile) -> None:
    serializer = ImportFileSerializer(data={'file': txt_file})
    with pytest.raises(ValidationError) as exc:
        serializer.is_valid(raise_exception=True)
    assert (
        'Only .csv files are allowed - .txt is not valid extension.'
        == exc.value.get_full_details()['file'][0]['message']
    )
