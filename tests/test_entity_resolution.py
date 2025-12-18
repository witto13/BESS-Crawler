"""
Unit tests for entity resolution.
"""
import unittest
from apps.extract.entity_resolution import (
    extract_plan_token,
    extract_parcel_token,
    normalize_company_name,
    extract_title_signature,
    compute_maturity_stage,
)


class TestEntityResolution(unittest.TestCase):
    
    def test_extract_plan_token(self):
        """Test plan token extraction."""
        title = "Aufstellungsbeschluss für Bebauungsplan Nr. 5"
        token = extract_plan_token(title)
        self.assertEqual(token, "5")
    
    def test_extract_parcel_token(self):
        """Test parcel token extraction."""
        location = "Gemarkung: Musterstadt; Flur: 3; Flurstück: 12/4"
        token = extract_parcel_token(location)
        self.assertIn("gemarkung=musterstadt", token)
        self.assertIn("flur=3", token)
        self.assertIn("flurstueck=12/4", token)
    
    def test_normalize_company_name(self):
        """Test company name normalization."""
        self.assertEqual(normalize_company_name("Example GmbH"), "example")
        self.assertEqual(normalize_company_name("Test AG"), "test")
        self.assertEqual(normalize_company_name("Company UG"), "company")
    
    def test_extract_title_signature(self):
        """Test title signature extraction."""
        title = "Aufstellungsbeschluss zur Beteiligung für Bebauungsplan Batteriespeicher"
        sig = extract_title_signature(title)
        self.assertIn("bebauungsplan", sig)
        self.assertIn("batteriespeicher", sig)
        self.assertNotIn("beteiligung", sig)  # Stop phrase removed
    
    def test_compute_maturity_stage(self):
        """Test maturity stage computation."""
        # Highest precedence
        self.assertEqual(compute_maturity_stage(["PERMIT_BAUGENEHMIGUNG"], None), "BAUGENEHMIGUNG")
        self.assertEqual(compute_maturity_stage(["PERMIT_BAUVORBESCHEID"], None), "BAUVORBESCHEID")
        self.assertEqual(compute_maturity_stage(["PERMIT_36_EINVERNEHMEN"], None), "PERMIT_36")
        self.assertEqual(compute_maturity_stage(["BPLAN_SATZUNG"], None), "BPLAN_SATZUNG")
        self.assertEqual(compute_maturity_stage(["BPLAN_AUFSTELLUNG"], None), "BPLAN_AUFSTELLUNG")
        
        # Default
        self.assertEqual(compute_maturity_stage([], None), "DISCOVERED")


if __name__ == "__main__":
    unittest.main()






