# Airflow: instalación

## Creación de entorno virtual para Airflow

```
cd ~/Projects/venvs
python -m venv airflow
source airflow/bin/activate
pip install --upgrade pip==20.2.4
```

## Instalación de Airflow

Definimos la variable AIRFLOW_HOME en `.bashrc`
```
cd
mkdir airflow
echo "export AIRFLOW_HOME=~/airflow" >> .bashrc
. ./.bashrc
echo $AIRFLOW_HOME
```

Definimos algunas variables necesarias para la instalación
```
AIRFLOW_VERSION=2.0.1
PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
```

Instalamos Airflow
```
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

## Inicialización de la base de datos

```
airflow db init
```

Esto nos creará una base de datos y los ficheros de configuración bajo `$AIRFLOW_HOME`.

### Creación de usuario

```
airflow users create \
    --username admin \
    --firstname admin \
    --lastname admin \
    --role Admin \
    --email admin@admin.org
```

Introducimos la password: `admin`

## Inicio del servidor y del scheduler

```
airflow webserver --port 8080
airflow scheduler
```
