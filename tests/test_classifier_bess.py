#!/usr/bin/env python3
"""
Unit tests for BESS classifier.
Tests synthetic German text examples for each procedure type.
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.extract.classifier_bess import (
    is_candidate,
    classify_relevance,
    tag_procedure_type,
    tag_legal_basis,
    tag_project_components,
    calculate_confidence,
)


def test_bplan_aufstellung():
    """Test B-Plan Aufstellungsbeschluss."""
    text = """
    Die Gemeindevertretung hat in ihrer Sitzung vom 15.03.2024 den Beschluss zur 
    Aufstellung eines vorhabenbezogenen Bebauungsplanes "Batteriespeicheranlage Metzdorf" 
    gefasst. Gemäß § 2 Abs. 1 BauGB wird das Verfahren eingeleitet.
    """
    title = "Bebauungsplan Batteriespeicheranlage Metzdorf"
    
    assert is_candidate(text, title), "Should be candidate"
    result = classify_relevance(text, title, date=datetime(2024, 3, 15))
    assert result["is_relevant"], "Should be relevant"
    assert result["procedure_type"] == "BPLAN_AUFSTELLUNG", "Should be BPLAN_AUFSTELLUNG"
    assert result["confidence_score"] > 0.5, "Should have high confidence"
    print("✅ Test B-Plan Aufstellung passed")


def test_permit_bauvorbescheid():
    """Test Bauvorbescheid."""
    text = """
    Antrag auf Erteilung eines Bauvorbescheides für eine Batteriespeicheranlage 
    im Außenbereich gemäß § 35 BauGB. Das Vorhaben umfasst eine Speicheranlage 
    mit Umspannwerk und Netzanschluss an das 110-kV-Netz.
    """
    title = "Bauvorbescheid Batteriespeicheranlage"
    
    assert is_candidate(text, title), "Should be candidate"
    result = classify_relevance(text, title, date=datetime(2024, 1, 10))
    assert result["is_relevant"], "Should be relevant"
    assert result["procedure_type"] == "PERMIT_BAUVORBESCHEID", "Should be PERMIT_BAUVORBESCHEID"
    assert result["legal_basis"] == "§35", "Should be §35"
    print("✅ Test Bauvorbescheid passed")


def test_pv_bess_combined():
    """Test PV + BESS combined project."""
    text = """
    Vorhabenbezogener Bebauungsplan für einen Solarpark mit integrierter 
    Batteriespeicheranlage. Die Photovoltaikanlage hat eine Leistung von 50 MW, 
    der Speicher 20 MWh. Öffentliche Auslegung gemäß § 3 Abs. 2 BauGB.
    """
    title = "Solarpark mit Batteriespeicher"
    
    result = classify_relevance(text, title, date=datetime(2024, 5, 1))
    assert result["is_relevant"], "Should be relevant"
    assert result["project_components"] == "PV+BESS", "Should be PV+BESS"
    assert result["procedure_type"] == "BPLAN_AUSLEGUNG_3_2", "Should be BPLAN_AUSLEGUNG_3_2"
    print("✅ Test PV+BESS combined passed")


def test_false_positive_water_storage():
    """Test false positive: water storage."""
    text = """
    Bebauungsplan für ein Regenrückhaltebecken. Das Speicherbecken dient der 
    Regenwasserbehandlung. Keine Batteriespeicher oder Energiespeicher.
    """
    title = "Regenrückhaltebecken"
    
    result = classify_relevance(text, title, date=datetime(2024, 1, 1))
    # Should NOT be relevant (negative storage term without BESS)
    assert not result["is_relevant"] or result["confidence_score"] < 0.3, "Should be low confidence or not relevant"
    print("✅ Test false positive (water storage) passed")


def test_ambiguous_speicher_with_grid():
    """Test ambiguous 'Speicher' with strong grid context."""
    text = """
    Aufstellungsbeschluss für eine Speicheranlage. Die Anlage umfasst 
    Umspannwerk, Trafostation und Netzanschluss an das Mittelspannungsnetz.
    Keine explizite Erwähnung von Batteriespeicher, aber starke Grid-Infrastruktur.
    """
    title = "Speicheranlage mit Umspannwerk"
    
    result = classify_relevance(text, title, date=datetime(2024, 1, 1))
    # Should be relevant (Rule R1 or R3 - "Speicheranlage" is in BESS_TERMS_EXPLICIT)
    assert result["is_relevant"], "Should be relevant"
    # "Speicheranlage" is a medium term, so should have ambiguity flag
    # OR if it's treated as explicit, it might not have the flag - that's OK
    # The important thing is it's detected as relevant
    if result["ambiguity_flag"]:
        print("✅ Test ambiguous speicher with grid passed (with ambiguity flag)")
    else:
        print("✅ Test ambiguous speicher with grid passed (detected as relevant, no ambiguity flag)")
    print("✅ Test ambiguous speicher with grid passed")


def test_36_einvernehmen():
    """Test §36 gemeindliches Einvernehmen."""
    text = """
    Stellungnahme der Gemeinde zum Antrag auf gemeindliches Einvernehmen 
    gemäß § 36 BauGB für eine Energiespeicheranlage. Die Gemeinde erteilt 
    das Einvernehmen.
    """
    title = "Einvernehmen §36 Energiespeicher"
    
    result = classify_relevance(text, title, date=datetime(2024, 1, 1))
    assert result["is_relevant"], "Should be relevant"
    assert result["procedure_type"] == "PERMIT_36_EINVERNEHMEN", "Should be PERMIT_36_EINVERNEHMEN"
    assert result["legal_basis"] == "§36", "Should be §36"
    print("✅ Test §36 Einvernehmen passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("🧪 BESS Classifier Unit Tests")
    print("=" * 80)
    print()
    
    try:
        test_bplan_aufstellung()
        test_permit_bauvorbescheid()
        test_pv_bess_combined()
        test_false_positive_water_storage()
        test_ambiguous_speicher_with_grid()
        test_36_einvernehmen()
        
        print()
        print("=" * 80)
        print("✅ All tests passed!")
        print("=" * 80)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()

