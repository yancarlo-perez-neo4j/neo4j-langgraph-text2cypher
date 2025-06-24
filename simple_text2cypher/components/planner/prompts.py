from langchain_core.prompts import ChatPromptTemplate

planner_system = """
You must analyze the input question and break it into individual sub tasks.
If appropriate independent tasks exist, then provide them as a list, otherwise return an empty list.
Tasks should NOT be dependent on each other.
Return a list of tasks to be completed.
"""


def create_planner_prompt_template() -> ChatPromptTemplate:
    """
    Create a planner prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    message = """Rules:
* Ensure that the tasks are not returning duplicated or similar information.
* Ensure that tasls are NOT dependent on information gathered from other tasks!
* tasks that are dependent on each other should be combined into a single question.
* tasks that return the same information should be combined into a single question.

question: {question}
"""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                planner_system,
            ),
            (
                "human",
                (message),
            ),
        ]
    )
