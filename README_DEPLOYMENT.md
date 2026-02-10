# GitHub Actions Deployment Configuration - Quick Reference

## Required GitHub Secrets

Add these secrets in your GitHub repository:
**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_HOST` | Your AWS VM's IP address or hostname | `54.123.45.67` |
| `AWS_USERNAME` | SSH username for the VM | `ubuntu` |
| `AWS_SSH_PRIVATE_KEY` | Complete SSH private key | Copy entire content from `~/.ssh/gforms_deploy` |
| `AWS_DEPLOY_PATH` | Full path to project directory on VM | `/home/ubuntu/gforms` |

## Quick Setup Steps

### 1. Generate SSH Key (Local Machine)
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/gforms_deploy
cat ~/.ssh/gforms_deploy.pub  # Copy this
```

### 2. Add Public Key to AWS VM
```bash
# On AWS VM
nano ~/.ssh/authorized_keys
# Paste the public key
```

### 3. Copy Private Key for GitHub Secret
```bash
# On Local Machine
cat ~/.ssh/gforms_deploy
# Copy ENTIRE content including headers for AWS_SSH_PRIVATE_KEY
```

### 4. Add Secrets to GitHub
1. Go to repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add all four secrets listed above

### 5. Verify Deployment
```bash
# Make a change and push
git add .
git commit -m "Test deployment"
git push origin main

# Watch deployment in GitHub Actions tab
```

## Files Created

- `.github/workflows/deploy.yml` - GitHub Actions workflow
- `deploy.sh` - Deployment script (runs on AWS VM)
- `DEPLOYMENT.md` - Complete deployment guide
- `.env.example` - Environment variables template

## Next Steps

See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Complete AWS VM setup instructions
- Gunicorn systemd service configuration
- Nginx setup
- Troubleshooting guide
