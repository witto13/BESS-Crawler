"""
Optional LLM fallback for ambiguous cases (review_recommended=True).
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# LLM fallback is optional - can be implemented with OpenAI, Anthropic, etc.
# For now, this is a placeholder that returns None (no LLM call)

def llm_review(classifier_result: Dict, text: str, title: str) -> Optional[Dict]:
    """
    Optional LLM review for ambiguous cases.
    
    Args:
        classifier_result: Result from classify_relevance()
        text: Full text
        title: Title
        
    Returns:
        Dict with LLM answers or None if not implemented
    """
    if not classifier_result.get("review_recommended"):
        return None
    
    # Placeholder for LLM integration
    # Example with OpenAI:
    # import openai
    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     messages=[
    #         {"role": "system", "content": "Du bist ein Experte für deutsche Bauplanung..."},
    #         {"role": "user", "content": f"Ist dies über ein Batteriespeichersystem (Strom)?\n\nTitel: {title}\n\nText: {text[:2000]}"}
    #     ]
    # )
    # return {"llm_is_bess": ..., "llm_procedure_type": ...}
    
    logger.debug("LLM fallback requested but not implemented")
    return None






