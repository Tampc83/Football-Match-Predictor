from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import Client
from dotenv import load_dotenv
import os

load_dotenv()

class MatchPredictor:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in .env!")
        print(f"Using OpenAI model: gpt-4o")
        self.llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
        self.client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))
        self.prompt_template = PromptTemplate(
            input_variables=["team1", "team2", "stats"],
            template="""
            Analyze this club football match data for April 12, 2025, and predict the outcome. Your response MUST use this exact format:

            Prediction: [Team Name or Draw]
            Score: [e.g., 2-1]
            Corners: [Total, e.g., 8-12]
            Shots: [Total, e.g., 15-20]
            Reasoning: [Brief explanation, 2-4 sentences]

            Teams: {team1} vs {team2}
            Statistics: {stats}
            """
        )
        self.chain = RunnableSequence(self.prompt_template | self.llm)

    def predict_match(self, team1, team2, stats):
        try:
            inputs = {"team1": team1, "team2": team2, "stats": stats}
            prediction = self.chain.invoke(inputs)
            prediction_text = prediction.content if hasattr(prediction, 'content') else str(prediction)
            self.client.create_run(
                name="club_football_prediction",
                run_type="llm",
                inputs=inputs,
                outputs={"prediction": prediction_text}
            )
            return prediction
        except Exception as e:
            print(f"OpenAI or LangSmith error: {e}")
            return f"Prediction: [Error]\nReasoning: Unable to generate prediction due to: {e}"