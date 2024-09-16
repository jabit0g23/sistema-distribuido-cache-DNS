
# Sistema Distribuido de Cache DNS

Este proyecto implementa un sistema distribuido de caché para solicitudes DNS, utilizando Redis y particionamiento distribuido. Siga los pasos a continuación para clonar, configurar y ejecutar el programa.

**[Ver video de implementación]()**

## Instalación y Configuración

### 1. Clonar el Repositorio

Primero, clona el repositorio desde GitHub:

```bash
git clone git@github.com:jabit0g23/sistema-distribuido-cache-DNS.git
```

### 2. Instalar Dependencias

Navega a la carpeta del repositorio clonado:

```bash
cd sistema-distribuido-cache-DNS
```

Asegúrate de tener instaladas las librerías necesarias para la correcta ejecución del programa:

```bash
pip install requests
pip install matplotlib
```

### 3. Modificar Parámetros del Programa

El programa está listo para ejecutarse, pero puedes modificar algunos parámetros según tus necesidades:

- **Cambiar entre Hash y Range**: Ve a `app.py` y modifica la variable de entorno `PARTITION_TYPE`. Cambia el valor entre `"hash"` y `"range"` según lo que desees usar.
- **Usar diferentes políticas de remoción y cambiar el número de particiones**: En el directorio encontrarás dos carpetas llamadas `docker-compose-allkeys-random` y `docker-compose-volatile-lru`. En cada una de estas carpetas, encontrarás archivos `.yml` con diferentes configuraciones. Copia el contenido del archivo que desees y pégalo en `docker-compose.yml`.
- **Cambiar el número de solicitudes**: Ve a `send_requests.py` y modifica el tamaño de la muestra (máximo 50000) y el número de solicitudes en la función `main`.

### 4. Ejecutar el Programa

Una vez que hayas configurado todo según tus preferencias, ejecuta el siguiente comando:

```bash
docker-compose up --build
```

Esto iniciará los servicios de Redis, la API y el servidor gRPC. Finalmente, ejecuta `send_requests.py` para realizar las solicitudes y generar los gráficos automáticamente.
