
# Run postgres container
docker-compose up -d

# Create temp directory for the plugin
mkdir -p /var/lib/pulp/tmp

export DJANGO_SETTINGS_MODULE=pulp_r.app.settings
# Create Migrations
django-admin makemigrations

# Migrate
django-admin migrate

# Run Server
pulpcore-api