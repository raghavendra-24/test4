# import streamlit as st
# from groq import Groq
# from gtts import gTTS
# import tempfile
# import os
# import json
# import re

# # Initialize session state
# if 'quiz' not in st.session_state:
#     st.session_state.quiz = {
#         'score': 0,
#         'difficulty': 'beginner',
#         'history': [],
#         'current_q': None,
#         'total_questions': 5,
#         'current_qnum': 0,
#         'quiz_completed': False,
#         'generated_questions': set(),
#         'user_answers': []
#     }

# def generate_question(api_key, topic, difficulty):
#     """Generate unique adaptive question with validation"""
#     client = Groq(api_key=api_key)
#     prompt = f"""
#     Create a unique {difficulty} level multiple-choice question about {topic} formatted as JSON.
#     Structure must be EXACTLY:
#     {{
#         "question": "unique question text",
#         "options": ["A", "B", "C", "D"],
#         "answer": "exact matching option",
#         "explanation": "detailed explanation"
#     }}
#     Requirements:
#     - Question must be unique and not repeated
#     - Output ONLY the raw JSON without formatting
#     - Answer must exactly match one option
#     - Include 4 distinct options
#     """

#     retries = 5  # Increased retries for uniqueness
#     for attempt in range(retries):
#         try:
#             response = client.chat.completions.create(
#                 model="mixtral-8x7b-32768",
#                 messages=[{
#                     "role": "system",
#                     "content": "You are a unique question generator. Output ONLY valid JSON."
#                 }, {
#                     "role": "user",
#                     "content": prompt
#                 }],
#                 temperature=0.7,
#                 response_format={"type": "json_object"}
#             )
            
#             # Clean response
#             raw_response = response.choices[0].message.content
#             cleaned_response = re.sub(r'^```json\s*|\s*```$', '', raw_response, flags=re.DOTALL)
            
#             question = json.loads(cleaned_response)
            
#             # Validate uniqueness
#             question_hash = hash(question['question'])
#             if question_hash in st.session_state.quiz['generated_questions']:
#                 raise ValueError("Duplicate question detected")
                
#             # Validate structure
#             required_keys = ["question", "options", "answer", "explanation"]
#             if not all(key in question for key in required_keys):
#                 raise ValueError("Missing required fields")
                
#             if question['answer'] not in question['options']:
#                 raise ValueError("Correct answer not in options")
                
#             if len(question['options']) != 4:
#                 raise ValueError("Exactly 4 options required")
                
#             st.session_state.quiz['generated_questions'].add(question_hash)
#             return question
            
#         except (json.JSONDecodeError, ValueError) as e:
#             if attempt < retries - 1:
#                 continue
#             st.error(f"""Failed to generate unique question after {retries} attempts.
#                    Try a different topic or increase question variety.""")
#             st.stop()
#     return None

# def text_to_speech(text):
#     """Convert text to audio"""
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
#         tts = gTTS(text=text, lang='en')
#         tts.save(fp.name)
#         return fp.name

# # Streamlit UI
# st.title("📝 EduGen Adaptive Quiz")
# st.markdown("### Unique Questions with Final Feedback")

# # API Key Input
# api_key = st.text_input("Enter your Groq API key:", type="password")
# if not api_key:
#     st.warning("⚠ Get your API key from [Groq Console](https://console.groq.com/)")
#     st.stop()

# # Quiz Setup
# col1, col2 = st.columns(2)
# with col1:
#     topic = st.text_input("Enter quiz topic:", placeholder="E.g., Quantum Physics, Renaissance Art")
# with col2:
#     total_q = st.number_input("Number of questions:", min_value=3, max_value=20, value=10)

# if not topic:
#     st.info("💡 Start by entering a topic above!")
#     st.stop()

# # Quiz control
# if st.button("🚀 Start Quiz") or st.session_state.quiz['current_qnum'] > 0:
#     if st.session_state.quiz['quiz_completed']:
#         st.session_state.quiz = {
#             'score': 0,
#             'difficulty': 'beginner',
#             'history': [],
#             'current_q': None,
#             'total_questions': total_q,
#             'current_qnum': 0,
#             'quiz_completed': False,
#             'generated_questions': set(),
#             'user_answers': []
#         }

#     # Generate new question if needed
#     if not st.session_state.quiz['current_q']:
#         try:
#             st.session_state.quiz['current_q'] = generate_question(
#                 api_key, 
#                 topic,
#                 st.session_state.quiz['difficulty']
#             )
#             st.session_state.quiz['current_qnum'] += 1
#         except Exception as e:
#             st.error(f"Error generating question: {str(e)}")
#             st.stop()

