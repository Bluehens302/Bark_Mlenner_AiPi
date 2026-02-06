#!/usr/bin/env python3
"""
SnapGene DNA File Annotator

This script reads a SnapGene .dna file and a FASTA file containing sequences,
then adds feature annotations and outputs a GenBank file (importable to SnapGene).

FASTA header format: >type|name|description
Example: >promoter|pTet|tetracycline-inducible promoter

Usage:
    GUI Mode (default):
        python annotate_snapgene.py

    GUI Mode (explicit):
        python annotate_snapgene.py --gui

    Command Line Mode:
        python annotate_snapgene.py input.dna sequences.fasta output.gb

Note: Output is GenBank format (.gb) which can be opened and saved as .dna in SnapGene
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from snapgene_reader import snapgene_file_to_seqrecord
from Bio.Seq import Seq
from Bio import SeqIO
from Bio.SeqFeature import SeqFeature, FeatureLocation
import tkinter as tk
from tkinter import filedialog


# Color mapping for different feature types (SnapGene RGB format)
FEATURE_COLORS = {
    'promoter': '#00FF00',      # Green
    'cds': '#FFFF00',           # Yellow
    'orf': '#FFFF00',           # Yellow (same as CDS)
    'terminator': '#FF0000',    # Red
    'rbs': '#0000FF',           # Blue
    'ribosome_binding': '#0000FF',  # Blue (alternative name)
}

DEFAULT_COLOR = '#808080'  # Gray for unknown types


def parse_fasta_header(header: str) -> Tuple[str, str, str]:
    """
    Parse FASTA header in format: >type|name|description

    Args:
        header: FASTA header string (with or without leading >)

    Returns:
        Tuple of (feature_type, name, description)
    """
    header = header.lstrip('>')
    parts = header.split('|', 2)

    if len(parts) >= 3:
        feature_type, name, description = parts
    elif len(parts) == 2:
        feature_type, name = parts
        description = ''
    elif len(parts) == 1:
        feature_type = 'unknown'
        name = parts[0]
        description = ''
    else:
        feature_type = 'unknown'
        name = header
        description = ''

    return feature_type.strip().lower(), name.strip(), description.strip()


def find_all_occurrences(sequence: str, pattern: str) -> List[int]:
    """
    Find all occurrences of pattern in sequence.

    Args:
        sequence: DNA sequence to search in
        pattern: DNA sequence pattern to find

    Returns:
        List of start positions (0-indexed)
    """
    positions = []
    start = 0
    while True:
        pos = sequence.find(pattern, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    return positions


def create_seqfeature(name: str, feature_type: str, start: int, end: int,
                     strand: int, description: str, color: str) -> SeqFeature:
    """
    Create a Biopython SeqFeature.

    Args:
        name: Feature name
        feature_type: Type of feature
        start: Start position (0-indexed)
        end: End position (0-indexed, exclusive)
        strand: 1 for forward, -1 for reverse
        description: Feature description
        color: Hex color code

    Returns:
        SeqFeature object
    """
    location = FeatureLocation(start, end, strand=strand)
    qualifiers = {
        'label': [name],
        'note': [description] if description else [],
        'ApEinfo_fwdcolor': [color],
        'ApEinfo_revcolor': [color]
    }
    return SeqFeature(location=location, type=feature_type, qualifiers=qualifiers)


def annotate_snapgene(snapgene_path: str, fasta_path: str, output_path: str):
    """
    Main function to annotate SnapGene file with sequences from FASTA.

    Args:
        snapgene_path: Path to input SnapGene .dna file
        fasta_path: Path to FASTA file with sequences
        output_path: Path to output GenBank file (readable by SnapGene)
    """
    print(f"Reading SnapGene file: {snapgene_path}")
    seqrecord = snapgene_file_to_seqrecord(snapgene_path)

    # Get the DNA sequence
    dna_sequence = str(seqrecord.seq).upper()
    if not dna_sequence:
        print("Error: No sequence found in SnapGene file")
        sys.exit(1)

    print(f"SnapGene sequence length: {len(dna_sequence)} bp")
    print(f"Existing features: {len(seqrecord.features)}")

    print(f"\nReading FASTA file: {fasta_path}")
    features_added = 0
    sequences_processed = 0
    sequences_not_found = 0

    # Parse FASTA file and search for each sequence
    for record in SeqIO.parse(fasta_path, 'fasta'):
        sequences_processed += 1

        # Parse header
        feature_type, name, description = parse_fasta_header(record.description)
        query_seq = str(record.seq).upper()

        # Get color for this feature type
        color = FEATURE_COLORS.get(feature_type, DEFAULT_COLOR)

        print(f"\nSearching for: {name} ({feature_type})")
        print(f"  Sequence length: {len(query_seq)} bp")

        # Search forward strand
        forward_matches = find_all_occurrences(dna_sequence, query_seq)
        if forward_matches:
            print(f"  Found {len(forward_matches)} match(es) on forward strand")
            for pos in forward_matches:
                feature = create_seqfeature(
                    name=name,
                    feature_type=feature_type,
                    start=pos,
                    end=pos + len(query_seq),
                    strand=1,
                    description=description,
                    color=color
                )
                seqrecord.features.append(feature)
                features_added += 1
                print(f"    Position: {pos + 1}-{pos + len(query_seq)} (+)")

        # Search reverse complement strand
        rev_comp_seq = str(Seq(query_seq).reverse_complement())
        reverse_matches = find_all_occurrences(dna_sequence, rev_comp_seq)
        if reverse_matches:
            print(f"  Found {len(reverse_matches)} match(es) on reverse strand")
            for pos in reverse_matches:
                feature = create_seqfeature(
                    name=name,
                    feature_type=feature_type,
                    start=pos,
                    end=pos + len(query_seq),
                    strand=-1,
                    description=description,
                    color=color
                )
                seqrecord.features.append(feature)
                features_added += 1
                print(f"    Position: {pos + 1}-{pos + len(query_seq)} (-)")

        if not forward_matches and not reverse_matches:
            sequences_not_found += 1
            # Silent skip as per user preference

    # Write output file as GenBank format
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Sequences processed: {sequences_processed}")
    print(f"  Sequences not found: {sequences_not_found}")
    print(f"  Features added: {features_added}")
    print(f"  Total features: {len(seqrecord.features)}")
    print(f"\nWriting output to: {output_path}")

    # Write as GenBank format (can be opened in SnapGene)
    with open(output_path, 'w', encoding='utf-8') as handle:
        SeqIO.write(seqrecord, handle, "genbank")
    print("Done!")
    print("\nNote: Output is in GenBank format (.gb), which can be opened in SnapGene.")


def select_file_gui(file_type: str, file_extensions: List[Tuple[str, str]]) -> str:
    """
    Open a file dialog to select a file.

    Args:
        file_type: Description of the file type (for dialog title)
        file_extensions: List of tuples (description, extension pattern)

    Returns:
        Selected file path or empty string if cancelled
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    file_path = filedialog.askopenfilename(
        title=f"Select {file_type}",
        filetypes=file_extensions
    )

    root.destroy()
    return file_path


