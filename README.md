# Airflow: Componentes Core

## Web server

Flask server with Gunicorn serving the UI

## Scheduler

Daemon in charge of scheduling workflows

## Metastore

Database where metadata are stored

## Executor

Class defining **how** your tasks should be executed (en K8s, en celery, en local, etc.)

## Worker

Process/sub process **executing** your task


# Airflow: Conceptos Fundamentales

## DAG

Es un **data pipeline** sin loops. Significa *Directed acyclic graph*.

## Operator

Es un wrapper sobre la tarea que queremos ejecutar.

Hay tres tipos de **Operators**:

### Action Operators

Por ejemplo, el **bash operator** permitirá ejecutar comandos shell, el **python operator** permitirá ejecutar funciones en python, etc.

### Transfer Operators

Permite transferir datos entre el origen y el destino de los datos.

### Sensor Operators

Esperan a que algo suceda antes de pasar a la siguiente tarea. Por ejemplo, el **file sensor** espera a que un fichero exista en una determinada localización.

## Task/Task instance

Una tarea es un operator en el data pipeline. Y una instancia de tarea es el operator en ejecución. Cuando ejecutamos un operator, obtenemos una *task instance*.

## Workflow

Es una combinación de los elementos vistos hasta ahora.

**Worflow** = DAG + Operators + Tasks + Dependencies.


**AIRFLOW NO ES UNA SOLUCIÓN DATA STREAMING NI UN FRAMEWORK PARA EL PROCESO DE DATOS**

# Airflow: arquitectura

## One Node Architecture

El scheduler iniciará las tareas mediante los executors y éstos actualizarán el estado de la tarea en el metastore. Las **queue** son parte de los executors, definen el orden en que deben ejecutarse las tareas. En la arquitectura 'one node' tenemos que cada 'queue' es parte del executor.

<img src="img/i_001.png"/>

## Multi Nodes Architecture

En este caso el componente **Queue** es externo, puede ser Redis o RabbitMQ.

<img src="img/i_002.png"/>

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

## Creación de la carpeta para albergar los DAGs

Dentro del fichero `~/airflow/airflow.cfg` está la propiedad `dags_folder`. Es aquí donde ubicaremos los scripts que diseñemos. En nuestro caso tenemos
```
dags_folder = /home/jcla/airflow/dags
```

Por lo tanto:
```
mkdir ~/airflow/dags
```


# Airflow: CLI

## Ayuda

* `airflow -h`
* `airflow db -h`
* `airflow users -h`
* `airflow users create -h`

## Base de datos

* `airflow db init`
* `airflow db upgrade`
* `airflow db reset`

## Inicio de servicios

* `airflow webserver`
* `airflow scheduler`

## DAGs

* `airflow dags list`
* `airflow tasks list tutorial`
* `airflow dags trigger -e 2021-01-01 tutorial`

# Airflow: DAGs

## Testing

Pasamos como parámetro el dag_id, el task_id y una fecha de ejecución pasada:

`airflow tasks test transfermarkt_processing creating_table 2021-01-01`

Para el caso de la creación de la tabla en sqlite, podemos comprobarlo accediendo a la base de datos de la siguiente forma:

`sqlite3 airflow.db`

y ejecutando la select correcta.

## Scheduling

Cuando se define un DAG hay dos argumentos importantes que siempre se definen.

* `start_date`: define cuándo empezará a planificarse la ejecución del DAG.
* `schedule_interval`: define la frecuencia con la que se ejecutará el data pipeline.

**Todas las fechas en Airflow están en horario UTC**. Existe un parámetro en el fichero de configuración que se llama `default_ui_timezone` donde se puede modificar este comportamiento. Se recomienda mantener este comportamiento.

### Backfilling

Si pausamos la ejecución de un DAG y la reanudamos más adelante, Airflow intentará lanzar todas las ejecuciones perdidas según se haya indicado en el `schedule_interval` empezando desde la última ejecución realizada.

### Catchup

Controla si debe ejecutarse o no el backfilling.

# Airflow: Ejecución en paralelo y escalado

Estudiaremos los parámetros necesarios para ejecutar múltiples DAGs y veremos qué **executors** nos permitirán escalar Airflow. Seremos capaces de ejecutar tantas tareas como necesitemos.

Con la configuración por defecto, si tenemos varias tareas que pueden ejecutarse en paralelo, se ejecutarán de forma secuencial. ¿Cuál se ejecutará antes?, no sabemos. El **executor** por defecto es el **Sequential Executor**. Los parámetros que nos permitirán controlar el executor son:

* sql_alchemy_conn
* executor

Para obtener sus valores ejecutamos

* `airflow config get-value core sql_alchemy_conn`
* `airflow config get-value core executor`

Por defecto estamos utilizando SQLite como metastore y esta base de datos no permite escrituras simultáneas o concurrentes. Por este motivo, las tareas se ejecutarán de forma secuencial.

Y vemos que por defecto se está utilizando el executor **SequentialExecutor**. Permite ejecutar las tareas de forma secuencial. Configuremos ahora Airflow para poder ejecutar taraes de forma paralela. Tendremos que:

1. Cambiar la base de datos a Postgres para permitir lecturas y escrituras concurrentes
2. Cambiar al **LocalExecutor**. Con esto, cada tarea se ejecutará en un subproceso. Una tarea se ejecutará en un subproceso.

## Configuración de Postgres

Instalamos un paquete adicional:

* `pip install 'apache-airflow[postgres]'`

Modificamos los siguientes parámetros en el fichero de configuración:

* `sql_alchemy_conn = postgresql+psycopg2://airflow:airflow@localhost:5432/airflow`

Comprobamos el acceso con:

* `airflow db check`

Si el resultado es correcto indicará que hemos configurado correctamente Airflow para utilizar Postgres como nuestro repositorio para el metastore.