#     # Display progress
#     progress = st.session_state.quiz['current_qnum']/st.session_state.quiz['total_questions']
#     st.progress(progress)
#     st.subheader(f"Question {st.session_state.quiz['current_qnum']} of {st.session_state.quiz['total_questions']}")

#     # Display Current Question
#     q = st.session_state.quiz['current_q']
#     st.markdown(f"#### {q['question']}")

#     # Audio Version
#     audio_file = text_to_speech(q['question'])
#     st.audio(audio_file, format="audio/mp3")
#     os.unlink(audio_file)

#     # Answer Input
#     user_answer = st.radio("Select answer:", q['options'], index=None)
#     submit = st.button("✅ Submit Answer")

#     if submit and user_answer:
#         # Store answer without immediate feedback
#         correct_answer = q['answer'].strip().lower()
#         user_answer_clean = user_answer.strip().lower()
#         is_correct = user_answer_clean == correct_answer

#         # Update state
#         st.session_state.quiz['history'].append({
#             'question': q['question'],
#             'correct': is_correct,
#             'difficulty': st.session_state.quiz['difficulty'],
#             'user_answer': user_answer,
#             'correct_answer': q['answer'],
#             'explanation': q['explanation']
#         })
        
#         if is_correct:
#             st.session_state.quiz['score'] += 1
        
#         # Adjust difficulty
#         consecutive_correct = sum(1 for item in st.session_state.quiz['history'][-3:] if item['correct'])
#         if is_correct:
#             if consecutive_correct >= 3 and st.session_state.quiz['difficulty'] != 'advanced':
#                 st.session_state.quiz['difficulty'] = 'advanced'
#             elif st.session_state.quiz['difficulty'] == 'beginner':
#                 st.session_state.quiz['difficulty'] = 'intermediate'
#         else:
#             if st.session_state.quiz['difficulty'] == 'advanced':
#                 st.session_state.quiz['difficulty'] = 'intermediate'
#             elif st.session_state.quiz['difficulty'] == 'intermediate':
#                 st.session_state.quiz['difficulty'] = 'beginner'

#         # Generate next question or complete quiz
#         if st.session_state.quiz['current_qnum'] < st.session_state.quiz['total_questions']:
#             try:
#                 st.session_state.quiz['current_q'] = generate_question(
#                     api_key, 
#                     topic,
#                     st.session_state.quiz['difficulty']
#                 )
#                 st.session_state.quiz['current_qnum'] += 1
#                 st.rerun()
#             except Exception as e:
#                 st.error(f"Error generating question: {str(e)}")
#                 st.stop()
#         else:
#             st.session_state.quiz['quiz_completed'] = True

# # Show final results with feedback
# if st.session_state.quiz['quiz_completed']:
#     st.balloons()
#     st.subheader("🎉 Quiz Completed!")
#     st.markdown(f"""
#     ### Final Score: {st.session_state.quiz['score']}/{st.session_state.quiz['total_questions']}
#     ({st.session_state.quiz['score']/st.session_state.quiz['total_questions']:.0%})
#     """)
    
#     # Detailed feedback section
#     st.divider()
#     st.subheader("📝 Question-wise Feedback")
    
#     for i, result in enumerate(st.session_state.quiz['history']):
#         with st.expander(f"Question {i+1}: {result['question']}"):
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.markdown(f"**Your Answer:** {result['user_answer']}")
#                 st.markdown(f"**Correct Answer:** {result['correct_answer']}")
#             with col2:
#                 st.markdown(f"**Explanation:** {result['explanation']}")
#             st.markdown("**Result:** " + ("✅ Correct" if result['correct'] else "❌ Incorrect"))
    
#     # Difficulty progression chart
#     st.divider()
#     st.subheader("📈 Difficulty Progression")
#     difficulty_numeric = [{'beginner':1, 'intermediate':2, 'advanced':3}[q['difficulty']] 
#                          for q in st.session_state.quiz['history']]
#     st.line_chart(difficulty_numeric, use_container_width=True, color="#4CAF50")
    
#     if st.button("🔄 Restart Quiz"):
#         st.session_state.quiz['quiz_completed'] = False
#         st.rerun()

# st.markdown("---")
# st.caption("💡 All feedback will be shown after completing the entire quiz!")

import streamlit as st
import json
import re
import os
from groq import Groq
from gtts import gTTS
import tempfile
from tenacity import retry, stop_after_attempt, wait_fixed

# Initialize session state
if 'quiz' not in st.session_state:
    st.session_state.quiz = {
        'api_key': None,
        'user_details': {},
        'questions': [],
        'current_q': 0,
        'score': 0,
        'difficulty': 'beginner',
        'history': [],
        'feedback': '',
        'chat_history': [],
        'raw_response': None,
        'parsing_errors': [],
        'attempt_count': 0
    }

