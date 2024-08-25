Write-Output "[Quality check]";
.\venv\Scripts\activate;
Write-Output "* [black]";
black .;
Write-Output "* [isort]";
isort . --profile black;
Write-Output "* [flake8]";
flake8 .
