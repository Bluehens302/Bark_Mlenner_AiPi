"""
Molecular Biology Tools API
Backend API for Google Docs integration
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import sys
import os

# Add tools directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
from molecular_biology_tools import (
    get_annealing_temp,
    validate_primer,
    gibson_assembly,
    insert_vector_ratio,
    restriction_digest_calculator,
    annealing_calculator
)

# Import SOP parser
from sop_parser import SOPParser

app = FastAPI(
    title="Molecular Biology Tools API",
    description="API for molecular biology calculations",
    version="1.0.0"
)

# Configure CORS for Google Apps Script
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Google Apps Script domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SOP Parser
sops_directory = os.path.join(os.path.dirname(__file__), '..', 'sops')
sop_parser = SOPParser(sops_directory)

# Request/Response Models
class PrimerPair(BaseModel):
    forward_primer: str = Field(..., description="Forward primer sequence")
    reverse_primer: str = Field(..., description="Reverse primer sequence")
    pcr_type: str = Field(..., description="PCR type: OneTaq or Q5")

class AnnealingTempResponse(BaseModel):
    annealing_temp: float
    tm1: float
    tm2: float
    warning: Optional[str] = None

class GibsonFragment(BaseModel):
    size_bp: int = Field(..., description="Fragment size in base pairs")
    concentration_ng_ul: float = Field(..., description="DNA concentration in ng/µL")
    molar_ratio: float = Field(1.0, description="Desired molar ratio (default 1.0)")

class GibsonAssemblyRequest(BaseModel):
    fragments: List[GibsonFragment] = Field(..., min_items=2)
    total_volume_ul: float = Field(..., description="Desired total reaction volume in µL")

class RestrictionDigestRequest(BaseModel):
    dna_mass_ng: float = Field(..., description="DNA mass in nanograms")
    dna_conc_ng_ul: float = Field(..., description="DNA concentration in ng/µL")

class InsertVectorRequest(BaseModel):
    vector_size_bp: int
    insert_size_bp: int
    vector_conc_ng_ul: float
    insert_conc_ng_ul: float
    ratio: float = Field(3.0, description="Insert:vector molar ratio")
    vector_mass_ng: float = Field(..., description="Vector mass for ligation in ng")

class OligoAnnealingRequest(BaseModel):
    oligo1_conc_uM: float
    oligo2_conc_uM: float
    desired_conc_uM: float
    final_volume_ul: float

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Molecular Biology Tools API",
        "version": "1.0.0",
        "endpoints": {
            "calculations": [
                "/pcr/annealing-temp",
                "/gibson/calculate",
                "/restriction/digest",
                "/ligation/insert-vector-ratio",
                "/oligo/annealing"
            ],
            "sops": [
                "/sops/list",
                "/sops/{sop_id}/sections",
                "/sops/{sop_id}/sections/{section_number}",
                "/sops/search?q={query}",
                "/sops/{sop_id}/text"
            ]
        }
    }

@app.post("/pcr/annealing-temp", response_model=AnnealingTempResponse)
async def calculate_annealing_temp(primer_pair: PrimerPair):
    """Calculate annealing temperature for PCR primers"""
    try:
        # Validate primers
        fwd = validate_primer(primer_pair.forward_primer)
        rev = validate_primer(primer_pair.reverse_primer)

        # Calculate annealing temp
        from Bio.SeqUtils import MeltingTemp as mt
        from Bio.Seq import Seq

        seq1 = Seq(fwd)
        seq2 = Seq(rev)

        if primer_pair.pcr_type == "OneTaq":
            tm1 = mt.Tm_NN(seq1, nn_table=mt.DNA_NN4, Na=50, Mg=1.8, dNTPs=0.2, dnac1=200)
            tm2 = mt.Tm_NN(seq2, nn_table=mt.DNA_NN4, Na=50, Mg=1.8, dNTPs=0.2, dnac1=200)
            annealing_temp = min(tm1, tm2) - 3
        elif primer_pair.pcr_type == "Q5":
            tm1 = mt.Tm_NN(seq1, nn_table=mt.DNA_NN4, Na=70, Mg=2.0, dNTPs=0.2, dnac1=500)
            tm2 = mt.Tm_NN(seq2, nn_table=mt.DNA_NN4, Na=70, Mg=2.0, dNTPs=0.2, dnac1=500)
            annealing_temp = min(tm1, tm2) + 3
        else:
            raise HTTPException(status_code=400, detail="PCR type must be 'OneTaq' or 'Q5'")

        warning = None
        if abs(tm1 - tm2) > 5:
            warning = f"Tm difference ({abs(tm1 - tm2):.1f}°C) is >5°C. Consider redesigning primers."

        return AnnealingTempResponse(
            annealing_temp=round(annealing_temp, 1),
            tm1=round(tm1, 1),
            tm2=round(tm2, 1),
            warning=warning
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/gibson/calculate")
async def calculate_gibson_assembly(request: GibsonAssemblyRequest):
    """Calculate Gibson assembly volumes with custom molar ratios"""
    try:
        # Extract fragment data
        fragments = [(f.size_bp, f.concentration_ng_ul) for f in request.fragments]
        ratios = [f.molar_ratio for f in request.fragments]

        # Calculate base reference amount
        min_ratio = min(ratios)
        base_pmol = 0.1

        # Calculate adjusted pmols and ng for each fragment
        adjusted_pmols = [base_pmol * ratio / min_ratio for ratio in ratios]
        adjusted_ng = []
        fragment_volumes = []

        for i, (size, conc) in enumerate(fragments):
            ng = adjusted_pmols[i] * size * 650 / 1000
            vol = ng / conc
            adjusted_ng.append(ng)
            fragment_volumes.append(vol)

        # Calculate scaling factor
        current_total_volume = sum(fragment_volumes)
        scale_factor = request.total_volume_ul / current_total_volume

        # Build response
        result_fragments = []
        total_pmol = 0

        for idx, (size, conc) in enumerate(fragments):
            scaled_ng = adjusted_ng[idx] * scale_factor
            scaled_vol = fragment_volumes[idx] * scale_factor
            scaled_pmol = adjusted_pmols[idx] * scale_factor
            total_pmol += scaled_pmol

            result_fragments.append({
                "fragment_number": idx + 1,
                "size_bp": size,
                "concentration_ng_ul": conc,
                "volume_ul": round(scaled_vol, 2),
                "mass_ng": round(scaled_ng, 2),
                "pmol": round(scaled_pmol, 3),
                "molar_ratio": ratios[idx]
            })

        total_size = sum(f[0] for f in fragments)

        return {
            "fragments": result_fragments,
            "total_volume_ul": request.total_volume_ul,
            "total_size_bp": total_size,
            "total_pmol": round(total_pmol, 3),
            "scale_factor": round(scale_factor, 2),
            "molar_ratios": ":".join(f"{r:.1f}" for r in ratios)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/restriction/digest")
async def calculate_restriction_digest(request: RestrictionDigestRequest):
    """Calculate restriction digest reaction volumes"""
    try:
        dna_mass_ug = request.dna_mass_ng / 1000.0
        reference_dna_mass_ug = 1.0
        reference_total_vol_ul = 50.0

        scale_factor = dna_mass_ug / reference_dna_mass_ug
        total_vol_ul = reference_total_vol_ul * scale_factor

        dna_vol_ul = request.dna_mass_ng / request.dna_conc_ng_ul

        if dna_vol_ul >= total_vol_ul:
            raise HTTPException(
                status_code=400,
                detail="DNA volume exceeds calculated total volume; increase DNA concentration."
            )

        buffer_vol_ul = total_vol_ul * 0.1
        reference_enzyme_vol_ul = 1.0
        enzyme_vol_ul = reference_enzyme_vol_ul * scale_factor
        enzyme_vol_ul = min(enzyme_vol_ul, total_vol_ul * 0.1)

        water_vol_ul = total_vol_ul - (dna_vol_ul + buffer_vol_ul + enzyme_vol_ul)

        if water_vol_ul < 0:
            raise HTTPException(
                status_code=400,
                detail="Calculated water volume is negative; increase DNA concentration."
            )

        warning = None
        if request.dna_mass_ng < 100:
            warning = "DNA mass <100 ng may yield suboptimal results."

        return {
            "dna_mass_ng": round(request.dna_mass_ng, 2),
            "dna_volume_ul": round(dna_vol_ul, 2),
            "buffer_volume_ul": round(buffer_vol_ul, 2),
            "enzyme_volume_ul": round(enzyme_vol_ul, 2),
            "water_volume_ul": round(water_vol_ul, 2),
            "total_volume_ul": round(total_vol_ul, 2),
            "warning": warning
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ligation/insert-vector-ratio")
async def calculate_insert_vector_ratio(request: InsertVectorRequest):
    """Calculate insert and vector amounts for ligation"""
    try:
        dna_mw_per_bp = 660

        vector_mass_g = request.vector_mass_ng * 1e-9
        vector_moles = vector_mass_g / (request.vector_size_bp * dna_mw_per_bp)

        insert_moles = vector_moles * request.ratio
        insert_mass_g = insert_moles * (request.insert_size_bp * dna_mw_per_bp)
        insert_mass_ng = insert_mass_g * 1e9

        vector_vol = request.vector_mass_ng / request.vector_conc_ng_ul
        insert_vol = insert_mass_ng / request.insert_conc_ng_ul

        return {
            "vector_mass_ng": round(request.vector_mass_ng, 2),
            "vector_volume_ul": round(vector_vol, 2),
            "insert_mass_ng": round(insert_mass_ng, 2),
            "insert_volume_ul": round(insert_vol, 2),
            "ratio": request.ratio
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/oligo/annealing")
async def calculate_oligo_annealing(request: OligoAnnealingRequest):
    """Calculate volumes for oligo annealing reaction"""
    try:
        oligo1_vol = (request.desired_conc_uM * request.final_volume_ul) / request.oligo1_conc_uM
        oligo2_vol = (request.desired_conc_uM * request.final_volume_ul) / request.oligo2_conc_uM
        water_vol = request.final_volume_ul - oligo1_vol - oligo2_vol

        if water_vol < 0:
            raise HTTPException(
                status_code=400,
                detail="Calculated water volume is negative; check concentrations."
            )

        return {
            "oligo1_volume_ul": round(oligo1_vol, 2),
            "oligo2_volume_ul": round(oligo2_vol, 2),
            "water_volume_ul": round(water_vol, 2),
            "final_volume_ul": request.final_volume_ul,
            "final_concentration_uM": request.desired_conc_uM
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# SOP ENDPOINTS
# ============================================================================

@app.get("/sops/list")
async def list_sops():
    """
    List all available SOP files

    Returns list of SOPs with their IDs and filenames
    """
    try:
        sops = sop_parser.list_sops()
        return {
            "count": len(sops),
            "sops": sops
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing SOPs: {str(e)}")

@app.get("/sops/{sop_id}/sections")
async def get_sop_sections(sop_id: str):
    """
    Get all numbered sections from a specific SOP

    Args:
        sop_id: SOP identifier (filename without extension)

    Returns:
        List of sections with section_number, title, and preview
    """
    try:
        sections = sop_parser.parse_sections(sop_id)

        if not sections:
            # Check if SOP exists but has no parseable sections
            text = sop_parser.extract_text_from_pdf(sop_id)
            if text:
                return {
                    "sop_id": sop_id,
                    "message": "SOP found but no numbered sections detected",
                    "sections": [],
                    "raw_text_available": True
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"SOP protocol not found: {sop_id}"
                )

        # Return sections with preview (first 200 chars of content)
        result_sections = []
        for section in sections:
            content_preview = section["content"][:200] + "..." if len(section["content"]) > 200 else section["content"]
            result_sections.append({
                "section_number": section["section_number"],
                "title": section["title"],
                "full_heading": section["full_heading"],
                "content_preview": content_preview
            })

        return {
            "sop_id": sop_id,
            "count": len(result_sections),
            "sections": result_sections
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing SOP: {str(e)}")

@app.get("/sops/{sop_id}/sections/{section_number}")
async def get_sop_section(sop_id: str, section_number: str):
    """
    Get a specific section from an SOP with suggested calculators

    Args:
        sop_id: SOP identifier
        section_number: Section number (e.g., "1", "2.1", "3.2.1")

    Returns:
        Section with full content and suggested calculators
    """
    try:
        section = sop_parser.get_section_with_calculator(sop_id, section_number)

        if not section:
            raise HTTPException(
                status_code=404,
                detail=f"SOP protocol not found: section {section_number} in {sop_id}"
            )

        return section
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving section: {str(e)}")

@app.get("/sops/search")
async def search_sops(q: str = Query(..., description="Search query")):
    """
    Search for sections across all SOPs

    Args:
        q: Search query (searches in section titles and content)

    Returns:
        List of matching sections from all SOPs
    """
    try:
        results = sop_parser.search_sections(q)

        if not results:
            return {
                "query": q,
                "count": 0,
                "results": [],
                "message": "SOP protocol not found"
            }

        # Add content preview to results
        for result in results:
            if len(result["content"]) > 300:
                result["content_preview"] = result["content"][:300] + "..."
            else:
                result["content_preview"] = result["content"]

            # Add suggested calculators
            calculators = sop_parser.map_section_to_calculator(
                result["title"],
                result["content"]
            )
            result["suggested_calculators"] = calculators

        return {
            "query": q,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching SOPs: {str(e)}")

@app.get("/sops/{sop_id}/text")
async def get_sop_full_text(sop_id: str):
    """
    Get full text content of an SOP (raw extraction)

    Args:
        sop_id: SOP identifier

    Returns:
        Full text content of the SOP
    """
    try:
        text = sop_parser.extract_text_from_pdf(sop_id)

        if not text:
            raise HTTPException(
                status_code=404,
                detail=f"SOP protocol not found: {sop_id}"
            )

        return {
            "sop_id": sop_id,
            "text": text,
            "length": len(text)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
