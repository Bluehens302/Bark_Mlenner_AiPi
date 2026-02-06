# 🚀 Quick Start Guide

Follow these steps to get your Molecular Biology Lab Assistant up and running.

## ✅ Immediate Next Steps

### 1. Add Your SOPs (REQUIRED)

📥 **Download your SOPs from Google Drive:**
https://drive.google.com/drive/folders/15UyI4juHo_SXeg9XmCTW5Q5M-o1tGvDe

Then place them in the `sops/` folder:

```bash
# Navigate to the sops folder
cd /home/hris/Bark_Mlenner_AiPi/sops/

# Copy your SOP files here
# Name them:
#   - pcr.md
#   - gibson_assembly.md
#   - restriction_ligation.md
#   - crispr_grna.md
```

**Note:** Convert to Markdown (`.md`) format if needed. See `sops/_template.md` for the expected format.

### 2. Commit and Push to GitHub

```bash
cd /home/hris/Bark_Mlenner_AiPi

# Add all files
git add .

# Commit
git commit -m "Add API backend and Google Apps Script integration

- FastAPI backend with molecular biology calculators
- Google Apps Script for Google Docs integration
- SOP repository structure
- Deployment documentation"

# Push to GitHub
git push origin main
```

### 3. Deploy the API

**Recommended: Use Render (Free)**

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect repository: `Bluehens302/Bark_Mlenner_AiPi`
5. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd api && uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Deploy!
7. **Save your deployment URL** (e.g., `https://molbio-tools-api.onrender.com`)

See `docs/deployment.md` for other deployment options.

### 4. Set Up Google Apps Script

1. Create a **new Google Doc** (this will be your lab notebook)
2. Go to **Extensions** → **Apps Script**
3. Delete default code
4. Copy **all content** from `api/google_apps_script.js`
5. Paste into Apps Script editor
6. **UPDATE line 14** with your API URL:
   ```javascript
   API_BASE_URL: 'https://your-deployed-url.com',  // ← CHANGE THIS
   ```
7. Save (💾)
8. Go back to your Google Doc
9. Reload the page
10. You should see **🧬 Lab Assistant** in the menu!

### 5. Test It!

1. In your Google Doc, click **🧬 Lab Assistant** → **📋 Start New Protocol**
2. Choose a protocol type
3. Click **🔬 Run Calculation**
4. Try a PCR calculation:
   - Forward primer: `ATCGATCGATCGATCGATCG`
   - Reverse primer: `GCTAGCTAGCTAGCTAGCTA`
   - PCR type: `OneTaq`
5. Results should appear in your document!

## 🎯 What You've Built

```
┌─────────────────────────┐
│   Google Docs           │ ← Users work here
│   (Lab Notebook)        │   - See previous work
│   + Apps Script Menu    │   - Get next step guidance
└───────────┬─────────────┘   - Run calculations
            │                 - Results auto-saved
            │
            │ API Calls
            ▼
┌─────────────────────────┐
│   FastAPI Backend       │ ← Deployed to Render/Cloud
│   (Calculations)        │   - PCR calculations
└───────────┬─────────────┘   - Gibson assembly
            │                 - Ligations
            │                 - Restriction digests
            ▼
┌─────────────────────────┐
│   molecular_biology_    │ ← Your existing Python tools
│   tools.py              │   (now accessible via API!)
└─────────────────────────┘

┌─────────────────────────┐
│   SOPs (Markdown)       │ ← Protocol instructions
│   GitHub Repository     │   - Displayed in Google Docs
└─────────────────────────┘   - Version controlled
```

## 📋 Checklist

- [ ] Downloaded SOPs from Google Drive
- [ ] Placed SOPs in `sops/` folder with correct names
- [ ] Committed changes to git
- [ ] Pushed to GitHub
- [ ] Deployed API to Render (or other platform)
- [ ] Copied deployment URL
- [ ] Created Google Doc
- [ ] Added Apps Script code
- [ ] Updated API_BASE_URL in script
- [ ] Tested a calculation
- [ ] Results appeared in document

## 🎓 How to Use Daily

### Starting a Protocol:
1. Open your Google Doc
2. **🧬 Lab Assistant** → **📋 Start New Protocol**
3. Select protocol type (PCR, Gibson, etc.)
4. Document shows Step 1 with SOP instructions

### During the Protocol:
1. Read the SOP instructions for current step
2. Click **🔬 Run Calculation** when needed
3. Enter your data (primers, concentrations, etc.)
4. Results automatically inserted into document
5. Click **⏭️ Next Step** when ready to proceed

### Viewing Progress:
- **📊 View Progress**: See where you are in the protocol
- **📖 View Current SOP**: See full protocol in sidebar
- **🔄 Refresh View**: Update document display

### Collaboration:
- Share the Google Doc with lab members
- They can see what you've done
- They can continue from where you left off
- All results are saved in the document

## 🆘 Troubleshooting

### "Menu not appearing"
- Reload the Google Doc
- Check Apps Script was saved
- Check for errors: Extensions → Apps Script → View → Logs

### "API not responding"
- Verify API is deployed: `curl https://your-api-url.com/`
- Check API URL in Apps Script is correct
- Check API logs on Render dashboard

### "SOP not loading"
- Verify SOP files are in `sops/` folder
- Check file names match expected names
- Ensure files are pushed to GitHub
- Check repository is public

### "Calculation errors"
- Check the error message
- Verify input format (primers should be ATCG only)
- Check Apps Script logs for details
- Test API directly with curl (see deployment.md)

## 📚 Next Steps

Once everything is working:

1. **Customize the SOPs** - Add your lab-specific details
2. **Create templates** - Make Google Doc templates for common workflows
3. **Train your team** - Show others how to use the system
4. **Enhance the API** - Add more calculations as needed
5. **Improve the UI** - Customize the Google Apps Script interface

## 💡 Tips

- **Create a template Google Doc** and share it with your team
- **Keep SOPs updated** - they're version controlled in git
- **Use descriptive step names** in SOPs for better navigation
- **Save your work** - Results are auto-saved in the document
- **Share the document** - Multiple people can view/contribute

## 📞 Need Help?

1. Check `README.md` for detailed documentation
2. Check `docs/deployment.md` for deployment issues
3. Review `sops/README.md` for SOP formatting
4. Check API docs: `https://your-api-url.com/docs`
5. Open an issue on GitHub

---

**Ready to revolutionize your lab workflow? Let's go! 🚀🧬**
