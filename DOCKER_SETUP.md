# Docker + AWS ECR Setup Guide

Complete guide for setting up Docker deployment with AWS ECR for the gforms Django application.

## Prerequisites

- AWS Account
- AWS CLI installed locally
- Docker installed locally (for testing)
- GitHub repository with admin access

## Part 1: AWS ECR Setup

### Step 1: Create ECR Repository

**Via AWS Console:**

1. Go to AWS Console → ECR (Elastic Container Registry)
2. Click "Create repository"
3. Repository settings:
   - **Visibility**: Private
   - **Repository name**: `gforms`
   - **Tag immutability**: Disabled (for now)
   - **Scan on push**: Enabled (recommended)
   - **Encryption**: AES-256 (default)
4. Click "Create repository"
5. **Note the repository URI**: `<account-id>.dkr.ecr.<region>.amazonaws.com/gforms`

**Via AWS CLI:**

```bash
aws ecr create-repository \
    --repository-name gforms \
    --region ap-south-1 \
    --image-scanning-configuration scanOnPush=true
```

### Step 2: Create IAM User for GitHub Actions

**Via AWS Console:**

1. Go to IAM → Users → Create user
2. User name: `github-actions-gforms`
3. **Attach policies directly**:
   - `AmazonEC2ContainerRegistryPowerUser` (or create custom policy below)
4. Click "Create user"
5. Go to user → Security credentials → Create access key
6. Use case: "Application running outside AWS"
7. **Save Access Key ID and Secret Access Key** (you'll need these for GitHub Secrets)

**Custom IAM Policy (More Restrictive):**

If you want minimal permissions, create a custom policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:GetRepositoryPolicy",
                "ecr:DescribeRepositories",
                "ecr:ListImages",
                "ecr:DescribeImages",
                "ecr:BatchGetImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:PutImage"
            ],
            "Resource": "arn:aws:ecr:ap-south-1:ACCOUNT_ID:repository/gforms"
        }
    ]
}
```

### Step 3: Configure AWS CLI on EC2 Instance

SSH to your EC2 instance:

```bash
ssh -i ~/.ssh/gforms_deploy_nopass ubuntu@13.201.12.40
```

Install AWS CLI (if not installed):

```bash
# Check if installed
aws --version

# If not installed:
sudo apt update
sudo apt install -y awscli

# Or install latest version:
curl "https://aw scli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt install unzip
unzip awscliv2.zip
sudo ./aws/install
```

Configure AWS credentials:

```bash
aws configure

# Enter when prompted:
AWS Access Key ID: <your-access-key-id>
AWS Secret Access Key: <your-secret-access-key>
Default region name: ap-south-1
Default output format: json
```

Test ECR access:

```bash
aws ecr describe-repositories --region ap-south-1
```

## Part 2: GitHub Secrets Configuration

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `AWS_ACCESS_KEY_ID` | IAM user access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | `wJalrXUtnFEMI/K7MDENG/...` |
| `AWS_REGION` | AWS region | `ap-south-1` |
| `ECR_REPOSITORY` | Repository name | `gforms` |
| `AWS_HOST` | EC2 IP address | `13.201.12.40` (already set) |
| `AWS_USERNAME` | EC2 SSH username | `ubuntu` (already set) |
| `AWS_SSH_PRIVATE_KEY` | SSH private key | (already set) |
| `AWS_DEPLOY_PATH` | Deployment path | `/home/ubuntu/gforms` (already set) |

**Total: 8 secrets** (4 new + 4 existing)

## Part 3: Server Preparation

### Step 1: Update .env File on Server

SSH to server and edit .env:

```bash
ssh -i ~/.ssh/gforms_deploy_nopass ubuntu@13.201.12.40
cd ~/gforms
nano .env
```

Add these lines:

```env
# Docker Configuration
DOCKER_IMAGE_TAG=latest
ECR_REGISTRY=ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com
ECR_REPOSITORY=gforms
AWS_REGION=ap-south-1
```

Replace `ACCOUNT_ID` with your actual AWS account ID.

### Step 2: Stop Current Gunicorn Service

```bash
# Check if running
sudo systemctl status gunicorn

# Stop the service
sudo systemctl stop gunicorn

# Disable from starting on boot (we'll use Docker instead)
sudo systemctl disable gunicorn
```

### Step 3: Make Deployment Script Executable

```bash
chmod +x docker-deploy.sh
```

## Part 4: Local Testing

Before pushing to production, test Docker build locally:

```bash
# On your local machine
cd ~/gforms

# Build Docker image
docker build -t gforms:test .

# Check if build succeeded
docker images | grep gforms

