from typing import TypedDict

class AgentState(TypedDict):
     question:str
     user: object
     sql:str
     result:dict
     answer:str
     intent:str
