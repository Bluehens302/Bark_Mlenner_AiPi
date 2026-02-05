import math
import re
from Bio.SeqUtils import MeltingTemp as mt
from Bio.Seq import Seq

def validate_primer(primer):
    """Validate primer sequence: only A, T, C, G, and common degenerate bases."""
    primer = primer.upper()
    valid_bases = set("ATCGWSMKRYBDHVN")
    if not all(base in valid_bases for base in primer):
        raise ValueError(
            f"Invalid primer sequence: {primer}. Only A, T, C, G, and degenerate bases (W, S, M, K, R, Y, B, D, H, V, N) allowed."
        )
    if len(primer) < 15 or len(primer) > 40:
        print(f"Warning: Primer length ({len(primer)} bp) is outside optimal range (15–40 bp).")
    return primer

def get_annealing_temp(primer1, primer2, pcr_type):
    """Calculate annealing temperature for OneTaq or Q5 polymerase."""
    try:
        primer1 = validate_primer(primer1)
        primer2 = validate_primer(primer2)
        seq1 = Seq(primer1)
        seq2 = Seq(primer2)
        if pcr_type == "OneTaq":
            tm1 = mt.Tm_NN(seq1, nn_table=mt.DNA_NN4, Na=50, Mg=1.8, dNTPs=0.2, dnac1=200)
            tm2 = mt.Tm_NN(seq2, nn_table=mt.DNA_NN4, Na=50, Mg=1.8, dNTPs=0.2, dnac1=200)
            annealing_temp = min(tm1, tm2) - 3
        elif pcr_type == "Q5":
            tm1 = mt.Tm_NN(seq1, nn_table=mt.DNA_NN4, Na=70, Mg=2.0, dNTPs=0.2, dnac1=500)
            tm2 = mt.Tm_NN(seq2, nn_table=mt.DNA_NN4, Na=70, Mg=2.0, dNTPs=0.2, dnac1=500)
            annealing_temp = min(tm1, tm2) + 3
        else:
            raise ValueError("Unknown PCR type. Use 'OneTaq' or 'Q5'.")
        if abs(tm1 - tm2) > 5:
            print(f"Warning: Tm difference ({abs(tm1 - tm2):.1f}°C) is >5°C. Consider redesigning primers.")
        return round(annealing_temp, 1)
    except Exception as e:
        raise ValueError(f"Error calculating Tm: {str(e)}")

