import pytest
from data_import.models import ImportFile
from data_import.views import ImportFileViewSet
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from tests.data_import.factories import ImportFileFactory
from tests.factories import UserFactory


@pytest.mark.django_db
def test_get_import_files_list(
    valid_csv_file_content: list, import_file_factory: ImportFileFactory, api_rf: APIRequestFactory, user: UserFactory
) -> None:
    headers = list(valid_csv_file_content[0].keys())
    import_file = import_file_factory(content=valid_csv_file_content, headers=headers)  # noqa

    view = ImportFileViewSet.as_view({'get': 'list'})
    request = api_rf.get('/import_file')
    force_authenticate(request, user)
    response = view(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['results'][-1]['content'] == import_file.content
    assert response.data['results'][-1]['headers'] == import_file.headers
    assert len(response.data['results']) == len(ImportFile.objects.all())


@pytest.mark.django_db
def test_import_file_creation(
    valid_data_file: InMemoryUploadedFile, valid_csv_file_content: list, api_rf: APIRequestFactory, user: UserFactory
) -> None:
    url = 'api/import_file/'
    data = {
        'file': valid_data_file,
        'filename': 'test_file',
    }

    view = ImportFileViewSet.as_view({'post': 'create'})
    request = api_rf.post(url, data=data)
    force_authenticate(request, user)
    response = view(request)

    assert status.HTTP_201_CREATED == response.status_code
    assert ImportFile.objects.filter(filename='test_file').exists()

    import_file = ImportFile.objects.get(filename='test_file')
    assert import_file.headers == list(valid_csv_file_content[0].keys())
    assert import_file.content == valid_csv_file_content
    assert str(import_file) == f'test_file ({import_file.date_added})'
