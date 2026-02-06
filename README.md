# Bark Mlenner AI-Powered Molecular Biology Assistant

An integrated system that combines Google Docs, Python molecular biology tools, and SOP management to create an interactive lab protocol assistant.

## 🎯 What This System Does

This "machine" provides lab researchers with:
- **Interactive Google Docs** that guide users through protocols step-by-step
- **Automatic calculations** for PCR, Gibson Assembly, Restriction Digests, and more
- **SOP integration** that displays relevant protocols at each step
- **Progress tracking** so users can see what was done previously and what comes next
- **Results storage** directly in the document for easy record-keeping

## 🏗️ Architecture

```
┌─────────────────┐
│  Google Docs    │  ← User Interface
│  + Apps Script  │
└────────┬────────┘
         │
         │ HTTPS API Calls
         │
┌────────▼────────┐
│   FastAPI       │  ← Backend API
│   (Python)      │
└────────┬────────┘
         │
         │ Imports
         │
┌────────▼────────────────┐
│ molecular_biology_tools │  ← Calculation Engine
│       (Python)          │
└─────────────────────────┘

         ┌──────────────┐
         │ SOP Files    │  ← Protocol Repository
         │ (Markdown)   │
         └──────────────┘
```

## 📁 Repository Structure

```
Bark_Mlenner_AiPi/
├── api/
│   ├── main.py                    # FastAPI backend server
│   └── google_apps_script.js      # Google Docs integration
├── tools/
│   └── molecular_biology_tools.py # Core calculation functions
├── sops/
│   ├── pcr.md                     # PCR protocol (ADD YOUR SOPs HERE)
│   ├── gibson_assembly.md         # Gibson assembly protocol
│   ├── restriction_ligation.md    # Restriction/ligation protocol
│   └── crispr_grna.md            # CRISPR gRNA design protocol
├── docs/
│   └── deployment.md              # Deployment instructions
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🚀 Quick Start Guide

### Step 1: Add Your SOPs

1. Download your SOPs from Google Drive
2. Convert them to Markdown format (`.md` files)
3. Place them in the `sops/` folder with these filenames:
   - `pcr.md` - PCR protocols
   - `gibson_assembly.md` - Gibson assembly protocols
   - `restriction_ligation.md` - Restriction/ligation protocols
   - `crispr_grna.md` - CRISPR gRNA design protocols

**SOP Format:**
```markdown
# Protocol Name

## Step 1
Instructions for step 1...
- Detail 1
- Detail 2

## Step 2
Instructions for step 2...
```

### Step 2: Deploy the API

#### Option A: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
cd api
python main.py

# API will be available at http://localhost:8000
```

#### Option B: Deploy to Cloud (Recommended for Production)

**Deploy to Render (Free):**
1. Push this repository to GitHub
2. Go to [render.com](https://render.com)
3. Create new "Web Service"
4. Connect your GitHub repository
5. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd api && uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Deploy!
7. Copy your deployment URL (e.g., `https://your-app.onrender.com`)

**Other Deployment Options:**
- **Google Cloud Run**: Serverless, auto-scaling
- **Railway**: Easy deployment
- **Heroku**: Classic platform
- **AWS Lambda**: Serverless with API Gateway

See `docs/deployment.md` for detailed deployment instructions.

### Step 3: Set Up Google Apps Script

1. Create a new Google Doc (this will be your lab notebook)
2. Go to **Extensions** → **Apps Script**
3. Delete the default code
4. Copy the entire contents of `api/google_apps_script.js`
5. Paste into the Apps Script editor
6. **Update the configuration** at the top:
   ```javascript
   const CONFIG = {
     API_BASE_URL: 'https://your-deployed-api-url.com',  // ← UPDATE THIS
     SOP_BASE_URL: 'https://raw.githubusercontent.com/Bluehens302/Bark_Mlenner_AiPi/main/sops/',
     ...
   };
   ```
7. Save the script (💾 icon)
8. Reload your Google Doc
9. You should see a new menu: **🧬 Lab Assistant**

### Step 4: Start Using It!

1. Open your Google Doc
2. Click **🧬 Lab Assistant** → **📋 Start New Protocol**
3. Select your protocol type
4. Follow the step-by-step guidance
5. Use **🔬 Run Calculation** to perform calculations
6. Results are automatically saved in the document

## 🧪 Available Calculations

The API provides these endpoints:

| Calculation | Endpoint | Description |
|------------|----------|-------------|
| PCR Annealing Temp | `/pcr/annealing-temp` | Calculate optimal annealing temperature |
| Gibson Assembly | `/gibson/calculate` | Calculate fragment volumes and ratios |
| Restriction Digest | `/restriction/digest` | Calculate digest reaction volumes |
| Insert:Vector Ratio | `/ligation/insert-vector-ratio` | Calculate ligation ratios |
| Oligo Annealing | `/oligo/annealing` | Calculate oligo annealing volumes |

## 📖 User Workflow

1. **User opens Google Doc**
   - Sees previous work and results
   - Sees current step in protocol

2. **System suggests next step**
   - Displays relevant SOP section
   - Shows what calculations are needed

3. **User performs calculations**
   - Clicks menu to run calculations
   - Enters data (primers, concentrations, etc.)
   - Results automatically inserted into document

4. **User proceeds**
   - Marks step complete
   - Moves to next step
   - Progress tracked automatically

## 🔧 Development

### Running Tests
```bash
# Test the API locally
curl http://localhost:8000/

# Test a specific endpoint
curl -X POST http://localhost:8000/pcr/annealing-temp \
  -H "Content-Type: application/json" \
  -d '{
    "forward_primer": "ATCGATCGATCGATCG",
    "reverse_primer": "GCTAGCTAGCTAGCTA",
    "pcr_type": "OneTaq"
  }'
```

### API Documentation
Once the API is running, visit:
- **Interactive docs**: `http://localhost:8000/docs`
- **OpenAPI spec**: `http://localhost:8000/openapi.json`

## 📝 TODO / Future Enhancements

- [ ] Add CRISPR gRNA primer design to API
- [ ] Support for multiple document templates
- [ ] Export results to CSV/Excel
- [ ] Plate layout calculator
- [ ] Integration with lab inventory systems
- [ ] Email notifications for long protocols
- [ ] Mobile app version

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Add your license here]

## 🆘 Troubleshooting

### API not responding
- Check that the API is running: `curl http://your-api-url/`
- Check API logs for errors
- Verify CORS is enabled

### Google Apps Script errors
- Check the Apps Script logs: View → Logs
- Verify API_BASE_URL is correct
- Ensure API is publicly accessible

### SOP not loading
- Check SOP files are in `sops/` folder
- Verify file names match protocol types
- Check GitHub repository is public

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation in `docs/`
- Review API documentation at `/docs` endpoint

---

**Made with 🧬 for molecular biology researchers**
