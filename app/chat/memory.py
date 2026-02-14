from langchain_core.messages import AIMessage, HumanMessage

from app.enums import SenderType


def build_history(messages: list) -> list:
    history = []
    for message in messages:
        if message.sender == SenderType.USER:
            history.append(HumanMessage(content=message.content))
        else:
            history.append(AIMessage(content=message.content))
    return history
