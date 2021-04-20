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

# Airflow: Ejecución en paralelo y escalado. LocalExecutor

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
* `executor = LocalExecutor`

Comprobamos el acceso con:

* `airflow db check`

Si el resultado es correcto indicará que hemos configurado correctamente Airflow para utilizar Postgres como nuestro repositorio para el metastore.

Ahora detenemos el scheduler y el webserver, y ejecutamos de nuevo la orden:

* `airflow db init`

Y la de creación de usuario (vista más arriba).

Iniciamos los procesos y veremos que ahora las tareas se ejecutan en paralelo.

# Airflow: Ejecución en paralelo y escalado. CeleryExecutor

Con el LocalExecutor ejecutaremos todas las tareas en un solo servidor como si fuesen subprocesos. Esto también tiene limitaciones. Con el LocalExecutor, todas las tareas que se tienen que ejecutar se envían a una cola o `queue` para que se ejecuten en el orden correcto, y cada una de esas tareas se convierte en un subproceso.

Ahora tendremos `workers`, serán máquinas dedicadas donde se ejecutarán las tareas existentes en la `queue`.

## CeleryExecutor

Es un sistema de tareas distribuído.

<img src="img/i_005.png"/>

Con el CeleryExecutor, la `queue` está fuera del executor y en este caso la cola será gestionada por **Redis**.

Démonos cuenta del parámetro `worker_concurrency = 2`. Define el number de tareas que se pueden ejecutar a la vez en cada worker.

<img src="img/i_006.png"/>

## Configuración

* `pip install apache-airflow[celery]`

### Redis 

* `pip install apache-airflow[redis]`
* `sudo apt install redis-server`
* Cambiamos la configuración de redis para arrancarlo como servicio, cambiamos `supervised` con el valor **systemd**.
* `sudo systemctl restart redis.service` y comprobamos que se ha iniciado con `sudo systemctl restart redis.service`

Instalamos un cliente gráfico para Redis

* `sudo snap install redis-desktop-manager`

### CeleryExecutor

* `executor = CeleryExecutor` en el fichero airflow.cfg
* `broker_url = redis://localhost:6379/0`. La base de datos es `0` que se creará la primera vez que se vaya a insertar algo.
* `result_backend = db+postgresql://airflow:airflow@localhost:5432/airflow`

Una feature que viene por defecto para monitorizar los workers, es **Flower**.

* `airflow celery flower`. Estará disponible en el puerto 5555. Si echamos un vistazo vemos que no tenemos ahora mismo configurado ningún worker, por tanto, no podremos ejecutar ninguna de las tareas con airflow.

## Agregando nuevos workers

Para agregar un nuevo worker en la máquina donde se está ejecutando airflow podemos ejecutar:

* `airflow celery worker`

Este comando lo deberíamos ejecutar en cada servidor que quisiéramos que formase parte de nuestro cluster de airflow. Una vez ejecutado este comando, podemos comprobar con **Flower** que tenemos una máquina lista para poder ejecutar tareas.

Ahora, ¿cómo podríamos limitar el número de ejecuciones de DAGs en cada worker?, es decir, ¿cómo decidir cuántos DAGs runs podríamos tener en paralelo?, ¿y cómo limitar el número de tareas que podemos ejecutar en cada máquina?.

### Parallelism

Definer el número total de tareas que se pueden ejecutar en paralelo en todo el cluster o instancia de Airflow. Por defecto está a 32. Si pusiésemos este valor a 1, estaríamos replicando el comportamiento del SequentialExecutor.

Esto tendría sentido si por ejemplo quisiéramos que nuestra instancia de Airflow no consumiese todos los recursos disponibles de una máquina. **Pero un caso de uso más habitual es limitar el número de tareas simultáneas que pueden ejecutar un DAG concreto**.

### dag_concurrency

Es el número de *task instances* que se pueden ejecutar en paralelo en un DAG. Se puede sobreescribir por el parámetro `concurrency` a nivel de DAG.

**Se recomienda dejar los valores por defecto en parallelism y dag_concurrency y ajustar el parámetro el parámetro concurrency para cada DAG que creemos.**

## DAGs runs concurrency

¿Cómo limitar las ejecuciones simultáneas de los DAGs?, supongamos que tienen que ejecutarse se forma secuencial porque los datos que generados en una ejecución se utilizan por la siguiente.

### max_active_runs_per_dag

Por defecto está a 16. Controla las ejecuciones simultáneas que puede haber de un mismo DAG.