# System instructions with strict formatting
SYSTEM_INSTRUCTION = """
You are an expert quiz generator. Follow these RULES:
1. Generate MCQs in this EXACT format:
**QuestionX**
{
    'Question': '...',
    'Options': {
        'OptionA': '...',
        'OptionB': '...', 
        'OptionC': '...',
        'OptionD': '...'
    },
    'Answer': '...'
}
2. Use SINGLE quotes for keys/values
3. No extra text before/after questions
4. Answers must EXACTLY match one option value
5. Ensure UNIQUE, age-appropriate questions
6. Maintain consistent option casing
7. Avoid special characters
8. Ensure proper JSON formatting
9. Ensure proper comma separation between key-value pairs
10. Avoid trailing commas in JSON objects
11. Use proper JSON boolean values (true/false)
12. Maintain consistent quotation usage
13. Validate JSON syntax before responding

EXAMPLE:
**Question1**
{
    'Question': 'What is 2+2?',
    'Options': {
        'OptionA': '3',
        'OptionB': '4',
        'OptionC': '5',
        'OptionD': '6'
    },
    'Answer': '4'
}
"""

def get_groq_client():
    """Initialize Groq client with validation"""
    if not st.session_state.quiz['api_key']:
        st.warning("🔑 Please enter your Groq API key")
        st.stop()
    try:
        return Groq(api_key=st.session_state.quiz['api_key'])
    except Exception as e:
        st.error(f"❌ API Connection Error: {str(e)}")
        st.stop()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def generate_questions(prompt):
    """Generate questions with retry logic"""
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=4000
        )
        raw_response = response.choices[0].message.content
        st.session_state.quiz['raw_response'] = raw_response
        return extract_questions(raw_response)
    except Exception as e:
        st.session_state.quiz['attempt_count'] += 1
        st.error(f"⚠️ Attempt {st.session_state.quiz['attempt_count']} failed: {str(e)}")
        return None

def extract_questions(response):
    """Extract and parse questions from API response with enhanced regex"""
    question_blocks = re.findall(r'\*\*Question\d+\*\*\s*({.*?})\s*(?=\*\*Question\d+\*\*|$)', response, re.DOTALL)
    
    questions = []
    for block in question_blocks:
        try:
            # Convert to valid JSON
            json_str = block.replace("'", '"')
            json_str = re.sub(r'(\w+)(\s*:\s*)', r'"\1"\2', json_str)  # Add quotes to keys
            question_data = json.loads(json_str)
            questions.append(question_data)
        except json.JSONDecodeError as e:
            st.session_state.quiz['parsing_errors'].append({
                'error_type': 'JSON Decode',
                'message': str(e),
                'block': block
            })
    return questions

