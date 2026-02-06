# Standard Operating Procedures (SOPs)

This folder contains the Standard Operating Procedures for various molecular biology protocols.

## 📥 Adding Your SOPs

### Instructions:
1. Download your SOPs from Google Drive: https://drive.google.com/drive/folders/15UyI4juHo_SXeg9XmCTW5Q5M-o1tGvDe
2. Convert them to Markdown format (`.md` files)
3. Save them in this folder with these exact names:
   - `pcr.md` - PCR protocols
   - `gibson_assembly.md` - Gibson assembly protocols
   - `restriction_ligation.md` - Restriction/ligation protocols
   - `crispr_grna.md` - CRISPR gRNA design protocols

### SOP Format

Each SOP should follow this structure:

```markdown
# Protocol Name

## Overview
Brief description of the protocol

## Materials
- List of materials needed
- Reagents
- Equipment

## Step 1: [Step Name]
Detailed instructions for step 1

**Calculations needed:**
- What calculations are required at this step
- Link to appropriate calculator

**Expected results:**
- What you should observe

## Step 2: [Step Name]
Detailed instructions for step 2

...

## Troubleshooting
Common issues and solutions

## References
Citations and additional resources
```

### Example SOP Template

See `_template.md` for a complete example.

## 🔗 How SOPs are Used

The Google Apps Script will:
1. Load the appropriate SOP based on protocol type
2. Display the relevant step to the user
3. Guide them through the protocol
4. Suggest calculations at each step

## ✅ Checklist

After adding your SOPs, verify:
- [ ] Files are in Markdown format (`.md`)
- [ ] File names match expected names (no spaces, lowercase with underscores)
- [ ] Each SOP has clear step-by-step instructions
- [ ] Steps are numbered with `## Step 1`, `## Step 2`, etc.
- [ ] Calculations are mentioned where needed
- [ ] Files are committed to git
- [ ] GitHub repository is updated

## 📝 Notes

- Keep SOPs updated as protocols change
- Version control with git ensures you can track changes
- Anyone with access to the repository can view these SOPs
- Consider making the repository private if SOPs are proprietary
