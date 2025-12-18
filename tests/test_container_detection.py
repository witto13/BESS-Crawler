"""
Unit tests for container detection.
"""
import unittest
from apps.extract.container_detection import is_container, has_required_procedure_signal, is_valid_procedure


class TestContainerDetection(unittest.TestCase):
    
    def test_amtsblatt_container(self):
        """Test that Amtsblatt issue titles are detected as containers."""
        title = "Amtsblatt Ausgabe 12/2023"
        url = "https://example.de/amtsblatt/12-2023.pdf"
        
        self.assertTrue(is_container(title.lower(), url, "AMTSBLATT"))
    
    def test_amtsblatt_with_procedure(self):
        """Test that Amtsblatt with procedure content is NOT a container."""
        title = "Amtsblatt Ausgabe 12/2023 - Aufstellungsbeschluss Bebauungsplan Nr. 5"
        url = "https://example.de/amtsblatt/12-2023.pdf"
        
        self.assertFalse(is_container(title.lower(), url, "AMTSBLATT"))
    
    def test_has_procedure_signal(self):
        """Test procedure signal detection."""
        classifier_result = {
            "procedure_type": "BPLAN_AUFSTELLUNG",
            "evidence_snippets": ["Aufstellungsbeschluss für Bebauungsplan Nr. 5"]
        }
        
        self.assertTrue(has_required_procedure_signal(classifier_result))
    
    def test_no_procedure_signal(self):
        """Test that missing procedure_type returns False."""
        classifier_result = {
            "procedure_type": None,
            "evidence_snippets": []
        }
        
        self.assertFalse(has_required_procedure_signal(classifier_result))
    
    def test_is_valid_procedure_container(self):
        """Test that container without procedure signal is invalid."""
        title = "Amtsblatt Ausgabe 12/2023"
        classifier_result = {
            "procedure_type": None,
            "evidence_snippets": []
        }
        
        is_valid, reason = is_valid_procedure(title.lower(), "https://example.de/amtsblatt.pdf", "AMTSBLATT", classifier_result, 0.1)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "SKIP_CONTAINER")
    
    def test_is_valid_procedure_with_signal(self):
        """Test that procedure with signal is valid."""
        title = "Aufstellungsbeschluss Bebauungsplan Nr. 5"
        classifier_result = {
            "procedure_type": "BPLAN_AUFSTELLUNG",
            "evidence_snippets": ["Aufstellungsbeschluss für Bebauungsplan"]
        }
        
        is_valid, reason = is_valid_procedure(title.lower(), "https://example.de/bplan.pdf", "MUNICIPAL_WEBSITE", classifier_result, 0.8)
        self.assertTrue(is_valid)
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()






