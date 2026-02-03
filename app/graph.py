from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_KEY")
# openai_key = os.getenv("OPENAI_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY
)

# flake8: noqa
class HREvaluation(BaseModel):
    suitability_score: int = Field(
        description="0-100 score indicating overall suitability for the role"
    )

    hire_recommendation: str = Field(
        description="One of: Strong Yes / Yes / Maybe / No"
    )

    key_strengths: list[str] = Field(
        description="Specific skills, achievements, or experiences that strongly match the JD"
    )

    impressive_highlights: list[str] = Field(
        description="Notable projects, impact, leadership, or outcomes mentioned in resume"
    )

    missing_or_weak_areas: list[str] = Field(
        description="Important skills or experiences missing or weak compared to JD"
    )

    final_summary: str = Field(
        description="Short HR-style summary of whether to proceed or not"
    )


class State(TypedDict):
    jd_text: str
    resume_image_b64: str
    hr_evaluation: dict
    final_report: str
  
    
def hr_evaluate(state: State):
        
        system_prompt = '''
        You are an experienced HR partner, who thinks like an real life person who is a HR.
        You also have an understanding (example emotional) like a real life person. So that it helps you to make descision not completely based on technical skills.
        Your task is to-
        -Evaluate the give resume from an HR perspective.
        -Focus on if candidate is fit for the role comparing with job description, how much impact he can provide. In which area he lacks (e.g. experience)
        -You also compare the technical skills mentioned in resume with job description
        -You also go through the projects mentioned in resume which will help you to make a better overall decision.
        
        '''
        # aesa call krna refer Image & vision OpenAI page
        result = client.responses.parse(  
            model="gpt-5.2",
            input=[
                {"role":"system", "content": system_prompt},
                {"role":"user", "content":[
                    {"type":"input_text", "text":state['jd_text']},
                    {"type":"input_image",
                     "image_url":f"data:image/jpeg;base64,{state['resume_image_b64']}"}
                ]}
            ],
            text_format = HREvaluation,
        )
        
        print(result.output_parsed)
        state["hr_evaluation"] = result.output_parsed
        
        return state
    
    
def generate_report(state: State):
    e = state["hr_evaluation"]

    report = f"""
        ### Candidate Screening Report

        **Suitability Score:** {e.suitability_score}/100  
        **Recommendation:** {e.hire_recommendation}

        #### Why this candidate stands out
        - {chr(10).join(e.key_strengths)}

        #### Impressive Highlights
        - {chr(10).join(e.impressive_highlights)}

        #### Gaps / Missing Areas
        - {chr(10).join(e.missing_or_weak_areas)}

        **Final Summary:**  
        {e.final_summary}
    """
    state["final_report"]= report
    return state


graph_builder = StateGraph(State)

graph_builder.add_node("hr_evaluate",hr_evaluate)
graph_builder.add_node("generate_report",generate_report)

graph_builder.add_edge(START,"hr_evaluate")
graph_builder.add_edge("hr_evaluate","generate_report")
graph_builder.add_edge("generate_report",END)

def create_graph():
    return graph_builder.compile()


