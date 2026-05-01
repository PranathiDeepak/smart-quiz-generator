import streamlit as st
import requests

API_URL = "https://smart-quiz-generator-815e.onrender.com"

st.title("🎓 Smart Quiz Generator")
st.sidebar.title("🎓 Smart Quiz Generator")
st.subheader("Generate quizzes from YouTube videos and track your learning!")

# Sidebar for navigation
page = st.sidebar.selectbox("Choose a page", ["Generate Quiz", "Quiz History", "Progress"])

if page == "Generate Quiz":
    st.header("📝 Generate a New Quiz")
    url = st.text_input("Paste a YouTube URL:")
    num_questions = st.slider("Number of questions:", 3, 10, 5)
    
    if st.button("Generate Quiz"):
        if not url:
            st.error("Please enter a YouTube URL")
        else:
            with st.spinner("Generating quiz... this may take a minute!"):
                response = requests.get(f"{API_URL}/generate_quiz", params={"url": url, "num_questions": num_questions})
                data = response.json()
            
            if "error" in data:
                st.error(data["error"])
            else:
                st.success(f"Generated {data['num_questions']} questions!")
                st.session_state.quiz = data
                st.session_state.url = url
                st.session_state.answers = [""] * data["num_questions"]
    
    # Display quiz if generated
    if "quiz" in st.session_state:
        for i, q in enumerate(st.session_state.quiz["questions"]):
            st.markdown(f"**Question {i+1}:** {q['question']}")
            st.session_state.answers[i] = st.radio(
                f"Select your answer for Q{i+1}:",
                options=["A", "B", "C", "D"],
                format_func=lambda x, q=q: f"{x}) {q['options'][x]}",
                key=f"q_{i}"
            )
        
        if st.button("Submit Answers"):
            with st.spinner("Evaluating your answers..."):
                response = requests.post(f"{API_URL}/submit_answers", json={
                    "url": st.session_state.url,
                    "answers": st.session_state.answers
                })
                results = response.json()
            
            st.markdown(f"### Score: {results['score']}/{results['total']}")
            
            for detail in results["details"]:
                if detail["is_correct"]:
                    st.success(f"✅ {detail['question']}")
                else:
                    st.error(f"❌ {detail['question']}")
                st.write(f"Your answer: {detail['user_answer']} | Correct: {detail['correct_answer']}")
                st.write(f"📖 {detail['explanation']}")
                st.write(f"🎬 Review at: {detail['timestamp']}")
                st.divider()
            
            if results["weak_topics"]:
                st.warning(f"**Weak Topics:** {', '.join(results['weak_topics'])}")

elif page == "Quiz History":
    st.header("📊 Quiz History")
    response = requests.get(f"{API_URL}/get_history")
    data = response.json()
    
    if not data["history"]:
        st.info("No quizzes taken yet. Go generate one!")
    else:
        for entry in data["history"]:
            st.markdown(f"**Date:** {entry['date']}")
            st.markdown(f"**Video:** {entry['url']}")
            st.markdown(f"**Score:** {entry['score']}/{entry['total']}")
            st.markdown(f"**Weak Topics:** {', '.join(entry['weak_topics'])}")
            st.divider()

elif page == "Progress":
    st.header("📈 Progress Tracker")
    response = requests.get(f"{API_URL}/get_progress")
    data = response.json()
    
    if not data["progress"]:
        st.info("No progress data yet. Take some quizzes first!")
    else:
        for topic, stats in data["progress"].items():
            passed = stats["attempted"] - stats["failed"]
            if stats["failed"] == 0:
                status = "✅ Mastered"
            elif stats["failed"] > passed:
                status = "❌ Needs work"
            else:
                status = "🔄 Improving"
            
            st.markdown(f"**{topic}** — {status}")
            st.write(f"Attempted: {stats['attempted']} | Passed: {passed} | Failed: {stats['failed']}")
            st.progress(passed / stats["attempted"] if stats["attempted"] > 0 else 0)
            st.divider()