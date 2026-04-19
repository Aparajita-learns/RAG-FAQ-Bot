class Augmenter:
    def __init__(self, llm):
        self.llm = llm

    def generate_response(self, query: str, context: str):
        """Generates a facts-only response based on provided context."""
        system_prompt = f"""You are a factual Mutual Fund FAQ Assistant. 
        Use ONLY the provided context below to answer the user's question.
        Guidelines:
        - Max 3 sentences.
        - Be objective and technical.
        - Do NOT offer advice.
        - Do NOT include disclaimers about data being as of a specific date or AUM changes.
        - If the answer isn't in the context, say you don't know based on official factsheets.

        Context:
        {context}

        Question: {query}
        """

        response = self.llm.invoke(system_prompt).content.strip()
        return response
