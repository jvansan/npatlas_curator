# NP Atlas Curator (v3) WEB APP EDITION


### Note

*Requires an Anaconda or Miniconda Python distribution in order to
install RDKit.*

### Docker Deployment

The app has been configured to run using Docker with three containers:

In theory, these should be able to be started using docker-compose:

**NOTE** The docker-compose.yml is sorely out of date.

```
docker-compose build
docker-compose up
```

Various sources have recommended not deploying in this manner.

For simplicity, I suggest `docker build` and `docker run`

1) *Data volume*

This is a non-running volume which store the data persistently.
Be careful with this and make backups. This can later be mounted to save data.

```
docker volume create mysql-data
```


```
docker exec mysql bash -c 'mysqldump -uroot -p$MYSQL_ROOT_PASSWORD --all-databases > /var/dumps/all.sql'
```

2) *MySQL Container*

Set the environment variables inside `mysql-container/Dockerfile`.

```
docker run --name mysql -p 3306:3306 -v mysql-data:/var/lib/mysql \
-v $(pwd)/mysql-dumps:/var/dumps -d -e MYSQL_DATABASE=npatlas_curation \
-e MYSQL_USER=<DB_USER> -e MYSQL_PASSWORD=<DB_PASSWORD> \
-e MYSQL_ROOT_PASSWORD=<ROOT_PASSWORD> mysql/mysql-server:5.7 \
--character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

3) *Redis Container*

The "Checker" portion of the curator app requires a Redis messaging queue
in order to run the Celery tasks. This server can be started by running:

```
docker run --name redis --restart always -d redis
```

If you do the following, redis will stop trying to backup redis info. This
is fine because there are no necessary persistent data on the redis db.
From redis-cli:

```
config set stop-writes-on-bgsave-error no
```

4) *Flask/uWSGI Container*

This container will run the Curator Flask app with a uWSGI server.
You can set the `DBSERVER` environment variable, or else it will default
to `localhost`.

Make sure to have a matching `instance/config.py` with the appropriate
`DBSERVER`, `DB_USER`, `DB_PASSWORD`, and an app `SECRET_KEY`

**ADDING DATA**

If you want to pass as dump file to MySQL, I suggest copying it to the main
directory of this project. Docker with then copy it and allow you to use
`flask db upgrade` followed by reading the appropriate  `dump.sql`.

```
docker exec -it curator bash
source activate curator && flask db upgrade
mysql -u<DB_USER> -p<DB_PASSWORD> -h<DBSERVER> npatlas_curation < dump.sql
```

```
docker build -t curator:latest -t curator:<VERSION> .
docker run --name curator -v $(pwd):/curator --restart always\
--link mysql:dbserver --link redis:redis \
--log-opt max-size=5m --log-opt max-file=10 \
-e DBSERVER=dbserver -e REDIS=redis -d curator:latest 
```

5) *Nginx Container*

I have created a simple custom Dockerfile to simplify deployment.
You can set the `SERVER_NAME` environment variable during build time,
or else it will default to `localhost`. In development you may wish to use
a self signed certificate in place of a letsencrypt one.

```
docker build -t my-nginx:latest -t my-nginx:<VERSION> \
--build-arg SERVER_NAME=<SERVER_NAME> ./my-nginx-container
docker run --name nginx -v /etc/letsencrypt:/etc/letsencrypt \
--link curator -d -p 80:80 -p 443:443 my-nginx:latest
```

6) *Celery Container*

```
docker build -f Dockerfile.celery -t curator-celery:latest .
docker run --name celery -v $(pwd):/curator --link mysql:dbserver \
--link redis:redis -e DBSERVER=dbserver -e REDIS=redis \
--log-opt max-size=5m --log-opt max-file=10 \
--restrt always -d curator-celery:latest
```