# Test run (optional)
docker run -p 8000:8000 --env-file .env gforms:test
```

## Part 5: First Deployment

### Manual First Deployment

1. **Commit and push Docker files:**

```bash
git add .
git commit -m "Add Docker and ECR deployment configuration"
git push origin main
```

2. **Watch GitHub Actions:**
   - Go to repository → Actions tab
   - Watch the workflow build and push image to ECR
   - It will fail on deployment initially (that's okay)

3. **Manual deployment on server:**

```bash
ssh -i ~/.ssh/gforms_deploy_nopass ubuntu@13.201.12.40
cd ~/gforms

# Pull latest code
git pull origin main

# Run Docker deployment manually first time
bash docker-deploy.sh
```

4. **Check if services are running:**

```bash
docker-compose -f docker-compose.prod.yml ps

# Should see:
# - gforms-django
# - gforms-postgres
# - gforms-redis
# - gforms-nginx
```

5. **Test application:**

```bash
curl http://localhost/health/

# Or open in browser:
# http://13.201.12.40
```

## Part 6: Verification

### Check Docker Containers

```bash
# List running containers
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs django
docker-compose -f docker-compose.prod.yml logs nginx
docker-compose -f docker-compose.prod.yml logs postgresql

# Check specific container
docker logs gforms-django
```

### Check ECR Images

```bash
# List images in ECR
aws ecr list-images --repository-name gforms --region ap-south-1

# Describe images
aws ecr describe-images --repository-name gforms --region ap-south-1
```

### Application Health

```bash
# Test endpoints
curl http://localhost/health/
curl http://localhost/admin/

# Check from outside
curl http://13.201.12.40/admin/
```

## Part 7: Monitoring and Maintenance

### View Logs

```bash
# Real-time logs for all services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f django

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 django
```

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart django
```

### Update Application

Simply push to main branch:

```bash
git add .
git commit -m "Update feature X"
git push origin main

# GitHub Actions will:
# 1. Build new Docker image
# 2. Push to ECR
# 3. Deploy to EC2 automatically
```

### Rollback to Previous Version

```bash
# SSH to server
ssh -i ~/.ssh/gforms_deploy_nopass ubuntu@13.201.12.40
cd ~/gforms

# List available images
aws ecr list-images --repository-name gforms --region ap-south-1

# Update .env with specific tag
nano .env
# Change: DOCKER_IMAGE_TAG=<commit-sha>

# Redeploy
bash docker-deploy.sh
```

## Troubleshooting

### Issue: ECR Login Failed

```bash
# Test ECR login manually
aws ecr get-login-password --region ap-south-1 | \
    docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com

# Check AWS credentials
aws sts get-caller-identity
```

### Issue: Container Won't Start

```bash
# Check logs
docker logs gforms-django

# Check container status
docker inspect gforms-django

# Try running manually
docker run -it --env-file .env ECR_REGISTRY/gforms:latest bash
```

### Issue: Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check network
docker network ls
docker network inspect gforms_gforms-network

# Test connection from Django container
docker exec -it gforms-django bash
apt-get update && apt-get install -y postgresql-client
psql -h postgresql -U postgres -d gforms-db
```

### Issue: Static Files Not Loading

```bash
# Check static volume
docker volume inspect gforms_static_volume

# Recollect static files
docker-compose -f docker-compose.prod.yml run --rm django python manage.py collectstatic --noinput

# Check nginx configuration
docker exec -it gforms-nginx cat /etc/nginx/conf.d/gforms.conf
```

## Cost Estimates

- **ECR Storage**: ~$0.10/GB/month (first 500MB free for 12 months)
- **ECR Data Transfer**: Minimal (within same region)
- **Typical Django app**: ~500MB-1GB for images = ~$0.05-0.10/month

Very affordable! 💰

## Security Best Practices

✅ **Implemented:**
- Private ECR repository
- IAM user with minimal permissions
- Docker runs as non-root user
- Multi-stage builds for smaller images
- Health checks on all containers

⚠️ **Recommended:**
- [ ] Enable ECR image scanning
- [ ] Set up ECR lifecycle policies (clean up old images)
- [ ] Use AWS Secrets Manager for sensitive data
- [ ] Implement container resource limits
- [ ] Set up CloudWatch logs for containers

## Next Steps

Once Docker/ECR is working:

1. **SSL/TLS**: Add HTTPS with Let's Encrypt
2. **Monitoring**: Set up container health monitoring
3. **Auto-scaling**: Move to ECS/EKS for auto-scaling
4. **CI/CD**: Add testing step before deployment
5. **Backups**: Automated database backups

Your Docker +ECR deployment is now complete! 🎉