Se puede configurar en el fichero airflow.cfg (afectará a todos los DAGs) o bien utilizar el parámetro `max_active_runs` a nivel de DAG.


# Airflow: complex data pipelines

## Agrupación de tareas, TASK GROUPS

Se trata de agrupar tareas con la misma funcionalidad para que el DAG no sea muy complejo y para facilitar su comprensión. Se trataría de pasar de esta situación ...

<img src="img/i_008.png"/>

... a esta otra ...

<img src="img/i_009.png"/>

Se trata de usar **TaskGroup**

```
from airflow.utils.task_group import TaskGroup

...

with TaskGroup('processing_tasks') as processing_tasks:
    task_2 = BashOperator(
        task_id='task_2',
        bash_command='sleep 3'
    )

    task_3 = BashOperator(
        task_id='task_3',
        bash_command='sleep 3'
    )
```

Para crear Subgrupos dentro de Grupos sería de la misma forma.

Los nombres de las tareas que están dentro de un grupo o un subgrupo se renombrarán y se añadirá como prefijo el nombre del grupo o subgrupo al que pertenecen.

# Airflow: XComs, intercambio de datos

Permite intercambiar datos entre distintas taraes. Está limitado en tamaño, por ejemplo, para Postgres, está limitado a 1GB.

# Airflow: elegir las tareas a ejecutar

Ejecutaremos una tarea u otra dependiendo de los valores que obtengamos en tareas previas, por ejemplo, el resultado de una consulta a base de datos.

Para esto tendremos que utilizar el **BranchPythonOperator**. Nos permite ejecutar una tarea u otra devolviendo el task_id de la tarea que queremos ejecutar.

Bajo los XComs se almacenará la tarea devuelta por el `branch operator`.

# Airflow: Trigger rules

Nos permite cambiar el comportamiento por defecto relacionado con las dependencias. Por defecto, si hay tres tareas que tienen que ejecutarse en paralelo y luego una cuarta, ésta última sólo se ejecutará si las tres finalizaron bien. ¿Y si quiero que se ejecute sólo cuando una ha ido mal?, ¿o cuándo solo una ha ido bien?.

Mediante las **Trigger rules** podemos cambiar este comportamiento por defecto y determinar bajo qué condiciones se ejecutará una tarea. **Hay 9 diferentes**:

## [task_a, task_b] >> task_c

### all_success

Es el comportamiento por defecto). Si `task_a` finaliza con error, `task_c` quedará en estado `upstream_failed`

### all_failed

`task_c` se ejecutará si las dos tareas fallan. Quedará en estado `skipped` si una de las dos finalizó con éxito.

### all_done

`task_c` se ejecutará si las dos anteriores se ejecutaron y sin importar el estado en que finalizaron.

### one_success

`task_c` se ejecutará si una de las dos anteriores terminó con éxito.

### one_failed

`task_c` se ejecutará si una de las dos anteriores terminó `failed`.

### none_failed

`task_c` se ejecutará si las dos anteriores terminaron en los estados `success` o `skipped`.

### none_failed_or_skipped

`task_c` se ejecutará si al menos uno de los padres terminó `success`. El resto pueden terminar `skipped`. La diferencia con la regla anterior **none_failed** es que con **none_failed** se ejecutará `task_c` si las dos tareas terminaron en `skipped`. Con la regla **none_failed_or_skipped** al menos una tiene que finalizar con éxito.

Disponemos del parámetro `trigger_rule` en cada task para indicar estas dependencias.

# Airflow: creación de plugins

Se pueden crear:

* Operators
* Views
* Hooks

Hay tres carpetas que Airflow monitoriza:

* plugins. Aquí pondremos nuestros plugins (tendremos que crearla).
* config
* dags

En Airflow 2.0, la clase `AirflowPluginClass` se utiliza para personalizar la interfaz de usuario (antes se utilizaba para crear plugins y nuestros desarrollos heredaban de ella).

En Airflow 2.0, los plugins se crean como módulos normales de Python. Dentro de la carpeta `plugins` creamos una carpeta con el nombre del plugin y dentro de aquí el código python con los nuevos operators, ... y ya podremos utilizarmos directamente en nuestros **Data Pipelines**.

La carga de plugins es *Lazy Loaded*, tendremos que reiniciar la instancia de Airflow cada vez que agreguemos un nuevo plugin. Luego podremos modificarlos sin necesidad de reiniciar la instancia una y otra vez.