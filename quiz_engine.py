from youtube_transcript_api import YouTubeTranscriptApi
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from datetime import datetime
import random
import os
import json

load_dotenv(override=True)
groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=groq_api_key
)

def get_video_id(url):
    if "v=" in url:
        video_id = url.split("v=")[1]
        video_id = video_id.split("&")[0]
        return video_id
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1]
        video_id = video_id.split("?")[0]
        return video_id
    else:
        return None

def get_transcript(url):
    video_id = get_video_id(url)
    if not video_id:
        return None
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        return transcript
    except Exception as e:
        return None

def chunk_transcript(transcript, chunk_duration=120):
    chunks = []
    current_text = ""
    chunk_start = transcript[0].start
    for segment in transcript:
        if segment.start - chunk_start >= chunk_duration:
            chunks.append({
                "text": current_text.strip(),
                "start": chunk_start,
                "end": segment.start
            })
            current_text = segment.text + " "
            chunk_start = segment.start
        else:
            current_text += segment.text + " "
    if current_text:
        chunks.append({
            "text": current_text.strip(),
            "start": chunk_start,
            "end": transcript[-1].start
        })
    return chunks

class TranscriptionAgent:
    def __init__(self):
        self.name = "Transcription Agent"
    
    def run(self, url):
        transcript = get_transcript(url)
        if not transcript:
            return None
        chunks = chunk_transcript(transcript)
        return chunks

class FilterAgent:
    def __init__(self, llm):
        self.name = "Filter Agent"
        self.llm = llm
    
    def run(self, chunks):
        educational_chunks = []
        for chunk in chunks:
            try:
                prompt = f"""Look at this transcript section and decide if it contains actual educational content or if it is filler content.
Filler content includes: introductions, outros, subscribe reminders, agenda overview, quiz segments, promotions, greetings, channel promotions, "like and share" requests, or any non-teaching content.
IMPORTANT: If the section contains ANY educational explanation, concepts, or teaching, even if mixed with casual talk, mark it as "educational".
Only mark as "skip" if the ENTIRE section is filler with NO educational value.
Transcript:
{chunk['text']}
Reply with ONLY one word: "educational" or "skip"
"""
                response = self.llm.invoke(prompt)
                content = response.content.strip().lower()
                if content == "educational":
                    educational_chunks.append(chunk)
            except Exception as e:
                educational_chunks.append(chunk)
        return educational_chunks

class ConceptExtractionAgent:
    def __init__(self, llm):
        self.name = "Concept Extraction Agent"
        self.llm = llm
    
    def run(self, chunks):
        all_concepts = []
        for chunk in chunks:
            try:
                start_min = int(chunk["start"] // 60)
                start_sec = int(chunk["start"] % 60)
                end_min = int(chunk["end"] // 60)
                end_sec = int(chunk["end"] % 60)
                timestamp = f"{start_min}:{start_sec:02d} - {end_min}:{end_sec:02d}"
                
                prompt = f"""Extract the 2-3 most important concepts or topics from this transcript section.
Transcript:
{chunk['text']}
Return ONLY JSON in this format:
{{"concepts": ["concept 1", "concept 2", "concept 3"]}}
"""
                response = self.llm.invoke(prompt)
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                concepts = json.loads(content)
                concepts["timestamp"] = timestamp
                all_concepts.append(concepts)
            except Exception as e:
                continue
        return all_concepts

class QuestionGenerationAgent:
    def __init__(self, llm):
        self.name = "Question Generation Agent"
        self.llm = llm
    
    def shuffle_options(self, question):
        options = list(question["options"].items())
        random.shuffle(options)
        old_correct = question["correct_answer"]
        correct_text = question["options"][old_correct]
        new_options = {}
        new_correct = None
        for i, (_, text) in enumerate(options):
            letter = ["A", "B", "C", "D"][i]
            new_options[letter] = text
            if text == correct_text:
                new_correct = letter
        question["options"] = new_options
        question["correct_answer"] = new_correct
        return question
    
    def run(self, concepts_list):
        all_questions = []
        for item in concepts_list:
            try:
                concepts = ", ".join(item["concepts"])
                timestamp = item["timestamp"]
                prompt = f"""Generate 1 multiple choice question that tests understanding of these concepts: {concepts}
The question should have:
- 4 options (A, B, C, D)
- The correct answer
- An explanation of why that answer is correct
Return ONLY JSON in this format:
{{
    "question": "the question text",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_answer": "B",
    "explanation": "why this is correct"
}}
"""
                response = self.llm.invoke(prompt)
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                question = json.loads(content)
                question = self.shuffle_options(question)
                question["timestamp"] = timestamp
                question["concepts"] = item["concepts"]
                all_questions.append(question)
            except Exception as e:
                continue
        return {"questions": all_questions}

class EvaluationAgent:
    def __init__(self, llm):
        self.name = "Evaluation Agent"
        self.llm = llm
    
    def deduplicate_topics(self, weak_topics):
        prompt = f"""Here is a list of topics:
{weak_topics}
Group similar or related topics together and give me a clean, 
deduplicated list. Combine topics that mean the same thing into 
one clear topic name.
Return ONLY JSON in this format:
{{"topics": ["topic 1", "topic 2", "topic 3"]}}
"""
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            result = json.loads(content)
            return result["topics"]
        except Exception as e:
            return weak_topics
    
    def evaluate(self, quiz_data, user_answers):
        score = 0
        weak_topics = []
        results = []
        
        for i, q in enumerate(quiz_data["questions"]):
            user_answer = user_answers[i].upper()
            is_correct = user_answer == q["correct_answer"]
            
            if is_correct:
                score += 1
            else:
                weak_topics.extend(q.get("concepts", []))
            
            results.append({
                "question": q["question"],
                "user_answer": user_answer,
                "correct_answer": q["correct_answer"],
                "is_correct": is_correct,
                "explanation": q["explanation"],
                "timestamp": q["timestamp"]
            })
        
        weak_topics = list(set(weak_topics))
        if weak_topics:
            weak_topics = self.deduplicate_topics(weak_topics)
        
        return {
            "score": score,
            "total": len(quiz_data["questions"]),
            "weak_topics": weak_topics,
            "details": results
        }

class QuizTracker:
    def __init__(self, filename="quiz_history.json"):
        self.filename = filename
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def save_result(self, url, score, total, weak_topics, all_topics):
        result = {
            "url": url,
            "score": score,
            "total": total,
            "weak_topics": weak_topics,
            "all_topics": all_topics,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.history.append(result)
        with open(self.filename, "w") as f:
            json.dump(self.history, f, indent=2)
    
    def get_weak_topics(self):
        all_weak = []
        for entry in self.history:
            all_weak.extend(entry["weak_topics"])
        return list(set(all_weak))
    
    def get_history(self):
        return self.history
    
    def get_progress(self):
        topic_stats = {}
        for entry in self.history:
            for topic in entry.get("all_topics", []):
                if topic not in topic_stats:
                    topic_stats[topic] = {"attempted": 0, "failed": 0}
                topic_stats[topic]["attempted"] += 1
                if topic in entry["weak_topics"]:
                    topic_stats[topic]["failed"] += 1
        return topic_stats