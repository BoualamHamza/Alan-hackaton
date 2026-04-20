"""
Parses the MedlinePlus XML file and extracts health topics relevant to our demo.
Saves the result as a clean JSON file in data/medlineplus/topics.json
"""

import xml.etree.ElementTree as ET
import json
import os

# Pathologies and medications we want to cover for the demo
TARGET_KEYWORDS = [
    # Cardiovascular
    "hypertension", "high blood pressure", "heart disease", "heart attack",
    "stroke", "cholesterol", "atrial fibrillation",
    # Metabolic
    "diabetes", "obesity", "thyroid",
    # Respiratory
    "asthma", "pneumonia", "bronchitis", "copd",
    # Infections & antibiotics
    "antibiotic", "infection", "urinary tract",
    # Pain & inflammation
    "pain", "ibuprofen", "paracetamol", "acetaminophen",
    # Mental health
    "depression", "anxiety",
    # Common medications
    "metformin", "statins", "aspirin", "omeprazole", "amoxicillin",
    # General
    "prescription", "medication", "drug",
]


def parse_medlineplus_xml(xml_path: str, output_path: str) -> int:
    """
    Reads the MedlinePlus XML file, filters relevant topics,
    and saves them to a JSON file.
    Returns the number of topics extracted.
    """
    print(f"Parsing XML file: {xml_path}")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    topics = []

    for topic in root.findall("health-topic"):
        title = topic.get("title", "").lower()
        summary_el = topic.find("full-summary")
        summary = summary_el.text if summary_el is not None else ""

        if not summary:
            continue

        # Check if this topic matches any of our target keywords
        combined = title + " " + summary.lower()
        if not any(kw in combined for kw in TARGET_KEYWORDS):
            continue

        # Extract also-called terms (alternative names)
        also_called = [
            el.text for el in topic.findall("also-called") if el.text
        ]

        # Extract MeSH descriptors (medical classification terms)
        mesh_terms = [
            el.get("term", "") for el in topic.findall("mesh-heading/descriptor")
        ]

        topics.append({
            "id": topic.get("id"),
            "title": topic.get("title"),
            "url": topic.get("url"),
            "summary": summary.strip(),
            "also_called": also_called,
            "mesh_terms": mesh_terms,
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(topics)} relevant topics → {output_path}")
    return len(topics)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(base_dir, "../../../data/medlineplus/mplus_topics.xml")
    output_path = os.path.join(base_dir, "../../../data/medlineplus/topics.json")
    parse_medlineplus_xml(xml_path, output_path)
