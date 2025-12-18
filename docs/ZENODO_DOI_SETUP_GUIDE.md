# Zenodo DOI Setup Guide for VerifiMind-PEAS

**Created**: 2025-12-18
**Purpose**: Fix Zenodo DOI generation issues and establish proper workflow

---

## 🔍 Problem Diagnosed

### Issues Found
1. ❌ **Missing .zenodo.json file** - Required for Zenodo metadata
2. ⚠️ **Inconsistent tag naming** - Mix of `v1.0.x` and `verifimind-v1.1.0`
3. ℹ️ **No CITATION.cff** - Missing citation metadata

### Files Created
1. ✅ `.zenodo.json` - Zenodo metadata configuration
2. ✅ `CITATION.cff` - GitHub citation file

---

## 📋 Step-by-Step Fix

### Step 1: Commit New Files

```bash
cd "C:\Users\weibi\OneDrive\Desktop\VerifiMind Project 2025"

# Add the new files
git add .zenodo.json CITATION.cff docs/ZENODO_DOI_SETUP_GUIDE.md

# Commit
git commit -m "feat: Add Zenodo and citation metadata files for DOI generation

- Add .zenodo.json with comprehensive metadata
- Add CITATION.cff for GitHub citation support
- Add setup guide documentation

This fixes Zenodo DOI generation issues."

# Push
git push
```

### Step 2: Enable Zenodo-GitHub Integration

1. **Go to Zenodo**: https://zenodo.org/
2. **Sign in** with your GitHub account
3. **Navigate to GitHub settings**: https://zenodo.org/account/settings/github/
4. **Find your repository**: `creator35lwb-web/VerifiMind-PEAS`
5. **Toggle ON** the repository switch
6. **Verify** the webhook is active

### Step 3: Create a New Release

#### Option A: Using GitHub CLI (Recommended)

```bash
# Create and push a new tag for the latest commit
git tag -a v1.1.1 -m "Release v1.1.1: Add Zenodo DOI support"
git push origin v1.1.1

# Create GitHub release
gh release create v1.1.1 \
  --title "VerifiMind-PEAS v1.1.1 - Zenodo DOI Support" \
  --notes "Release v1.1.1 includes Zenodo DOI metadata configuration.

**What's New:**
- ✅ Added .zenodo.json for automatic DOI generation
- ✅ Added CITATION.cff for academic citations
- ✅ Fixed Zenodo integration

**Previous Release:** v1.1.0 (Production-Ready MCP Server)

**Zenodo DOI:** Will be generated automatically upon release publication.

This release enables automatic DOI generation for all future releases."
```

#### Option B: Using GitHub Web Interface

1. Go to: https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/new
2. **Tag**: `v1.1.1`
3. **Title**: `VerifiMind-PEAS v1.1.1 - Zenodo DOI Support`
4. **Description**: (Copy from Option A above)
5. Click **Publish release**

### Step 4: Verify Zenodo DOI Creation

1. **Wait 5-10 minutes** after release publication
2. **Check Zenodo**: https://zenodo.org/account/settings/github/
3. **Look for your release** in the list
4. **Click on the release** to see the DOI
5. **DOI format**: `10.5281/zenodo.XXXXXXX`

### Step 5: Update CITATION.cff with Real DOI

Once you get the DOI from Zenodo:

```bash
# Edit CITATION.cff and replace XXXXXXX with real DOI number
# For example: 10.5281/zenodo.1234567

# Commit the update
git add CITATION.cff
git commit -m "docs: Update CITATION.cff with Zenodo DOI"
git push
```

---

## 🎯 Future Workflow

### For Every New Release:

1. **Make your changes**
2. **Commit and push** to GitHub
3. **Create a Git tag**:
   ```bash
   git tag -a v1.x.x -m "Release v1.x.x: Description"
   git push origin v1.x.x
   ```
4. **Create GitHub release** (via CLI or web)
5. **Zenodo automatically**:
   - Detects new release
   - Reads .zenodo.json
   - Generates new DOI
   - Creates archive

### DOI Badge for README

After getting your DOI, add this badge to your README.md:

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

Replace `XXXXXXX` with your actual DOI number.

---

## 📖 .zenodo.json Explained

The `.zenodo.json` file contains:

- **title**: Project name
- **description**: Detailed description
- **creators**: Authors (you, Manus AI, Claude Code)
- **keywords**: Search terms for discovery
- **license**: MIT license
- **related_identifiers**: Links to related DOIs (Genesis Methodology)
- **version**: Current version number
- **publication_date**: Release date

Zenodo reads this file automatically when creating DOIs.

---

## 🔗 Related Resources

- **Zenodo GitHub Integration**: https://docs.zenodo.org/deposit/integrations/github/
- **CITATION.cff Spec**: https://citation-file-format.github.io/
- **GitHub Releases**: https://docs.github.com/en/repositories/releasing-projects-on-github

---

## ❓ Troubleshooting

### Issue: Zenodo doesn't create DOI

**Solutions:**
1. Check Zenodo-GitHub integration is enabled
2. Verify .zenodo.json has no syntax errors
3. Ensure release is published (not draft)
4. Wait 10-15 minutes (Zenodo can be slow)
5. Check Zenodo logs: https://zenodo.org/account/settings/github/

### Issue: Invalid .zenodo.json

**Solution:**
```bash
# Validate JSON syntax
python -m json.tool .zenodo.json
```

If there are errors, fix them and commit again.

### Issue: DOI not showing on GitHub

**Solution:**
1. DOI appears on Zenodo, not GitHub
2. Add DOI badge to README manually
3. Update CITATION.cff with DOI

---

## ✅ Success Checklist

- [ ] .zenodo.json file created and committed
- [ ] CITATION.cff file created and committed
- [ ] Files pushed to GitHub
- [ ] Zenodo-GitHub integration enabled
- [ ] New release created (v1.1.1)
- [ ] DOI generated on Zenodo (wait 10 mins)
- [ ] CITATION.cff updated with real DOI
- [ ] DOI badge added to README
- [ ] Verified DOI works (click the badge)

---

## 📞 Need Help?

If you still have issues:

1. **Check Zenodo Status**: https://zenodo.org/account/settings/github/
2. **Zenodo Support**: support@zenodo.org
3. **GitHub Discussions**: https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions

---

**Created by**: Claude Code (Implementation Agent)
**Date**: 2025-12-18
**Status**: Ready for implementation

---

**Next Step**: Commit these files and create v1.1.1 release!
