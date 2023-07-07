import pytest
from data_import.models import ImportFile
from data_import.views import ImportFileViewSet
from rest_framework import status
from rest_framework.test import force_authenticate


@pytest.mark.django_db
def test_get_import_files(valid_csv_file_content, import_file_factory, api_rf, user):
    headers = list(valid_csv_file_content[0].keys())
    import_file = import_file_factory(content=valid_csv_file_content, headers=headers)

    view = ImportFileViewSet.as_view({'get': 'list'})
    request = api_rf.get('/import_file')
    force_authenticate(request, user)
    response = view(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['results'][-1]['content'] == import_file.content
    assert response.data['results'][-1]['headers'] == import_file.headers
    assert len(response.data['results']) == len(ImportFile.objects.all())
