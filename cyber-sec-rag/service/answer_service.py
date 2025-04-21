from app_gem import gemini_model
import google.generativeai as genai

def generate_answer(query, context):
    prompt_template = """You are a cybersecurity expert assistant with deep technical knowledge. Your task is to provide comprehensive, detailed answers based on the context provided below.

    CONTEXT:
    {context}
    
    QUESTION:
    {question}
    
    Instructions:
    1. First, carefully analyze all the provided context fragments to gather relevant information.
    2. Synthesize a complete, well-structured answer that incorporates information from ALL relevant context fragments don't miss any useful information from context. 
    3. whenever necessary include specific details, examples, and technical explanations from the context do not generate the information by your knowledge. 
    4. Structure your answer with clear explanations of key concepts, and practical implications and do not generate information on your knowledge.
    5. Make your response detailed and thorough - aim for completeness rather than brevity.
    6. Use only information present in the context - do not add external knowledge.
    7. If the context is insufficient, clearly state I don not have sufficient information to answer, do not mention any other information.
    
    Provide a thorough, detailed response that fully addresses the question using all relevant information from the context:"""
    
    full_prompt = prompt_template.format(context=context, question=query)
    try:
        print(f"Generating answer for query: {query}, context length: {len(context)}")
        print(f"Prompt length: {len(full_prompt)}")
        response = gemini_model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=0.95,
                max_output_tokens=2048,
                presence_penalty=0.1,
                frequency_penalty=0.1
            ),
            stream=True
        )
        response_text = "".join([part.text for part in response])
        print(f"Generated answer: {response_text}")
        if not response_text.strip():
            return "No relevant information found in the context."
        return response_text
    except Exception as e:
        print(f"Gemini error: {str(e)}")
        raise RuntimeError(f"Error generating answer: {str(e)}")