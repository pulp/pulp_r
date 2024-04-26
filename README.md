# pulp-r

A Pulp plugin to support hosting your own r.

## Installation

Create virtual environment and run `pip install -r requirements.txt`

Create your DB_ENCRYPTION_KEY fir pulp

```bash
mkdir -p /etc/pulp/certs
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | sudo tee /etc/pulp/certs/database_fields.symmetric.key > /dev/null
sudo chmod 600 /etc/pulp/certs/database_fields.symmetric.key
```
Figure out the user/group you are running the django-admin command as.  This is the user that will own the key file.

```bash
ps aux | grep manage.py 
```

Change the ownership of the encryption key file to the user running the Django application
    
```bash
sudo chown <user>:<group> /etc/pulp/certs/database_fields.symmetric.key
```

Verify that the user running the Django application has read access to the encryption key file:
    
```bash
sudo chmod 400 /etc/pulp/certs/database_fields.symmetric.key
```
Create temp directory for the plugin

```bash
mkdir -p /var/lib/pulp/tmp
```


Run postgres container

```bash
docker-compose up -d
```

Create Migrations

```bash
django-admin makemigrations
```

Migrate

```bash
django-admin migrate
```

Run Server
    
```bash
pulpcore-api
```

Client
```bash
python scripts/query_server.py 
```

