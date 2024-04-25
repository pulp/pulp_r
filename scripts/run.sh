
# Run postgres container
docker-compose up -d

# Create temp directory for the plugin
mkdir -p /var/lib/pulp/tmp

# Create Migrations
django-admin makemigrations

# Migrate
django-admin migrate

# Run Server
pulpcore-api