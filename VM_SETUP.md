# AWS VM Initial Setup Guide

Complete setup instructions for your AWS Ubuntu VM at `13.201.12.40`.

## Step 1: Connect to AWS VM

```bash
# From your local machine
ssh -i ~/.ssh/gforms_deploy_nopass ubuntu@13.201.12.40
```

## Step 2: Check Your Username

```bash
# Find your actual username
whoami

# Note this down - you'll need it for GitHub Secrets
```

## Step 3: Install System Packages

```bash
# Update package list
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv git docker.io docker-compose

# Install pipenv
pip3 install pipenv --break-system-packages
```

## Step 4: Configure Docker Access

```bash
# Add your user to docker group (replace YOUR_USERNAME with output from 'whoami')
sudo usermod -aG docker YOUR_USERNAME

# Log out and back in for changes to take effect
exit

# SSH back in
ssh -i ~/.ssh/gforms_deploy_nopass ubuntu@13.201.12.40

# Verify docker works without sudo
docker ps
```

## Step 5: Generate SSH Key for GitHub (on AWS VM)

```bash
# Generate SSH key on the server
ssh-keygen -t ed25519 -C "aws-vm-gforms" -f ~/.ssh/github_deploy

# Press Enter for no passphrase (twice)

# Display public key
cat ~/.ssh/github_deploy.pub

# Copy this public key - you'll add it to GitHub
```

## Step 6: Add SSH Key to GitHub

**Option A: Deploy Key (Recommended for single repo)**

1. Go to your GitHub repo: https://github.com/DineshKingston/gforms
2. Settings → Deploy keys → Add deploy key
3. Title: `AWS VM - 13.201.12.40`
4. Key: Paste the output from `cat ~/.ssh/github_deploy.pub`
5. ✅ Check "Allow write access" (needed for git pull)
6. Click "Add key"

**Option B: Add to your GitHub account**

1. Go to GitHub → Settings (your profile) → SSH and GPG keys
2. New SSH key
3. Title: `AWS VM Deployment`
4. Key: Paste the output from `cat ~/.ssh/github_deploy.pub`
5. Add SSH key

## Step 7: Configure Git SSH on Server

```bash
# Create/edit SSH config
nano ~/.ssh/config
```

Add this content:

```
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_deploy
  IdentitiesOnly yes
```

Save and exit (Ctrl+X, Y, Enter), then:

```bash
# Set correct permissions
chmod 600 ~/.ssh/config

# Test GitHub connection
ssh -T git@github.com

# You should see: "Hi DineshKingston! You've successfully authenticated..."
```

## Step 8: Clone Repository Using SSH

```bash
# Navigate to home directory
cd ~

# Clone using SSH URL
git clone git@github.com:DineshKingston/gforms.git

# Navigate to project
cd gforms
```

## Step 9: Set Up Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env
```

Update these values in `.env`:

```env
SECRET_KEY=generate-a-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=13.201.12.40,your-domain.com

DEFAULT_DB_ENGINE=django.db.backends.postgresql
DEFAULT_DB_HOST=localhost
DEFAULT_DB_USER=postgres
DEFAULT_DB_PASSWORD=YOUR_STRONG_PASSWORD_HERE
DEFAULT_DB_NAME=gforms-db
DEFAULT_DB_PORT=5432
```

**Generate SECRET_KEY:**
```bash
pipenv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 10: Start Docker Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Check they're running
docker ps

# Create database
docker exec -it postgresql psql -U postgres -c "CREATE DATABASE \"gforms-db\";"
```

## Step 11: Set Up Django Application

```bash
# Install Python dependencies
pipenv install

# Run migrations
pipenv run python manage.py migrate

# Create superuser
pipenv run python manage.py createsuperuser

# Collect static files
pipenv run python manage.py collectstatic --noinput

# Create logs directory
mkdir -p logs
```

## Step 12: Configure Gunicorn Service

```bash
# Find your pipenv virtualenv path
pipenv --venv

# Note the path, you'll need it
```

Create systemd service:

```bash
sudo nano /etc/systemd/system/gunicorn-gforms.service
```

Add this content (replace paths with your actual values):

```ini
[Unit]
Description=Gunicorn daemon for Django gforms application
After=network.target

[Service]
Type=notify
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/gforms
Environment="PATH=/home/YOUR_USERNAME/.local/share/virtualenvs/gforms-XXXXXXXX/bin"
EnvironmentFile=/home/YOUR_USERNAME/gforms/.env
ExecStart=/home/YOUR_USERNAME/.local/share/virtualenvs/gforms-XXXXXXXX/bin/gunicorn \
          --workers 3 \
          --bind 0.0.0.0:8000 \
          --timeout 60 \
          --access-logfile /home/YOUR_USERNAME/gforms/logs/gunicorn-access.log \
          --error-logfile /home/YOUR_USERNAME/gforms/logs/gunicorn-error.log \
          forms.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn-gforms
sudo systemctl start gunicorn-gforms
sudo systemctl status gunicorn-gforms
```

## Step 13: Test Application

```bash
# Test locally
curl http://localhost:8000

# If you get HTML response, it's working!
```

## Step 14: Update GitHub Secrets

Go to GitHub → Settings → Secrets and variables → Actions

Add/Update these secrets:

| Secret Name | Value |
|-------------|-------|
| `AWS_HOST` | `13.201.12.40` |
| `AWS_USERNAME` | Output from `whoami` on server |
| `AWS_SSH_PRIVATE_KEY` | Content from `cat ~/.ssh/gforms_deploy_nopass` on LOCAL machine |
| `AWS_DEPLOY_PATH` | `/home/YOUR_USERNAME/gforms` |

## Step 15: Make Deploy Script Executable

```bash
# On the server
cd ~/gforms
chmod +x deploy.sh
```

## Step 16: Test Deployment

From your local machine:

```bash
# Make a small change and push
git commit --allow-empty -m "Test deployment"
git push origin main

# Watch in GitHub Actions tab
```

## Verification Checklist

- [ ] Username identified with `whoami`
- [ ] Docker installed and accessible without sudo
- [ ] SSH key generated on server and added to GitHub
- [ ] Repository cloned using SSH URL
- [ ] `.env` file created with production values
- [ ] Docker services running (PostgreSQL, Redis)
- [ ] Database created
- [ ] Django migrations applied
- [ ] Superuser created
- [ ] Gunicorn service running
- [ ] Application responds on port 8000
- [ ] GitHub Secrets configured
- [ ] `deploy.sh` is executable
- [ ] GitHub Actions deployment tested

## Troubleshooting

**Can't connect via SSH:**
```bash
# Check Security Group allows SSH from your IP
# AWS Console → EC2 → Security Groups → Inbound rules
```

**Docker permission denied:**
```bash
# Add user to docker group
sudo usermod -aG docker $(whoami)
# Log out and back in
```

**Git clone fails:**
```bash
# Test GitHub SSH connection
ssh -T git@github.com

# Check SSH config
cat ~/.ssh/config
```

**Gunicorn won't start:**
```bash
# Check logs
sudo journalctl -u gunicorn-gforms -n 50

# Check virtualenv path
pipenv --venv
```