def text_to_speech(text):
    """Convert text to audio with error handling"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts = gTTS(text=text, lang='en')
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"🔇 TTS Error: {str(e)}")
        return None

def user_details_form():
    """Collect user information"""
    with st.form("user_details"):
        st.session_state.quiz['user_details'] = {
            'name': st.text_input("Student Name"),
            'grade': st.number_input("Grade Level", min_value=1, max_value=12, value=5),
            'subject': st.selectbox("Subject", ["Math", "Science", "History", "English"]),
            'topic': st.text_input("Topic", placeholder="E.g., Fractions, Solar System"),
            'difficulty': st.select_slider("Difficulty", ['Beginner', 'Intermediate', 'Advanced']),
            'num_questions': st.slider("Number of Questions", 5, 20, 10)
        }
        if st.form_submit_button("🚀 Start Quiz"):
            generate_quiz()

def generate_quiz():
    """Generate new quiz questions"""
    details = st.session_state.quiz['user_details']
    prompt = f"""
    Generate {details['num_questions']} {details['subject']} questions about {details['topic']}
    for a {details['grade']}th grade student at {details['difficulty']} level.
    """
    
    with st.spinner("🧠 Generating questions..."):
        questions = generate_questions(prompt)
    
    if questions:
        st.session_state.quiz.update({
            'questions': questions,
            'current_q': 0,
            'score': 0,
            'history': [],
            'feedback': '',
            'attempt_count': 0
        })
        st.rerun()
    else:
        st.error("❌ Failed to generate questions. Please try a different topic or reduce question count.")

def show_question():
    """Display current question with audio"""
    q_idx = st.session_state.quiz['current_q']
    q = st.session_state.quiz['questions'][q_idx]
    
    st.subheader(f"❓ Question {q_idx + 1}")
    st.markdown(f"**{q['Question']}**")
    
    # Audio version
    if audio_file := text_to_speech(q['Question']):
        st.audio(audio_file)
        os.unlink(audio_file)
    
    # Answer selection using option values
    options = list(q['Options'].values())
    user_answer = st.radio("Options:", options, index=None, key=f"q{q_idx}")
    
    if st.button("✅ Submit Answer"):
        process_answer(q, user_answer)

def process_answer(q, user_answer):
    """Handle answer submission and progression"""
    is_correct = user_answer.strip() == q['Answer'].strip()
    
    st.session_state.quiz['history'].append({
        'question': q['Question'],
        'user_answer': user_answer,
        'correct_answer': q['Answer'],
        'is_correct': is_correct
    })
    
    if is_correct:
        st.session_state.quiz['score'] += 1
    
    if st.session_state.quiz['current_q'] < len(st.session_state.quiz['questions']) - 1:
        st.session_state.quiz['current_q'] += 1
        st.rerun()
    else:
        generate_feedback()

def generate_feedback():
    """Generate AI performance analysis"""
    details = st.session_state.quiz['user_details']
    prompt = f"""
    Analyze performance for {details['name']} (Grade {details['grade']}):
    - Subject: {details['subject']}
    - Topic: {details['topic']}
    - Score: {st.session_state.quiz['score']}/{len(st.session_state.quiz['questions'])}
    - Question History: {st.session_state.quiz['history']}
    
    Provide 200-word analysis covering:
    1. Strengths and weaknesses
    2. Key areas needing improvement
    3. Study recommendations
    4. Encouraging feedback
    """
    
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        st.session_state.quiz['feedback'] = response.choices[0].message.content
    except Exception as e:
        st.error(f"📝 Feedback Error: {str(e)}")

def debug_panel():
    """Show debugging information"""
    with st.expander("🐞 Debug Panel"):
        st.subheader("Raw API Response")
        st.code(st.session_state.quiz.get('raw_response', 'No response captured'))
        
        st.subheader("Parsing Errors")
        if st.session_state.quiz['parsing_errors']:
            for error in st.session_state.quiz['parsing_errors']:
                st.error(f"""
                **Question Error**  
                Type: {error['error_type']}  
                Message: {error['message']}
                """)
                st.code(error['block'])
        else:
            st.success("✅ No parsing errors detected")
        
        st.subheader("Session State")
        st.json(st.session_state.quiz)

def chat_interface():
    """Interactive study assistant"""
    st.subheader("💬 Study Assistant")
    
    for msg in st.session_state.quiz['chat_history']:
        st.chat_message("user" if msg['is_user'] else "assistant").write(msg['content'])
    
    if prompt := st.chat_input("Ask about the topic..."):
        st.session_state.quiz['chat_history'].append({'is_user': True, 'content': prompt})
        
        try:
            client = get_groq_client()
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}]
            )
            reply = response.choices[0].message.content
            st.session_state.quiz['chat_history'].append({'is_user': False, 'content': reply})
            st.rerun()
        except Exception as e:
            st.error(f"💬 Chat Error: {str(e)}")

# Main application flow
st.title("🎓 Smart Study Pro")
st.caption("Powered by Groq AI • Adaptive Learning System")

# API Key Input
st.session_state.quiz['api_key'] = st.text_input(
    "Enter Groq API Key:",
    type="password",
    help="Get from https://console.groq.com/keys"
)

if st.session_state.quiz['api_key']:
    if not st.session_state.quiz.get('user_details'):
        user_details_form()
    else:
        if st.session_state.quiz['questions']:
            show_question()
        else:
            user_details_form()

    if st.session_state.quiz.get('feedback'):
        st.subheader("📊 Performance Report")
        st.write(st.session_state.quiz['feedback'])
        
        st.subheader("📝 Question Review")
        for i, result in enumerate(st.session_state.quiz['history']):
            with st.expander(f"Question {i+1}: {result['question']}", expanded=False):
                st.markdown(f"""
                **Your Answer:** {result['user_answer'] or 'No answer'}  
                **Correct Answer:** {result['correct_answer']}  
                **Result:** {"✅ Correct" if result['is_correct'] else "❌ Incorrect"}
                """)
        
        if st.button("🔄 Retake Quiz"):
            st.session_state.quiz.update({
                'questions': [],
                'current_q': 0,
                'score': 0,
                'history': [],
                'feedback': ''
            })
            st.rerun()

    chat_interface()
    debug_panel()

# Footer
st.markdown("---")
st.markdown("**Tips:** • Start with simple topics • Check debug panel if issues occur • Refresh to start over")
