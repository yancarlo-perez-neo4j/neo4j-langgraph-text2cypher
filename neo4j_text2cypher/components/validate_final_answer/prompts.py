from langchain.prompts import ChatPromptTemplate


def create_validate_final_answer_prompt_template() -> ChatPromptTemplate:
    """
    Create a validate final answer prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant.",
            ),
            (
                "human",
                (
                    """Your task is to validate whether the provided answer adequately addresses the user's question. 

VALIDATION CRITERIA - Answer is VALID if it:
1. Directly addresses the main question asked
2. Uses the retrieved data appropriately 
3. Acknowledges limitations when data is incomplete
4. Is clear and understandable

VALIDATION CRITERIA - Answer is INVALID only if it:
1. Completely ignores the question asked
2. Contains obvious factual errors from the data
3. Claims data exists when retrieved data is empty
4. Is incomprehensible or garbled

IMPORTANT GUIDELINES:
- Be GENEROUS in validation - minor gaps or style issues should NOT trigger reprocessing
- Do NOT require additional data unless the current answer is fundamentally inadequate
- Do NOT request more details for reasonable partial answers
- Consider the complexity of the question - some questions may not have complete answers in the data

Input Question: {question}

Answer: {answer}

Graph Schema:
{schema}

Retrieved Data:
{data}

Evaluate the answer using the criteria above. Only mark as invalid if there are serious issues that would genuinely confuse or mislead the user.

"""
                ),
            ),
        ]
    )
