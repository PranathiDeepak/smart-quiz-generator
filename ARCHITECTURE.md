\# Smart Quiz Generator - Agent Architecture



\## Agent 1: Transcription Agent

\- Input: YouTube URL

\- Task: Extract transcript and chunk it by timestamp

\- Output: Chunks with timestamps



\## Agent 2: Concept Extraction Agent

\- Input: Chunks with timestamps

\- Task: Identify key topics/concepts from each chunk

\- Output: Key concepts per chunk with timestamps



\## Agent 3: Question Generation Agent

\- Input: Concepts with timestamps

\- Task: Generate MCQ questions targeting specific concepts

\- Output: Questions with options, correct answer, explanation, timestamp



\## Agent 4: Evaluation Agent

\- Input: User answers + correct answers

\- Task: Evaluate answers, provide feedback, identify weak areas

\- Output: Score, feedback per question, list of weak topics



\## Pipeline Flow

YouTube URL → Agent 1 → Agent 2 → Agent 3 → Agent 4 → Score + Weak Areas

