import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import os
import json
import re

# Initialize session state
if 'quiz' not in st.session_state:
    st.session_state.quiz = {
        'score': 0,
        'difficulty': 'beginner',
        'history': [],
        'current_q': None,
        'total_questions': 5,
        'current_qnum': 0,
        'quiz_completed': False,
        'generated_questions': set(),
        'user_answers': []
    }

def generate_question(api_key, topic, difficulty):
    """Generate unique adaptive question with validation"""
    client = Groq(api_key=api_key)
    prompt = f"""
    Create a unique {difficulty} level multiple-choice question about {topic} formatted as JSON.
    Structure must be EXACTLY:
    {{
        "question": "unique question text",
        "options": ["A", "B", "C", "D"],
        "answer": "exact matching option",
        "explanation": "detailed explanation"
    }}
    Requirements:
    - Question must be unique and not repeated
    - Output ONLY the raw JSON without formatting
    - Answer must exactly match one option
    - Include 4 distinct options
    """

    retries = 5  # Increased retries for uniqueness
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{
                    "role": "system",
                    "content": "You are a unique question generator. Output ONLY valid JSON."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Clean response
            raw_response = response.choices[0].message.content
            cleaned_response = re.sub(r'^```json\s*|\s*```$', '', raw_response, flags=re.DOTALL)
            
            question = json.loads(cleaned_response)
            
            # Validate uniqueness
            question_hash = hash(question['question'])
            if question_hash in st.session_state.quiz['generated_questions']:
                raise ValueError("Duplicate question detected")
                
            # Validate structure
            required_keys = ["question", "options", "answer", "explanation"]
            if not all(key in question for key in required_keys):
                raise ValueError("Missing required fields")
                
            if question['answer'] not in question['options']:
                raise ValueError("Correct answer not in options")
                
            if len(question['options']) != 4:
                raise ValueError("Exactly 4 options required")
                
            st.session_state.quiz['generated_questions'].add(question_hash)
            return question
            
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < retries - 1:
                continue
            st.error(f"""Failed to generate unique question after {retries} attempts.
                   Try a different topic or increase question variety.""")
            st.stop()
    return None

def text_to_speech(text):
    """Convert text to audio"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts = gTTS(text=text, lang='en')
        tts.save(fp.name)
        return fp.name

# Streamlit UI
st.title("📝 EduGen Adaptive Quiz")
st.markdown("### Unique Questions with Final Feedback")

# API Key Input
api_key = st.text_input("Enter your Groq API key:", type="password")
if not api_key:
    st.warning("⚠ Get your API key from [Groq Console](https://console.groq.com/)")
    st.stop()

# Quiz Setup
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Enter quiz topic:", placeholder="E.g., Quantum Physics, Renaissance Art")
with col2:
    total_q = st.number_input("Number of questions:", min_value=3, max_value=20, value=10)

if not topic:
    st.info("💡 Start by entering a topic above!")
    st.stop()

# Quiz control
if st.button("🚀 Start Quiz") or st.session_state.quiz['current_qnum'] > 0:
    if st.session_state.quiz['quiz_completed']:
        st.session_state.quiz = {
            'score': 0,
            'difficulty': 'beginner',
            'history': [],
            'current_q': None,
            'total_questions': total_q,
            'current_qnum': 0,
            'quiz_completed': False,
            'generated_questions': set(),
            'user_answers': []
        }

    # Generate new question if needed
    if not st.session_state.quiz['current_q']:
        try:
            st.session_state.quiz['current_q'] = generate_question(
                api_key, 
                topic,
                st.session_state.quiz['difficulty']
            )
            st.session_state.quiz['current_qnum'] += 1
        except Exception as e:
            st.error(f"Error generating question: {str(e)}")
            st.stop()

    # Display progress
    progress = st.session_state.quiz['current_qnum']/st.session_state.quiz['total_questions']
    st.progress(progress)
    st.subheader(f"Question {st.session_state.quiz['current_qnum']} of {st.session_state.quiz['total_questions']}")

    # Display Current Question
    q = st.session_state.quiz['current_q']
    st.markdown(f"#### {q['question']}")

    # Audio Version
    audio_file = text_to_speech(q['question'])
    st.audio(audio_file, format="audio/mp3")
    os.unlink(audio_file)

    # Answer Input
    user_answer = st.radio("Select answer:", q['options'], index=None)
    submit = st.button("✅ Submit Answer")

    if submit and user_answer:
        # Store answer without immediate feedback
        correct_answer = q['answer'].strip().lower()
        user_answer_clean = user_answer.strip().lower()
        is_correct = user_answer_clean == correct_answer

        # Update state
        st.session_state.quiz['history'].append({
            'question': q['question'],
            'correct': is_correct,
            'difficulty': st.session_state.quiz['difficulty'],
            'user_answer': user_answer,
            'correct_answer': q['answer'],
            'explanation': q['explanation']
        })
        
        if is_correct:
            st.session_state.quiz['score'] += 1
        
        # Adjust difficulty
        consecutive_correct = sum(1 for item in st.session_state.quiz['history'][-3:] if item['correct'])
        if is_correct:
            if consecutive_correct >= 3 and st.session_state.quiz['difficulty'] != 'advanced':
                st.session_state.quiz['difficulty'] = 'advanced'
            elif st.session_state.quiz['difficulty'] == 'beginner':
                st.session_state.quiz['difficulty'] = 'intermediate'
        else:
            if st.session_state.quiz['difficulty'] == 'advanced':
                st.session_state.quiz['difficulty'] = 'intermediate'
            elif st.session_state.quiz['difficulty'] == 'intermediate':
                st.session_state.quiz['difficulty'] = 'beginner'

        # Generate next question or complete quiz
        if st.session_state.quiz['current_qnum'] < st.session_state.quiz['total_questions']:
            try:
                st.session_state.quiz['current_q'] = generate_question(
                    api_key, 
                    topic,
                    st.session_state.quiz['difficulty']
                )
                st.session_state.quiz['current_qnum'] += 1
                st.rerun()
            except Exception as e:
                st.error(f"Error generating question: {str(e)}")
                st.stop()
        else:
            st.session_state.quiz['quiz_completed'] = True

# Show final results with feedback
if st.session_state.quiz['quiz_completed']:
    st.balloons()
    st.subheader("🎉 Quiz Completed!")
    st.markdown(f"""
    ### Final Score: {st.session_state.quiz['score']}/{st.session_state.quiz['total_questions']}
    ({st.session_state.quiz['score']/st.session_state.quiz['total_questions']:.0%})
    """)
    
    # Detailed feedback section
    st.divider()
    st.subheader("📝 Question-wise Feedback")
    
    for i, result in enumerate(st.session_state.quiz['history']):
        with st.expander(f"Question {i+1}: {result['question']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Your Answer:** {result['user_answer']}")
                st.markdown(f"**Correct Answer:** {result['correct_answer']}")
            with col2:
                st.markdown(f"**Explanation:** {result['explanation']}")
            st.markdown("**Result:** " + ("✅ Correct" if result['correct'] else "❌ Incorrect"))
    
    # Difficulty progression chart
    st.divider()
    st.subheader("📈 Difficulty Progression")
    difficulty_numeric = [{'beginner':1, 'intermediate':2, 'advanced':3}[q['difficulty']] 
                         for q in st.session_state.quiz['history']]
    st.line_chart(difficulty_numeric, use_container_width=True, color="#4CAF50")
    
    if st.button("🔄 Restart Quiz"):
        st.session_state.quiz['quiz_completed'] = False
        st.rerun()

st.markdown("---")
st.caption("💡 All feedback will be shown after completing the entire quiz!")