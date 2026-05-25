# 📤 Push to GitHub - Step-by-Step Guide

**Current Location:** `C:\MyFiles\DOCUMENT-2026\2026\May2026\behavioriq_V2`  
**Time to Complete:** 5-10 minutes  
**Result:** GitHub URL ready for submission

---

## ✅ STEP 1: Create GitHub Account (If You Don't Have One)

### Option A: If You Already Have GitHub Account
→ Skip to **STEP 2**

### Option B: If You Need a New Account
1. Go to https://github.com
2. Click "Sign up"
3. Enter your email
4. Create password
5. Choose username (remember this!)
6. Verify email
7. Done ✅

**Note:** Username appears in your GitHub URL like: `https://github.com/[USERNAME]/repo`

---

## ✅ STEP 2: Create GitHub Repository

### Via Web Browser (Easiest)

1. Go to https://github.com/new
2. Fill in:
   - **Repository name:** `behavioriq_V2`
   - **Description:** `BehaviorIQ: AI-Powered Food Review & Recommendation System - DSN X BCT Challenge 2026`
   - **Visibility:** `Public` (judges need to see it)
   - **.gitignore:** Skip (we'll do this manually)
   - **License:** MIT (optional)
3. Click "Create repository"
4. **COPY the URL** shown (looks like: `https://github.com/[USERNAME]/behavioriq_V2.git`)
5. Keep this page open

---

## ✅ STEP 3: Initialize Git Locally

Open PowerShell in your project folder and run these commands:

```powershell
# Navigate to your project
cd c:\MyFiles\DOCUMENT-2026\2026\May2026\behavioriq_V2

# Initialize git
git init

# Set your name (use your real name)
git config user.name "Your Name"

# Set your email (use your GitHub email)
git config user.email "your.email@gmail.com"
```

---

## ✅ STEP 4: Create .gitignore File

This prevents pushing sensitive files (API keys, large data files, cache).

Run this command to create `.gitignore`:

```powershell
# Create .gitignore file
@"
# Environment variables
.env

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environment
venv/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data files (too large for GitHub)
*.csv
data/*.csv

# Cache files
*.cache
.pytest_cache/
.streamlit/

# OS files
.DS_Store
Thumbs.db

# Logs
*.log

# Compiled files
*.egg-info/
dist/
build/

# Large files
chroma_db/
*.json
"@ | Out-File -Encoding UTF8 ".gitignore"
```

---

## ✅ STEP 5: Add All Files to Git

```powershell
# Add all files (except those in .gitignore)
git add .

# Check what will be committed
git status
```

**Expected output:** Should show many files ready to be committed (but not `.env`, `.csv`, `__pycache__`, etc.)

---

## ✅ STEP 6: Make First Commit

```powershell
# Commit all files with a message
git commit -m "Initial commit: BehaviorIQ - DSN X BCT Challenge submission"
```

---

## ✅ STEP 7: Connect to GitHub

```powershell
# Add GitHub repository as remote (replace URL from Step 2)
git remote add origin https://github.com/[YOUR-USERNAME]/behavioriq_V2.git

# Rename branch to main (GitHub default)
git branch -M main
```

---

## ✅ STEP 8: Push to GitHub

```powershell
# Push all files to GitHub
git push -u origin main
```

**If prompted:** 
- Username: Your GitHub username
- Password: Your GitHub personal access token (see note below)

### If Authentication Fails:

You might need a **Personal Access Token** instead of your password.

1. Go to https://github.com/settings/tokens/new
2. Check `repo` scope
3. Generate token
4. Copy the token
5. Use token as password when pushing

---

## ✅ STEP 9: Verify on GitHub

1. Go to https://github.com/[YOUR-USERNAME]/behavioriq_V2
2. You should see all your files!
3. Copy this URL for submission

---

## 📋 COMPLETE COMMAND SEQUENCE (Copy & Paste)

Here's everything at once (just replace `YOUR-NAME` and `YOUR-EMAIL`):

```powershell
# Navigate to project
cd c:\MyFiles\DOCUMENT-2026\2026\May2026\behavioriq_V2

# Initialize git
git init
git config user.name "Your Name"
git config user.email "your.email@gmail.com"

# Create .gitignore (paste the content from Step 4 above)
# Then run:

# Add all files
git add .

# Check status
git status

# Commit
git commit -m "Initial commit: BehaviorIQ - DSN X BCT Challenge submission"

# Add remote (replace with YOUR URL from GitHub step 2)
git remote add origin https://github.com/YOUR-USERNAME/behavioriq_V2.git

# Rename branch
git branch -M main

# Push
git push -u origin main
```

---

## ✅ TROUBLESHOOTING

### Error: "fatal: not a git repository"
→ Make sure you ran `git init` first

### Error: "fatal: could not read Username"
→ You need a Personal Access Token (see Step 8 note above)

### Error: "fatal: remote origin already exists"
→ You might have already done this. Check with: `git remote -v`

### Error: ".env file not committed"
→ Good! That's what we want. Check your `.gitignore` is working correctly.

### Slow push (large files)
→ Make sure `.csv` and `data/` folders are in `.gitignore`

---

## 🎯 FINAL RESULT

After pushing, you'll have:

✅ GitHub repository: `https://github.com/[YOUR-USERNAME]/behavioriq_V2`

✅ All your code visible to judges

✅ README.md showing system overview

✅ All documentation in root folder

✅ Dockerfile and deployment config visible

---

## 📝 FOR YOUR SUBMISSION FORM

When filling the submission form, paste:
```
https://github.com/[YOUR-USERNAME]/behavioriq_V2
```

Replace `[YOUR-USERNAME]` with your actual GitHub username.

---

## ⚡ QUICK VERSION (If you know Git)

```bash
cd behavioriq_V2
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
git add .
git commit -m "Initial commit: BehaviorIQ submission"
git remote add origin https://github.com/[USERNAME]/behavioriq_V2.git
git branch -M main
git push -u origin main
```

---

**Status:** ✅ Ready to push  
**Time Needed:** 5 minutes  
**Next:** Fill solution paper after this is done

Good luck! 🚀
