# Deployment Guide - AWS Ubuntu VM

This guide explains how to deploy the Django gforms application to an AWS Ubuntu VM using GitHub Actions.

## Table of Contents

- [Prerequisites](#prerequisites)
- [AWS VM Setup](#aws-vm-setup)
- [GitHub Configuration](#github-configuration)
- [Environment Variables](#environment-variables)
- [First Deployment](#first-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- AWS Ubuntu EC2 instance (Ubuntu 20.04 or later recommended)
- GitHub repository with the gforms project
- SSH access to the AWS VM
- Basic knowledge of Linux command line

## AWS VM Setup

### 1. Install Required System Packages

SSH into your AWS Ubuntu VM and run:

```bash
# Update package list
sudo apt update
sudo apt upgrade -y

# Install Python 3.12 and pip
sudo apt install -y python3.12 python3.12-venv python3-pip

# Install pipenv
pip3 install pipenv

# Install Git
sudo apt install -y git

# Install PostgreSQL client (if not using Docker)
sudo apt install -y postgresql-client

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker

# Add your user to docker group
sudo usermod -aG docker $USER
```

### 2. Clone the Repository

```bash
# Choose your deployment directory
cd /home/ubuntu  # or your preferred location

# Clone the repository
git clone https://github.com/YOUR_USERNAME/gforms.git
cd gforms
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
nano .env
```

Add the following content (adjust values as needed):

```env
# Django Settings
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-ip-address

# Database Configuration
DEFAULT_DB_ENGINE=django.db.backends.postgresql
DEFAULT_DB_HOST=localhost
DEFAULT_DB_USER=postgres
DEFAULT_DB_PASSWORD=postgres-password
DEFAULT_DB_NAME=gforms-db
DEFAULT_DB_PORT=5432
```

**Important**: Generate a secure SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Install Python Dependencies

```bash
pipenv install --deploy
```

### 5. Set Up Docker Services

Start PostgreSQL and Redis using Docker Compose:

```bash
docker-compose up -d
```

Create the database:

```bash
docker exec -it postgresql psql -U postgres -c "CREATE DATABASE \"gforms-db\";"
```

### 6. Run Initial Migrations

```bash
pipenv run python manage.py migrate
pipenv run python manage.py collectstatic --noinput

# Create a superuser
pipenv run python manage.py createsuperuser
```

### 7. Configure Gunicorn Systemd Service

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/gunicorn-gforms.service
```

Add the following content (adjust paths):

```ini
[Unit]
Description=Gunicorn daemon for Django gforms application
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/gforms
Environment="PATH=/home/ubuntu/.local/share/virtualenvs/gforms-XXXXXXXX/bin"
EnvironmentFile=/home/ubuntu/gforms/.env
ExecStart=/home/ubuntu/.local/share/virtualenvs/gforms-XXXXXXXX/bin/gunicorn \
          --workers 3 \
          --bind 0.0.0.0:8000 \
          --timeout 60 \
          --access-logfile /home/ubuntu/gforms/logs/gunicorn-access.log \
          --error-logfile /home/ubuntu/gforms/logs/gunicorn-error.log \
          forms.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Find your virtualenv path**:
```bash
pipenv --venv
```

Create logs directory:
```bash
mkdir -p logs
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn-gforms
sudo systemctl start gunicorn-gforms
sudo systemctl status gunicorn-gforms
```

### 8. Configure Nginx (Optional but Recommended)

Install Nginx:

```bash
sudo apt install -y nginx
```

Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/gforms
```

Add:

```nginx
server {
    listen 80;
    server_name your-domain.com your-ip-address;

    client_max_body_size 20M;

    location /static/ {
        alias /home/ubuntu/gforms/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/gforms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## GitHub Configuration

### 1. Generate SSH Key Pair

On your **local machine**:

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/gforms_deploy
```

### 2. Add Public Key to AWS VM

Copy the public key:

```bash
cat ~/.ssh/gforms_deploy.pub
```

On the **AWS VM**, add it to authorized_keys:

```bash
nano ~/.ssh/authorized_keys
# Paste the public key on a new line
```

### 3. Add GitHub Secrets

Go to your GitHub repository: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `AWS_HOST` | Your VM's IP or hostname | `54.123.45.67` or `ec2-54-123-45-67.compute-1.amazonaws.com` |
| `AWS_USERNAME` | SSH username | `ubuntu` |
| `AWS_SSH_PRIVATE_KEY` | Private key content | Copy from `~/.ssh/gforms_deploy` (entire content including headers) |
| `AWS_DEPLOY_PATH` | Deployment directory path | `/home/ubuntu/gforms` |

**Copy private key**:
```bash
cat ~/.ssh/gforms_deploy
```

Copy the **entire content** including the `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----` lines.

## Environment Variables

Update `forms/settings.py` to use environment variables:

```python
import os
from pathlib import Path

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
```

## First Deployment

### Manual First Deployment

Before using GitHub Actions, verify everything works:

```bash
# On AWS VM
cd /home/ubuntu/gforms
bash deploy.sh
```

### Automated Deployment

Once manual deployment works:

1. Make any change to your code
2. Commit and push to the `main` branch:
   ```bash
   git add .
   git commit -m "Test deployment"
   git push origin main
   ```
3. Go to GitHub → **Actions** tab
4. Watch the deployment workflow run
5. Verify the application is updated

### Manual Trigger

You can also trigger deployment manually from GitHub:

1. Go to **Actions** tab
2. Click on "Deploy to AWS Ubuntu VM" workflow
3. Click "Run workflow" button
4. Select branch and run

## Troubleshooting

### Deployment Failed - SSH Connection

**Issue**: GitHub Actions can't connect to AWS VM

**Solutions**:
- Verify AWS Security Group allows SSH (port 22) from GitHub Actions IPs
- Check `AWS_SSH_PRIVATE_KEY` secret is the complete private key
- Verify public key is in `~/.ssh/authorized_keys` on VM
- Test SSH locally: `ssh -i ~/.ssh/gforms_deploy ubuntu@YOUR_VM_IP`

### Gunicorn Service Not Found

**Issue**: `systemctl is-active --quiet gunicorn-gforms` fails

**Solutions**:
- Verify systemd service is created and enabled
- Check service status: `sudo systemctl status gunicorn-gforms`
- View logs: `sudo journalctl -u gunicorn-gforms -n 50`

### Database Connection Error

**Issue**: Can't connect to PostgreSQL

**Solutions**:
- Check Docker containers: `docker-compose ps`
- Verify database exists: `docker exec -it postgresql psql -U postgres -l`
- Check environment variables in `.env` file
- View PostgreSQL logs: `docker logs postgresql`

### Static Files Not Loading

**Issue**: CSS/JS not loading on the website

**Solutions**:
- Run: `pipenv run python manage.py collectstatic --noinput`
- Check Nginx configuration for `/static/` location
- Verify `STATIC_ROOT` in settings.py
- Check file permissions: `ls -la staticfiles/`

### Migration Errors

**Issue**: `python manage.py migrate` fails

**Solutions**:
- Check database connection
- View migration status: `pipenv run python manage.py showmigrations`
- Try fake migration: `pipenv run python manage.py migrate --fake`

### Permission Denied Errors

**Issue**: Script can't restart services or access files

**Solutions**:
- Make deploy.sh executable: `chmod +x deploy.sh`
- Add user to docker group: `sudo usermod -aG docker ubuntu`
- Configure sudo for systemctl: `sudo visudo` and add:
  ```
  ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart gunicorn-gforms
  ```

### View Application Logs

```bash
# Gunicorn logs
tail -f logs/gunicorn-error.log
tail -f logs/gunicorn-access.log

# Systemd service logs
sudo journalctl -u gunicorn-gforms -f

# Docker logs
docker logs postgresql
docker logs redis

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Useful Commands

```bash
# Check deployment script
bash deploy.sh

# Restart services manually
sudo systemctl restart gunicorn-gforms
sudo systemctl restart nginx
docker-compose restart

# View running processes
ps aux | grep gunicorn
docker ps

# Test application
curl http://localhost:8000
curl http://your-domain.com
```

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use strong SECRET_KEY** - Generate with Django utility
3. **Set DEBUG=False** in production
4. **Configure ALLOWED_HOSTS** properly
5. **Use HTTPS** - Set up SSL/TLS with Let's Encrypt
6. **Restrict SSH access** - Use AWS Security Groups
7. **Regular updates** - Keep system packages updated
8. **Database backups** - Set up automated backups

## Next Steps

- [ ] Set up SSL/TLS with Let's Encrypt (Certbot)
- [ ] Configure database backups
- [ ] Set up monitoring and logging (e.g., Sentry)
- [ ] Configure email backend for production
- [ ] Set up CDN for static files (optional)
- [ ] Implement health check endpoints
