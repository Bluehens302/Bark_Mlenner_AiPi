# SOP Subsections Guide

## Overview

The system has been updated to work with your PDF SOPs and their numbered subsections. This allows users to browse and select only the specific sections they need, with appropriate calculators automatically suggested.

## How It Works

### 1. SOP Structure
Your SOPs contain numbered sections like:
- `1. Introduction`
- `2. Materials and Methods`
- `2.1 Media Preparation`
- `2.2 Cell Culture`
- `3. Protocol Steps`
- `3.1 Gibson Assembly`
- etc.

The system automatically parses these numbered sections from your PDF files.

### 2. API Endpoints

The backend API now provides these SOP endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /sops/list` | List all available SOP PDF files |
| `GET /sops/{sop_id}/sections` | Get all numbered sections from an SOP |
| `GET /sops/{sop_id}/sections/{section_number}` | Get specific section with full content |
| `GET /sops/search?q={query}` | Search for sections across all SOPs |
| `GET /sops/{sop_id}/text` | Get full raw text of an SOP |

### 3. Section Matching to Calculators

The system automatically matches section content to calculators:

| Keywords in Section | Suggested Calculator |
|-------------------|---------------------|
| pcr, primer, annealing | PCR Annealing Temperature |
| gibson, assembly, fragment | Gibson Assembly |
| restriction, digest, enzyme | Restriction Digest |
| ligation, insert, vector | Insert:Vector Ratio |
| oligo, oligonucleotide | Oligo Annealing |

## User Workflow

### Step 1: Browse SOPs
1. User opens Google Doc
2. Clicks **🧬 Lab Assistant** → **📋 Browse SOPs**
3. Sees list of available SOPs
4. Selects one

### Step 2: Browse Sections
1. System shows all numbered sections in that SOP
2. User selects the section they need
3. System displays ONLY that section (not the whole SOP)

### Step 3: Work with Section
1. User reads the protocol instructions
2. System suggests relevant calculators
3. User runs calculations
4. Results are saved in the document

### Step 4: Mark Complete and Move On
1. User clicks **✅ Mark Section Complete**
2. Section is marked complete with timestamp
3. User browses to next needed section

## Key Features

### ✅ Subsection-Only Display
- Each section is displayed independently
- Section content starts and ends at the numbered boundaries
- No unnecessary content included

### ✅ Smart Calculator Suggestions
- System analyzes section content
- Suggests relevant calculators automatically
- Links to appropriate Python functions

### ✅ Search Functionality
- Search across all SOPs
- Finds sections by keyword
- Returns "SOP protocol not found" if no match

### ✅ Progress Tracking
- Tracks which sections completed
- Shows calculation history
- Maintains timeline of work

## Error Handling

### "SOP protocol not found"
This message appears when:
- Searching returns no results
- Requested SOP file doesn't exist
- Requested section number doesn't exist
- PDF cannot be parsed

## Example Usage Scenarios

### Scenario 1: Gibson Assembly
1. User searches for "gibson"
2. Finds section "3.1 Gibson Assembly Protocol"
3. System loads just that section
4. Suggests "Gibson Assembly Calculator"
5. User runs calculation with their fragment data
6. Results saved in document

### Scenario 2: Media Preparation
1. User browses "Minimal media prep.pdf"
2. Sees section "2. Media Preparation Steps"
3. Selects that section
4. Follows protocol
5. Marks complete when done

### Scenario 3: Multi-Step Protocol
1. User starts with section "1. Cell Culture"
2. Completes and marks done
3. Moves to section "2. DNA Extraction"
4. Completes and marks done
5. Progress tracks all completed sections

## Technical Details

### PDF Parsing
- Uses `pdfplumber` library to extract text
- Identifies numbered sections with regex patterns
- Caches parsed content for performance
- Handles various numbering formats:
  - `1.`, `2.1`, `3.2.1`
  - `Section 1:`, `Step 2.1`

### Section Pattern Matching
```regex
^(?:Section\s+)?(\d+(?:\.\d+)*)[\.:\s]\s*(.+?)$
```

This matches:
- `1. Introduction`
- `2.1 Materials`
- `Section 3: Methods`
- `Step 4.2.1 Protocol`

### Content Extraction
- Extracts text between section headers
- Preserves formatting where possible
- Removes excessive whitespace
- Limits preview to 200 characters in lists

## Deployment Notes

### Requirements
Added to `requirements.txt`:
```
pypdf2==3.0.1
pdfplumber==0.10.3
```

### File Structure
```
sops/
├── Minimal media prep.pdf
├── SOP-103_DART_Conjugation.pdf
└── SOP-2XX_Gibson_Assembly_General_Protocol_v1.0_FINAL (1).pdf
```

### Google Apps Script
Use **v2** of the Google Apps Script:
- `api/google_apps_script_v2.js` (NEW - use this one!)
- `api/google_apps_script.js` (old - for reference only)

## Troubleshooting

### PDFs not parsing
- Ensure PDFs are text-based (not scanned images)
- Check that sections are numbered
- Use `/sops/{sop_id}/text` endpoint to see raw extraction

### No sections found
- PDF may not have numbered sections
- Try different section numbering format
- Manual conversion to markdown may be needed

### Wrong calculator suggested
- Keywords in section didn't match
- Manually select calculator from menu
- Update keyword mapping in `sop_parser.py`

## Future Enhancements

Potential improvements:
- [ ] OCR for scanned PDFs
- [ ] Better section parsing (bullet points, figures)
- [ ] Step-by-step wizard within sections
- [ ] Automatic protocol resumption
- [ ] Export section + results as PDF
- [ ] Voice-guided protocol reading
- [ ] Integration with lab equipment
