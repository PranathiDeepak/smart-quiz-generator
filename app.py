from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from quiz_engine import (
    llm, TranscriptionAgent, FilterAgent, 
    ConceptExtractionAgent, QuestionGenerationAgent,
    EvaluationAgent, QuizTracker
)

app = FastAPI(title="Smart Quiz Generator API")

current_quiz = {}

class AnswerSubmission(BaseModel):
    url: str
    answers: List[str]

@app.get("/")
def home():
    return {"message": "Welcome to Smart Quiz Generator API"}

@app.get("/test")
def test():
    return {"status": "working"}

@app.get("/generate_quiz")
def generate_quiz(url: str, num_questions: int = 5):
    agent1 = TranscriptionAgent()
    chunks = agent1.run(url)
    if not chunks:
        return {"error": "Could not fetch transcript"}
    
    agent_filter = FilterAgent(llm)
    filtered_chunks = agent_filter.run(chunks)
    if not filtered_chunks:
        return {"error": "No educational content found"}
    
    total_chunks = len(filtered_chunks)
    if total_chunks <= num_questions:
        selected_chunks = filtered_chunks
    else:
        step = total_chunks // num_questions
        selected_chunks = [filtered_chunks[i * step] for i in range(num_questions)]
    
    agent2 = ConceptExtractionAgent(llm)
    concepts = agent2.run(selected_chunks)
    if not concepts:
        return {"error": "Could not extract concepts"}
    
    agent3 = QuestionGenerationAgent(llm)
    quiz = agent3.run(concepts)
    if not quiz or not quiz["questions"]:
        return {"error": "Could not generate questions"}
    
    current_quiz[url] = {
        "quiz": quiz,
        "filtered_chunks": filtered_chunks
    }
    
    display_questions = []
    for q in quiz["questions"]:
        display_questions.append({
            "question": q["question"],
            "options": q["options"]
        })
    
    return {
        "url": url,
        "num_questions": len(display_questions),
        "questions": display_questions
    }

@app.post("/submit_answers")
def submit_answers(submission: AnswerSubmission):
    if submission.url not in current_quiz:
        return {"error": "No quiz found for this URL. Generate a quiz first."}
    
    quiz_data = current_quiz[submission.url]["quiz"]
    
    if len(submission.answers) != len(quiz_data["questions"]):
        return {"error": f"Expected {len(quiz_data['questions'])} answers, got {len(submission.answers)}"}
    
    agent4 = EvaluationAgent(llm)
    results = agent4.evaluate(quiz_data, submission.answers)
    
    tracker = QuizTracker()
    all_topics = []
    for q in quiz_data["questions"]:
        all_topics.extend(q.get("concepts", []))
    all_topics = list(set(all_topics))
    tracker.save_result(submission.url, results["score"], results["total"], results["weak_topics"], all_topics)
    
    return results

@app.get("/get_history")
def get_history():
    tracker = QuizTracker()
    return {"history": tracker.get_history()}

@app.get("/get_progress")
def get_progress():
    tracker = QuizTracker()
    return {"progress": tracker.get_progress()}

@app.get("/get_weak_topics")
def get_weak_topics():
    tracker = QuizTracker()
    return {"weak_topics": tracker.get_weak_topics()}