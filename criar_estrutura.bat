@echo off
SET ROOT=poc-bridge

echo Criando diretorios para %ROOT%...
mkdir %ROOT%
mkdir %ROOT%\app
mkdir %ROOT%\app\core
mkdir %ROOT%\app\services
mkdir %ROOT%\app\api
mkdir %ROOT%\app\api\v1
mkdir %ROOT%\storage

echo Criando arquivos __init__.py...
type nul > %ROOT%\app\__init__.py
type nul > %ROOT%\app\core\__init__.py
type nul > %ROOT%\app\services\__init__.py
type nul > %ROOT%\app\api\__init__.py
type nul > %ROOT%\app\api\v1\__init__.py

echo Criando arquivos de logica...
type nul > %ROOT%\app\main.py
type nul > %ROOT%\app\core\security.py
type nul > %ROOT%\app\services\poc_service.py
type nul > %ROOT%\app\services\storage.py
type nul > %ROOT%\app\api\v1\alerts.py

echo Criando arquivos de configuracao...
type nul > %ROOT%\.env
type nul > %ROOT%\requirements.txt
type nul > %ROOT%\README.md
type nul > %ROOT%\ARQUITETURA.md

echo Estrutura criada com sucesso em /%ROOT%
pause