def select_directory_gui() -> str:
    """
    Open a directory dialog to select an output directory.

    Returns:
        Selected directory path or empty string if cancelled
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    directory = filedialog.askdirectory(
        title="Select Output Directory"
    )

    root.destroy()
    return directory


def main():
    parser = argparse.ArgumentParser(
        description='Annotate SnapGene DNA files with features from FASTA sequences',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
FASTA Header Format:
  >type|name|description

  Example:
  >promoter|pTet|tetracycline-inducible promoter
  ATCGATCGATCG...

Supported Feature Types and Colors:
  - promoter (green)
  - cds/orf (yellow)
  - terminator (red)
  - rbs/ribosome_binding (blue)
  - unknown (gray)
        """
    )

    parser.add_argument('input_dna', nargs='?', help='Input SnapGene .dna file')
    parser.add_argument('fasta', nargs='?', help='FASTA file with sequences to annotate')
    parser.add_argument('output_gb', nargs='?', help='Output GenBank .gb file (importable to SnapGene)')
    parser.add_argument('--gui', action='store_true', help='Use graphical file selection dialogs')

    args = parser.parse_args()

    # If no arguments provided or --gui flag, use GUI mode
    use_gui = args.gui or not args.input_dna

    if use_gui:
        print("Starting file selection...")

        # Select SnapGene input file
        print("\nPlease select the SnapGene .dna file to annotate...")
        input_dna = select_file_gui(
            "SnapGene DNA File",
            [("SnapGene DNA Files", "*.dna"), ("All Files", "*.*")]
        )

        if not input_dna:
            print("No SnapGene file selected. Exiting.")
            sys.exit(0)

        print(f"Selected: {input_dna}")

        # Select FASTA file
        print("\nPlease select the FASTA file with sequences to annotate...")
        fasta = select_file_gui(
            "FASTA File",
            [("FASTA Files", "*.fasta *.fa *.fna"), ("All Files", "*.*")]
        )

        if not fasta:
            print("No FASTA file selected. Exiting.")
            sys.exit(0)

        print(f"Selected: {fasta}")

        # Select output directory
        print("\nPlease select the output directory...")
        output_dir = select_directory_gui()

        if not output_dir:
            print("No output directory selected. Exiting.")
            sys.exit(0)

        print(f"Selected: {output_dir}")

        # Create output filename based on input filename
        input_filename = Path(input_dna).stem
        output_dna = str(Path(output_dir) / f"{input_filename}_annotated.gb")

        print(f"\nOutput file will be: {output_dna}")

    else:
        # Use command line arguments
        input_dna = args.input_dna
        fasta = args.fasta
        output_dna = args.output_gb

        # Validate input files exist
        if not Path(input_dna).exists():
            print(f"Error: Input file not found: {input_dna}")
            sys.exit(1)

        if not Path(fasta).exists():
            print(f"Error: FASTA file not found: {fasta}")
            sys.exit(1)

    # Run annotation
    annotate_snapgene(input_dna, fasta, output_dna)


if __name__ == '__main__':
    main()
