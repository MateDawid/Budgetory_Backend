param([String]$path=".")

Write-Output "[Quality check - started in '$path' path]";
.\venv\Scripts\activate;
Write-Output "* [black]";
black $path --line-length=120;
Write-Output "* [isort]";
isort $path --profile black;
Write-Output "* [flake8]";
flake8 $path;
Write-Output "[Quality check - finished]";