def pcr_mastermix_calculator():
    """Calculate PCR master mix (excluding template) and annealing temperature for OneTaq or Q5."""
    print("\n🔬 PCR Master Mix Calculator")
    try:
        pcr_type = input("Choose PCR type ('OneTaq' or 'Q5') [default OneTaq]: ").strip() or "OneTaq"
        if pcr_type not in ["OneTaq", "Q5"]:
            raise ValueError("Invalid PCR type. Use 'OneTaq' or 'Q5'.")
        fwd = input("Enter forward primer sequence: ").strip()
        rev = input("Enter reverse primer sequence: ").strip()
        num_reactions = int(input("How many reactions? "))
        if num_reactions <= 0:
            raise ValueError("Number of reactions must be positive.")
        extra_reactions = float(input("Add extra (%) for pipetting loss [default 10]: ") or 10)
        if extra_reactions < 0:
            raise ValueError("Extra percentage cannot be negative.")
        total_rxns = math.ceil(num_reactions * (1 + extra_reactions / 100))
        print(f"\n📌 Preparing mix for {total_rxns} total reactions ({num_reactions} + {extra_reactions}% extra)")
        if pcr_type == "OneTaq":
            master_mix = {
                "OneTaq 2X Master Mix": (12.5, "µL"),
                "10 µM Forward Primer": (0.5, "µL"),
                "10 µM Reverse Primer": (0.5, "µL"),
                "Water": (11.5, "µL")
            }
            template_per_tube = (1.0, "µL")
        else:
            master_mix = {
                "5X Q5 Reaction Buffer": (5.0, "µL"),
                "10 mM dNTPs": (0.5, "µL"),
                "10 µM Forward Primer": (1.25, "µL"),
                "10 µM Reverse Primer": (1.25, "µL"),
                "Q5 Polymerase": (0.25, "µL"),
                "Water": (16.25, "µL")
            }
            template_per_tube = (1.0, "µL")
        print("\n🧪 Master Mix (EXCLUDING template):")
        for component, (vol_per_rxn, unit) in master_mix.items():
            total_vol = vol_per_rxn * total_rxns
            print(f"{component:<25}: {vol_per_rxn:.2f} {unit} × {total_rxns} = {total_vol:.2f} {unit}")
        print(f"\nAdd template DNA to each tube: {template_per_tube[0]} {template_per_tube[1]} (per reaction)")
        ann_temp = get_annealing_temp(fwd, rev, pcr_type)
        print(f"\n🔥 Suggested annealing temperature: {ann_temp}°C")
        print("\n🧬 Suggested Thermocycler Program:")
        print("1. Initial denaturation: 98°C for 30 sec" if pcr_type == "Q5" else "1. Initial denaturation: 94°C for 30 sec")
        print(f"2. Denaturation: {'98' if pcr_type == 'Q5' else '94'}°C for 10 sec")
        print(f"3. Annealing: {ann_temp}°C for 15–30 sec")
        print("4. Extension: 72°C for 30 sec per kb")
        print(" (adjust time for amplicon length)")
        print("5. Final extension: 72°C for 5 min")
        print("6. Hold: 4°C")
    except ValueError as e:
        print(f"❌ Error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def insert_vector_ratio():
    """Calculate insert and vector amounts for ligation based on molar ratio."""
    try:
        print("\n🧪 Insert:Vector Ratio Calculator (molar ratio, user-defined vector mass)")
        vector_size = int(input("Enter vector size (bp): "))
        if vector_size <= 0:
            raise ValueError("Vector size must be positive.")
        insert_size = int(input("Enter insert size (bp): "))
        if insert_size <= 0:
            raise ValueError("Insert size must be positive.")
        vector_conc = float(input("Enter vector DNA concentration (ng/µL): "))
        if vector_conc <= 0:
            raise ValueError("Vector concentration must be positive.")
        insert_conc = float(input("Enter insert DNA concentration (ng/µL): "))
        if insert_conc <= 0:
            raise ValueError("Insert concentration must be positive.")
        ratio = float(input("Enter desired insert:vector molar ratio (e.g., 3 for 3:1) [default 3]: ") or 3)
        if ratio <= 0:
            raise ValueError("Ratio must be positive.")
        vector_mass_ng = float(input("Enter DNA ligation reaction mass (ng): "))
        if vector_mass_ng <= 0:
            raise ValueError("Vector mass must be positive.")
        dna_mw_per_bp = 660
        vector_mass_g = vector_mass_ng * 1e-9
        vector_moles = vector_mass_g / (vector_size * dna_mw_per_bp)
        insert_moles = vector_moles * ratio
        insert_mass_g = insert_moles * (insert_size * dna_mw_per_bp)
        insert_mass_ng = insert_mass_g * 1e9
        vector_vol = vector_mass_ng / vector_conc
        insert_vol = insert_mass_ng / insert_conc
        print(f"\n✅ Results:")
        print(f"Vector: {vector_mass_ng:.2f} ng ({vector_vol:.2f} µL at {vector_conc} ng/µL)")
        print(f"Insert: {insert_mass_ng:.2f} ng ({insert_vol:.2f} µL at {insert_conc} ng/µL)")
        return {
            "vector_mass": vector_mass_ng,
            "vector_vol": vector_vol,
            "vector_conc": vector_conc,
            "insert_mass": insert_mass_ng,
            "insert_vol": insert_vol,
            "insert_conc": insert_conc
        }
    except ValueError as e:
        print(f"❌ Error: {str(e)}")
        return None

def ligation_setup(ivr_results):
    """Set up ligation reaction using insert:vector ratio results."""
    try:
        print("\n🧪 Ligation Reaction Setup (using previous Insert:Vector Ratio results)")
        total_vol = float(input("Enter desired total ligation reaction volume (µL) [default 20]: ") or 20)
        if total_vol <= 0:
            raise ValueError("Total volume must be positive.")
        ligase_vol = float(input("Enter desired total ligase volume (µL): "))
        if ligase_vol <= 0:
            raise ValueError("Ligase volume must be positive.")
        vector_vol = ivr_results["vector_vol"]
        insert_vol = ivr_results["insert_vol"]
        ligase_buffer_vol = total_vol * 0.1
        water_vol = total_vol - (vector_vol + insert_vol + ligase_buffer_vol + ligase_vol)
        if water_vol < 0:
            raise ValueError("Calculated water volume is negative; check inputs.")
        print(f"\n✅ Recommended Ligation Reaction Setup:")
        print(f"Vector DNA: {ivr_results['vector_mass']:.2f} ng ({vector_vol:.2f} µL at {ivr_results['vector_conc']} ng/µL)")
        print(f"Insert DNA: {ivr_results['insert_mass']:.2f} ng ({insert_vol:.2f} µL at {ivr_results['insert_conc']} ng/µL)")
        print(f"10× Ligase Buffer: {ligase_buffer_vol:.2f} µL")
        print(f"T4 DNA Ligase: {ligase_vol:.2f} µL")
        print(f"Water: {water_vol:.2f} µL")
    except ValueError as e:
        print(f"❌ Error: {str(e)}")

def annealing_calculator():
    """Calculate volumes for oligo annealing reaction."""
    try:
        print("\n🧪 Oligo Annealing Calculator")
        oligo1_conc = float(input("Enter oligo 1 stock concentration (µM): "))
        if oligo1_conc <= 0:
            raise ValueError("Oligo 1 concentration must be positive.")
        oligo2_conc = float(input("Enter oligo 2 stock concentration (µM): "))
        if oligo2_conc <= 0:
            raise ValueError("Oligo 2 concentration must be positive.")
        desired_conc = float(input("Enter desired final annealed oligo concentration (µM): "))
        if desired_conc <= 0:
            raise ValueError("Desired concentration must be positive.")
        final_vol = float(input("Enter desired final reaction volume (µL): "))
        if final_vol <= 0:
            raise ValueError("Final volume must be positive.")
        oligo1_vol = (desired_conc * final_vol) / oligo1_conc
        oligo2_vol = (desired_conc * final_vol) / oligo2_conc
        water_vol = final_vol - oligo1_vol - oligo2_vol
        if water_vol < 0:
            raise ValueError("Calculated water volume is negative; check concentrations.")
        print(f"\n✅ Results:")
        print(f"Oligo 1: {oligo1_vol:.2f} µL at {oligo1_conc} µM")
        print(f"Oligo 2: {oligo2_vol:.2f} µL at {oligo2_conc} µM")
        print(f"Water: {water_vol:.2f} µL")
    except ValueError as e:
        print(f"❌ Error: {str(e)}")

def restriction_digest_calculator():
    """Calculate reagent volumes for a restriction digest reaction, scaling total volume by DNA mass."""
    try:
        print("\n🧬 Restriction Digest Calculator")
        print("-------------------------------")
        print("Calculates reagent volumes and total volume scaled by DNA mass (reference: 1 µg DNA in 50 µL reaction).")
        dna_mass_ng = float(input("Enter DNA mass (ng): "))
        if dna_mass_ng <= 0:
            raise ValueError("DNA mass must be positive.")
        if dna_mass_ng < 100:
            print("Warning: DNA mass <100 ng may yield suboptimal results.")
        dna_conc_ng_ul = float(input("Enter DNA concentration (ng/µL): "))
        if dna_conc_ng_ul <= 0:
            raise ValueError("DNA concentration must be positive.")
        dna_mass_ug = dna_mass_ng / 1000.0
        reference_dna_mass_ug = 1.0
        reference_total_vol_ul = 50.0
        scale_factor = dna_mass_ug / reference_dna_mass_ug
        total_vol_ul = reference_total_vol_ul * scale_factor
        dna_vol_ul = dna_mass_ng / dna_conc_ng_ul
        if dna_vol_ul >= total_vol_ul:
            raise ValueError("DNA volume exceeds calculated total volume; increase DNA concentration.")
        buffer_vol_ul = total_vol_ul * 0.1
        reference_enzyme_vol_ul = 1.0
        enzyme_vol_ul = reference_enzyme_vol_ul * scale_factor
        enzyme_vol_ul = min(enzyme_vol_ul, total_vol_ul * 0.1)
        water_vol_ul = total_vol_ul - (dna_vol_ul + buffer_vol_ul + enzyme_vol_ul)
        if water_vol_ul < 0:
            raise ValueError("Calculated water volume is negative; increase DNA concentration.")
        print(f"\n✅ Recommended Restriction Digest Setup (scaled for {dna_mass_ng:.2f} ng DNA):")
        print(f"DNA: {dna_mass_ng:.2f} ng ({dna_vol_ul:.2f} µL at {dna_conc_ng_ul:.2f} ng/µL)")
        print(f"10X NEBuffer: {buffer_vol_ul:.2f} µL (1X final concentration)")
        print(f"Restriction Enzyme: {enzyme_vol_ul:.2f} µL")
        print(f"Nuclease-free Water: {water_vol_ul:.2f} µL")
        print(f"Total Volume: {total_vol_ul:.2f} µL")
        print("Note: Add enzyme last and keep reaction on ice.")
        return {
            "dna_mass_ng": dna_mass_ng,
            "dna_vol_ul": dna_vol_ul,
            "dna_conc_ng_ul": dna_conc_ng_ul,
            "buffer_vol_ul": buffer_vol_ul,
            "enzyme_vol_ul": enzyme_vol_ul,
            "water_vol_ul": water_vol_ul,
            "total_vol_ul": total_vol_ul
        }
    except ValueError as e:
        print(f"❌ Error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def restriction_ligation():
    """Menu for restriction and ligation calculations."""
    ivr_results = None
    while True:
        print("\n🧬 Restriction/Ligation Calculator")
        print("-------------------------------")
        print("1. Insert:Vector Ratio Calculator")
        print("2. Oligo Annealing Calculator")
        print("3. Ligation Reaction Setup")
        print("4. Restriction Digest Calculator")
        print("5. Back to Main Menu")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            ivr_results = insert_vector_ratio()
        elif choice == "2":
            annealing_calculator()
        elif choice == "3":
            if ivr_results:
                ligation_setup(ivr_results)
            else:
                print("⚠️ Please run Insert:Vector Ratio Calculator first.")
        elif choice == "4":
            restriction_digest_calculator()
        elif choice == "5":
            break
        else:
            print("⚠️ Invalid choice. Please try again.")


def gibson_assembly():
    """Calculate volumes for Gibson assembly with adjustable molar ratios."""
    try:
        print("\n🧪 Gibson Assembly Calculator")
        num_fragments = int(input("Enter number of fragments: "))
        if num_fragments < 2:
            raise ValueError("Number of fragments must be at least 2.")

        fragments = []
        total_size = 0

        for i in range(num_fragments):
            size = int(input(f"Enter size of fragment {i + 1} (bp): "))
            if size <= 0:
                raise ValueError(f"Fragment {i + 1} size must be positive.")
            conc = float(input(f"Enter DNA concentration of fragment {i + 1} (ng/µL): "))
            if conc <= 0:
                raise ValueError(f"Fragment {i + 1} concentration must be positive.")
            fragments.append((size, conc))
            total_size += size

        if total_size == 0:
            raise ValueError("Total fragment size cannot be zero.")

        # NEW: Get desired molar ratios
        print(f"\n🔬 Molar Ratio Setup:")
        print("Enter desired molar ratios for each fragment")
        print("(e.g., enter '3' for 3x more, '0.5' for half as much)")

        ratios = []
        for i in range(num_fragments):
            ratio = float(input(f"Molar ratio for fragment {i + 1} (default 1.0): ") or "1.0")
            if ratio <= 0:
                raise ValueError(f"Ratio for fragment {i + 1} must be positive.")
            ratios.append(ratio)

        desired_total_volume = float(input("Enter desired total reaction volume (µL): "))
        if desired_total_volume <= 0:
            raise ValueError("Total volume must be positive.")

        # Calculate base reference amount (smallest fragment at ratio 1.0)
        min_ratio = min(ratios)
        base_pmol = 0.1  # Base picomoles to work from

        # Calculate adjusted pmols and ng for each fragment
        adjusted_pmols = [base_pmol * ratio / min_ratio for ratio in ratios]
        adjusted_ng = []
        fragment_volumes = []

        for i, (size, conc) in enumerate(fragments):
            ng = adjusted_pmols[i] * size * 650 / 1000
            vol = ng / conc
            adjusted_ng.append(ng)
            fragment_volumes.append(vol)

        # Calculate scaling factor for desired volume
        current_total_volume = sum(fragment_volumes)
        scale_factor = desired_total_volume / current_total_volume

        print(f"\n✅ Gibson Assembly Setup with Custom Ratios:")
        print(f"📊 Scaling factor: {scale_factor:.2f}x")
        print(f"📏 Total volume: {desired_total_volume} µL")
        print(f"🧬 Total size: {total_size:,} bp")
        print("-" * 80)

        total_pmol = 0

        for idx, (size, conc) in enumerate(fragments):
            scaled_ng = adjusted_ng[idx] * scale_factor
            scaled_vol = fragment_volumes[idx] * scale_factor
            scaled_pmol = adjusted_pmols[idx] * scale_factor
            total_pmol += scaled_pmol

            print(f"Fragment {idx + 1}: {scaled_ng:.2f} ng ({scaled_vol:.2f} µL)")
            print(f"   📏 Size: {size:,} bp")
            print(f"   🧪 Concentration: {conc} ng/µL")
            print(f"   ⚗️  Amount: {scaled_pmol:.3f} pmol")
            print(f"   📊 Molar ratio: {ratios[idx]:.1f}x")
            print()

        # Summary with ratio information
        print("-" * 80)
        print(f"📊 SUMMARY:")
        print(f"   Total pmols: {total_pmol:.3f} pmol")
        print(f"   Molar ratios: {':'.join(f'{r:.1f}' for r in ratios)}")

        # Show actual molar ratios achieved
        actual_ratios = [p / min(adjusted_pmols) for p in adjusted_pmols]
        print(f"   Actual ratios: {':'.join(f'{r:.1f}' for r in actual_ratios)}")

    except ValueError as e:
        print(f"❌ Error: {str(e)}")



def design_crispr_grna_primers(vector_sequence=None, grna_spacer=None, crispr_repeat_length=22, max_primer_length=60, interactive=True):
    """
    Design Gibson assembly primers for inserting gRNA spacers between CRISPR repeats.
    
    This function generates forward and reverse primers that include:
    - CRISPR repeat sequence (homology arm for Gibson assembly)
    - gRNA spacer sequence (the guide RNA targeting sequence)
    
    Parameters:
    -----------
    vector_sequence : str, optional
        Full vector sequence containing two CRISPR repeats with spacer between them.
        Format: ...CRISPR_repeat1...spacer...CRISPR_repeat2...
    grna_spacer : str, optional
        gRNA spacer sequence (28-32 bp recommended). If None and interactive=True, will prompt user.
    crispr_repeat_length : int
        Length of CRISPR repeat to use for homology (default: 22 bp)
    max_primer_length : int
        Maximum allowed primer length (default: 60 bp)
    interactive : bool
        If True, prompts user for input. If False, requires vector_sequence and grna_spacer.
    
    Returns:
    --------
    dict : Dictionary containing primer sequences and metadata, or None if error
    
    Example:
    --------
    >>> results = design_crispr_grna_primers(
    ...     vector_sequence="cggtgaactgccgagtaggtagctgataacgagacctcgtttacctatcggtctcgtgaactgccgagtaggtagctgataacc",
    ...     grna_spacer="GATGCTGGGGATGGACTTCAACATATCCTC",
    ...     interactive=False
    ... )
    >>> print(results['forward_primer'])
    """
    
    def reverse_complement_dna(seq):
        """Return the reverse complement of a DNA sequence."""
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
                      'a': 't', 't': 'a', 'g': 'c', 'c': 'g'}
        return ''.join(complement.get(base, base) for base in reversed(seq))
    
    def validate_dna_sequence(seq, name, min_len=None, max_len=None):
        """Validate DNA sequence."""
        valid_bases = set('ATGCatgc')
        if not all(base in valid_bases for base in seq):
            raise ValueError(f"{name} contains invalid characters. Use only A, T, G, C.")
        
        if min_len and len(seq) < min_len:
            raise ValueError(f"{name} is too short ({len(seq)} bp). Minimum: {min_len} bp.")
        
        if max_len and len(seq) > max_len:
            raise ValueError(f"{name} is too long ({len(seq)} bp). Maximum: {max_len} bp.")
        
        return seq.upper()
    
    def find_crispr_repeats(vector_seq, repeat_pattern):
        """Find the two CRISPR repeat positions in the vector."""
        vector_upper = vector_seq.upper()
        repeat_upper = repeat_pattern.upper()
        
        first_pos = vector_upper.find(repeat_upper)
        if first_pos == -1:
            raise ValueError(f"Could not find CRISPR repeat pattern in vector sequence")
        
        second_pos = vector_upper.find(repeat_upper, first_pos + len(repeat_upper))
        if second_pos == -1:
            raise ValueError(f"Could not find second CRISPR repeat in vector sequence")
        
        return first_pos, second_pos
    
    try:
        print("\n🧬 CRISPR gRNA Gibson Assembly Primer Designer")
        
        # Get input sequences
        if interactive:
            if vector_sequence is None:
                print("\nEnter the full vector sequence containing two CRISPR repeats:")
                print("(Format: ...CRISPR_repeat1...old_spacer...CRISPR_repeat2...)")
                vector_sequence = input("> ").strip()
            if grna_spacer is None:
                grna_spacer = input("Enter gRNA spacer sequence (28-32 bp, keep seed sequence intact): ").strip()
        else:
            if vector_sequence is None or grna_spacer is None:
                raise ValueError("vector_sequence and grna_spacer must be provided when interactive=False")
        
        # Validate inputs
        vector_sequence = validate_dna_sequence(vector_sequence, "Vector sequence")
        grna_spacer = validate_dna_sequence(grna_spacer, "gRNA spacer", min_len=28, max_len=32)
        
        # Find the CRISPR repeats - use the known repeat pattern
        # The CRISPR repeat pattern we're looking for
        crispr_repeat_pattern = "GTGAACTGCCGAGTAGGTAGCTGATAAC"
        
        first_repeat_pos, second_repeat_pos = find_crispr_repeats(vector_sequence, crispr_repeat_pattern)
        
        # Extract the appropriate regions for homology arms
        # Forward primer: last 22 bp of first CRISPR repeat
        first_repeat_end = first_repeat_pos + len(crispr_repeat_pattern)
        forward_homology = vector_sequence[first_repeat_end - crispr_repeat_length:first_repeat_end]
        
        # Reverse primer: first 22 bp of second CRISPR repeat
        reverse_homology = vector_sequence[second_repeat_pos:second_repeat_pos + crispr_repeat_length]
        
        # Generate primers
        # Forward primer: gRNA spacer first, then homology arm (last 22 bp of first repeat)
        forward_primer = grna_spacer + forward_homology
        
        # Reverse primer: gRNA spacer RC first, then homology arm RC (first 22 bp of second repeat, RC)
        reverse_primer = reverse_complement_dna(grna_spacer) + reverse_complement_dna(reverse_homology)
        
        # Check primer lengths
        if len(forward_primer) > max_primer_length:
            raise ValueError(f"Forward primer ({len(forward_primer)} bp) exceeds maximum length ({max_primer_length} bp)")
        
        if len(reverse_primer) > max_primer_length:
            raise ValueError(f"Reverse primer ({len(reverse_primer)} bp) exceeds maximum length ({max_primer_length} bp)")
        
        # Compile results
        results = {
            'vector_sequence': vector_sequence,
            'first_repeat_position': first_repeat_pos,
            'second_repeat_position': second_repeat_pos,
            'forward_homology': forward_homology,
            'reverse_homology': reverse_homology,
            'grna_spacer': grna_spacer,
            'grna_spacer_length': len(grna_spacer),
            'seed_sequence': grna_spacer[:8],
            'forward_primer': forward_primer,
            'forward_primer_length': len(forward_primer),
            'reverse_primer': reverse_primer,
            'reverse_primer_length': len(reverse_primer),
            'expected_insert_size': crispr_repeat_length * 2 + len(grna_spacer)
        }
        
        # Print results
        print("\n✅ CRISPR gRNA Primer Design Results")
        print("=" * 80)
        
        print("\n📋 INPUT SEQUENCES:")
        print(f"  Vector length:    {len(vector_sequence)} bp")
        print(f"  First repeat at:  position {first_repeat_pos}")
        print(f"  Second repeat at: position {second_repeat_pos}")
        print(f"  gRNA Spacer:      {results['grna_spacer']} ({results['grna_spacer_length']} bp)")
        print(f"  Seed Sequence:    {results['seed_sequence']} (first 8 bp)")
        
        print("\n🧬 HOMOLOGY ARMS EXTRACTED:")
        print(f"  Forward homology (last {crispr_repeat_length} bp of repeat 1): {forward_homology}")
        print(f"  Reverse homology (first {crispr_repeat_length} bp of repeat 2): {reverse_homology}")
        
        print("\n🧬 GENERATED PRIMERS:")
        print(f"\n  Forward Primer ({results['forward_primer_length']} bp):")
        print(f"  5'-{results['forward_primer']}-3'")
        print(f"      └─ gRNA spacer ({len(grna_spacer)} bp):   {results['grna_spacer']}")
        print(f"      └─ Homology arm ({crispr_repeat_length} bp): {forward_homology}")
        
        print(f"\n  Reverse Primer ({results['reverse_primer_length']} bp):")
        print(f"  5'-{results['reverse_primer']}-3'")
        print(f"      └─ gRNA spacer RC ({len(grna_spacer)} bp):   {reverse_complement_dna(results['grna_spacer'])}")
        print(f"      └─ Homology arm RC ({crispr_repeat_length} bp): {reverse_complement_dna(reverse_homology)}")
        
        print("\n📊 EXPECTED PRODUCT:")
        print(f"  Insert size: {results['expected_insert_size']} bp")
        print(f"  Structure: [First CRISPR repeat]-[gRNA spacer]-[Second CRISPR repeat]")
        
        print("\n💡 VALIDATION SUGGESTIONS:")
        print(f"  1. Colony PCR with flanking primers (expected: ~{len(crispr_repeat_pattern)*2 + len(grna_spacer)} bp)")
        print("  2. Sanger sequencing to confirm gRNA sequence")
        print("  3. Functional validation via CRISPR activity assay")
        
        print("=" * 80)
        
        return results
        
    except ValueError as e:
        print(f"❌ Error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def main():
    """Main menu for the cloning calculator suite."""
    while True:
        print("\n🧬 Cloning Calculator Suite")
        print("----------------------------")
        print("What type of cloning are you doing?")
        print("1. Gibson Assembly")
        print("2. Restriction/Ligation cloning")
        print("3. PCR Master Mix & Thermocycler Program Calculator")
        print("4. CRISPR gRNA Primer Designer (Gibson Assembly)")
        print("5. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            gibson_assembly()
        elif choice == "2":
            restriction_ligation()
        elif choice == "3":
            pcr_mastermix_calculator()
        elif choice == "4":
            design_crispr_grna_primers()
        elif choice == "5":
            print("👋 Exiting. Good luck with your cloning!")
            break
        else:
            print("⚠️ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()