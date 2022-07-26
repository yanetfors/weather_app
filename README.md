# Project Weather Forecast
## Descripción del Proyecto

El presente proyecto tiene como objetivo obtener y procesar información sobre el clima para que pueda ser usada en modelos predictivos.

## Solución Actual
La primera versión es una propuesta de ETL con Pandas, y Postgres como base de datos. 
La lógica principal que se sigue es la siguiente (ejecutándose el mismo proceso cada hora):
1. Obtener los datos del API https://smn.conagua.gob.mx/es/web-service-api, específicamente el segundo servicio que obtiene los datos por hora y a 48 horas. Guardar el archivo comprimido en una carpeta de nombre raw.
2. Descomprimir el archivo y guardarlo en formato csv en una carpeta de nombre stg. Los nombres de los archivos
tendrán el formato YYYY_mm_dd-H  (Ejemplo: 2002_07_25-10), de manera que se puede notar por el nombre la fecha y hora en que se descargó la información.
3. Procesar el archivo para obtener uno nuevo con el promedio de temperatura y precipitación (de las últimas dos horas anteriores) por estado y municipio.
4. Obtener la informacion más reciente de la carpeta data_municipios. Aquí se asume que el nombre de las carpetas y el archivo siempre coincidirán con el del ejemplo brindado. Por lo que la información más reciente se tomará por el nombre de la carpeta que coincida con la de mayor fecha.
5. Hacer un unión entre la información del promedio(paso 3) y la última más reciente(paso 4) por id de estado y municipio. El merge se hace respetando los datos del archivo data_municipio.
6. Se cargan los datos del dataset con el promedio de temperatura y precipitación a una tabla en la base de datos (weather_avg).
7. Se cargan los datos del dataset del paso 4 a una tabla en la base de datos (weather_data_mun).
8. Se cargan los datos del dataset anterior a una tabla en la base de datos (weather_current). En los dos casos anteriores se hace un append de los registros agregándole la fecha de inserción,y en este último se elimina la tabla y se agregan los resgistros, por lo que siempre estará la información de la última hora.

## Propuestas de Mejoras: 
* Ejecutar el proceso ETL con Airflow (la primera propuesta la estaba desarrollando con Airflow pero tuve un issue que no se podía conectar al Postgres, y probé varios cambios pero no pude solucionarlo)
* En el caso que se pueda ejecutar con Airlow, modularizar mejor la solución de manera que queden bien definidas las tareas que se van a ejecutar en el Dag.
* Renombrar los campos de los datasets para que se entienda mejor el significado del dato.
* Agregar Pruebas Unitarias.
* Guardar los archivos en la nube (buckets de S3 para las zonas de raw y stg)
* Valorar el uso de Spark dependiendo del volumen de datos y cuanto más se necesite procesar.
* Con respecto a la lógica, actualmente es posible que se esté almacenando mucha información repetida, ya que si el pronóstico para ciertos lugares no cambia con mucha frecuencia, sería la misma información por cada hora. 
En este caso se debería valorar con el equipo de DS si es más recomendable solamente agregar los valores que hayan cambiado, y mantener esta tabla como se hace con las dimensiones cambiantes de tipo 2 para los almacenes de datos, que se va llevando un registro histórico de los cambios.
* Agregar mayor manejo de excepciones.

## Propuestas para Escalar la Solución: 
* La propuesta para escalar sería definir toda la arquitectura en AWS, usando los servicios:
  - [AWS S3](https://aws.amazon.com/s3/): Como DataLake con las zonas definidas en la propuesta, o valorar si se requieren otras zonas
  - [AWS Glue Job](https://docs.aws.amazon.com/glue/latest/dg/add-job.html): para el ETl, o posibles nuevos ETLs, con PySpark o python, dependiendo del volumen de información
  - [AWS Athena](https://aws.amazon.com/athena/): para consultar la información del DataLake.
  - [AWS MWAA](https://aws.amazon.com/managed-workflows-for-apache-airflow/): para utilizar Airflow en AWS
  - [AWS RDS for Postgres](https://aws.amazon.com/rds/):  para la base de datos, o valorar el tipo de BD y servicio más apropiado.
  - También se puede valorar en dependencia de los nuevos requerimientos y procesos si sería necesario el diseño de un DWH, para lo cual propondría el uso de [Redshift](https://aws.amazon.com/redshift/).

## Cómo Ejecutar

1. Clonar el repositorio.
2. Ejecutar
```
        docker-compose up

```
3. El programa tiene definido que se ejecute a los 30 minutos de cada hora.
Si desea hacer una prueba inmediata, puede comentar el códido dentro de la condición
` if __name__ == "__main__" ` e invocar directamente a la función execute_etl()

### Problemas técnicos
- Antes de subir esta versión, tuve que probar diferentes variantes relacionadas al Docker-compose y Dockerfile por errores presentados a la hora de conectarse al postgres.
- En la versión que estoy subiendo está funcionando, pero en caso de presentar algún problema, garantice que tenga un postgres corriendo y actualice el archivo .env con los valores correctos

### Notas:
El archivo .env no se debe subir al repo pero lo dejé para propósitos de la prueba local 