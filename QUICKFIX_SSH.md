# SSH Key Error Fix - Passphrase Protected Key

## Problem
GitHub Actions error: `ssh: this private key is passphrase protected`

## Solution: Generate Passphrase-Free SSH Key

### Step 1: Generate New SSH Key (WITHOUT Passphrase)

```bash
# Generate key without passphrase (just press Enter when asked for passphrase)
ssh-keygen -t ed25519 -C "github-actions-gforms" -f ~/.ssh/gforms_deploy_nopass

# When prompted: "Enter passphrase (empty for no passphrase):"
# Just press ENTER twice (leave passphrase empty)
```

### Step 2: Copy Public Key to AWS VM

```bash
# Display public key
cat ~/.ssh/gforms_deploy_nopass.pub

# Copy the output, then SSH to your AWS VM and add it
ssh ubuntu@YOUR_AWS_IP

# On AWS VM, add the public key
nano ~/.ssh/authorized_keys
# Paste the public key on a new line, save and exit
```

### Step 3: Update GitHub Secret

```bash
# Display private key (on local machine)
cat ~/.ssh/gforms_deploy_nopass

# Copy the ENTIRE output including:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ... (all the lines)
# -----END OPENSSH PRIVATE KEY-----
```

**Update GitHub Secret:**
1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Find `AWS_SSH_PRIVATE_KEY` secret
4. Click the pencil icon to edit
5. Replace with the new private key content
6. Click "Update secret"

### Step 4: Test the Connection

```bash
# Test SSH connection with the new key
ssh -i ~/.ssh/gforms_deploy_nopass ubuntu@YOUR_AWS_IP

# If it connects without asking for a passphrase, you're good!
```

### Step 5: Trigger Deployment Again

Push a commit or manually trigger the workflow:

```bash
git commit --allow-empty -m "Test deployment with new SSH key"
git push origin main
```

## Alternative: Use Passphrase in Workflow (Not Recommended)

If you want to keep the passphrase-protected key, update the workflow:

```yaml
- name: Deploy to AWS VM
  uses: appleboy/ssh-action@v1.0.3
  with:
    host: ${{ secrets.AWS_HOST }}
    username: ${{ secrets.AWS_USERNAME }}
    key: ${{ secrets.AWS_SSH_PRIVATE_KEY }}
    passphrase: ${{ secrets.AWS_SSH_PASSPHRASE }}  # Add this line
    port: 22
    script: |
      ...
```

Then add a new GitHub Secret `AWS_SSH_PASSPHRASE` with your passphrase value.

**However, using a passphrase-free key is simpler and the recommended approach for CI/CD.**
