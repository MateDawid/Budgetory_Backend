Write-Output "[Quality check - started]";
.\venv\Scripts\activate;
Write-Output "* [black]";
black . --line-length=120;
Write-Output "* [isort]";
isort . --profile black;
Write-Output "* [flake8]";
flake8 .;
Write-Output "[Quality check - finished]";