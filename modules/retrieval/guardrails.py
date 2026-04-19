import re

class Guardrails:
    def __init__(self, llm):
        self.llm = llm

    def scrub_pii(self, query: str) -> str:
        """Removes potential PII like PAN and Aadhaar from the query."""
        pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
        aadhaar_pattern = r'\b[0-9]{12}\b'
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        query = re.sub(pan_pattern, "[REDACTED_ID]", query, flags=re.IGNORECASE)
        query = re.sub(aadhaar_pattern, "[REDACTED_ID]", query)
        query = re.sub(email_pattern, "[REDACTED_EMAIL]", query)
        
        return query

    def is_factual_intent(self, query: str) -> bool:
        """Returns True if the query is factual, False if advisory/subjective."""
        prompt = f"""You are a security guard for a Mutual Fund FAQ assistant. 
        Analyze the user query: "{query}"
        Does this query ask for:
        1. Investment advice or specific recommendations? ("Should I buy?", "Is this good?")
        2. Relative comparisons or qualitative evaluations? ("Which is better?", "Which is safer?", "Is A better than B?")
        3. Performance predictions or opinions?
        4. Personal account private data?

        If it asks for ANY of the above, reply with "ADVICE".
        If it asks for ONLY OBJECTIVE FACTS found in a factsheet (expense ratio, exit load, SIP amount, lock-in, benchmark), reply with "FACTUAL".
        
        Response (one word only):"""
        
        response = self.llm.invoke(prompt).content.strip().upper()
        return "FACTUAL" in response
