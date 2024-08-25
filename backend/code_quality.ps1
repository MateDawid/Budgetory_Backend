Write-Output "[Quality check]";
.\venv\Scripts\activate;
Write-Output "* [black]";
black . --line-length=120;
Write-Output "* [isort]";
isort . --profile black;
Write-Output "* [flake8]";
flake8 .
