# 🔐 API Key Security Guide

## ⚠️ URGENT: Your API Key Was Leaked!

Your Gemini API key was reported as leaked to GitHub, which is why it's now blocked.

---

## 🚨 Immediate Actions Required

### 1. Get a New API Key

**For Google Gemini:**
1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"** or **"Get API Key"**
4. Copy the new key (starts with `AIzaSy...`)
5. **IMPORTANT:** Enable domain restrictions if available:
   - Restrict to your server's IP address
   - Or restrict to specific HTTP referrers

**For DeepSeek (optional):**
1. Go to: https://platform.deepseek.com/
2. Sign in and navigate to API Keys
3. Create a new key
4. Copy it securely

### 2. Update Your .env File

```bash
# Navigate to the chatbot directory
cd albaqer_chatbot

# Edit the .env file (DO NOT use .env.example)
notepad .env  # or use your preferred editor
```

Replace the old keys:
```env
GEMINI_API_KEY=AIzaSy-YOUR-NEW-KEY-HERE
DEEPSEEK_API_KEY=sk-YOUR-NEW-KEY-HERE
```

### 3. Verify .env is Ignored

```bash
# Check if .env is in .gitignore
git check-ignore albaqer_chatbot/.env

# Should output: albaqer_chatbot/.env
# If it doesn't, add it to .gitignore
```

### 4. Remove .env from Git History (if it was committed)

**⚠️ This rewrites history - coordinate with your team!**

```bash
# Check if .env is in git history
git log --oneline --all -- albaqer_chatbot/.env

# If it shows commits, remove it from history:
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch albaqer_chatbot/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push to GitHub (DANGEROUS - make sure team is aware)
git push origin --force --all
git push origin --force --tags
```

**Alternative (Safer):** Use BFG Repo-Cleaner:
```bash
# Download BFG from: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
```

---

## 🛡️ Best Practices to Prevent Future Leaks

### 1. Always Use .gitignore

Your `.gitignore` should include:
```gitignore
.env
.env.local
.env.*.local
*.env
```

### 2. Use .env.example as Template

- ✅ Commit: `.env.example` (with placeholder values)
- ❌ Never commit: `.env` (with real values)

### 3. Use Git Hooks (Pre-commit)

Install pre-commit hooks to prevent committing secrets:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
      - id: detect-private-key
  
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
EOF

# Install the hooks
pre-commit install
```

### 4. Use GitHub Secret Scanning Alerts

1. Go to: https://github.com/YOUR_USERNAME/ecommerce_albaqer/settings/security_analysis
2. Enable **"Secret scanning"**
3. Enable **"Push protection"** (prevents pushing secrets)

### 5. Use Environment Variables in Production

For deployment, use proper secret management:

**Heroku:**
```bash
heroku config:set GEMINI_API_KEY=your-key-here
```

**Docker:**
```bash
docker run -e GEMINI_API_KEY=your-key-here your-app
```

**Cloud Platforms (AWS/GCP/Azure):**
- Use AWS Secrets Manager
- Use GCP Secret Manager
- Use Azure Key Vault

### 6. Rotate Keys Regularly

- Change API keys every 3-6 months
- Immediately rotate if a key is suspected to be compromised
- Use separate keys for dev/staging/production

### 7. Use API Key Restrictions

**Google Cloud Console:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Find your API key
3. Click **"Edit"**
4. Add restrictions:
   - **Application restrictions:** HTTP referrers or IP addresses
   - **API restrictions:** Only enable "Generative Language API"

---

## 🔍 Check for Leaked Secrets

### 1. Scan Your Repository

```bash
# Using gitleaks
docker run -v $(pwd):/path zricethezav/gitleaks:latest detect --source="/path"

# Using trufflehog
docker run --rm -v $(pwd):/repo trufflesecurity/trufflehog:latest filesystem /repo
```

### 2. Check GitHub

1. Go to: https://github.com/YOUR_USERNAME/ecommerce_albaqer/security
2. Check for any alerts
3. Review **"Dependabot alerts"** and **"Secret scanning alerts"**

---

## 📝 Emergency Checklist

- [ ] Revoke the old leaked API key (if possible)
- [ ] Create a new API key with restrictions
- [ ] Update `.env` with the new key
- [ ] Verify `.env` is in `.gitignore`
- [ ] Check if `.env` is in git history
- [ ] Remove `.env` from git history if needed
- [ ] Force push cleaned history to GitHub
- [ ] Notify team members about the change
- [ ] Test that the application works with new key
- [ ] Set up git hooks to prevent future leaks
- [ ] Enable GitHub secret scanning
- [ ] Rotate other potentially compromised keys

---

## 🧪 Test Your Setup

```bash
# 1. Verify .env is ignored
git status | grep -i "\.env"
# Should NOT show .env file

# 2. Try to add .env (should fail if .gitignore works)
git add albaqer_chatbot/.env
# Should show: The following paths are ignored by one of your .gitignore files

# 3. Test the API key works
cd albaqer_chatbot
python -c "from config.settings import GEMINI_API_KEY; print('Key loaded:', GEMINI_API_KEY[:10] + '...')"
```

---

## 📚 Additional Resources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Google API Key Best Practices](https://cloud.google.com/docs/authentication/api-keys)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Git Remove Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)

---

## 💡 Quick Summary

1. **Get new API key** from Google AI Studio
2. **Update `.env`** with new key
3. **Never commit `.env`** to git
4. **Use `.env.example`** for templates
5. **Enable GitHub secret scanning**
6. **Set up pre-commit hooks**
7. **Test everything works**

---

**Remember:** Treat API keys like passwords. Never share them, never commit them, and rotate them regularly!
