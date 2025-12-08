# To run this file, you must have flet and pandas installed:
# pip install flet pandas openpyxl

import flet as ft
import pandas as pd
import io
import os
import requests
import uuid
FILE_PATH = "src/MCQ_files/mcq_algae.ods"

# --- 1. MOCK DATA & DATA LOADING ---

# This string simulates the data structure found in your Excel file.
# Headers: SN, Question, A, B, C, D, Answer
MOCK_EXCEL_DATA = """
QN,Question,A,B,C,D,Answer
1,What is the capital of France?,Berlin,Madrid,Paris,Rome,C
2,What is the chemical symbol for water?,O2,H2O,CO2,NaCl,B
3,Which planet is known as the Red Planet?,Venus,Mars,Jupiter,Saturn,B
4,Who wrote 'To Kill a Mockingbird'?,J.K. Rowling,Ernest Hemingway,Harper Lee,F. Scott Fitzgerald,C
"""
def get_system_uuid():
   # Define a file path for storing the device ID
    # The actual path might differ slightly on a real Android device
    id_file = "device_id.txt"
    device_id = None

    # Check if ID already exists
    if os.path.exists(id_file):
        with open(id_file, "r") as f:
            device_id = f.read()
    else:
        # Generate a new unique ID and save it
        device_id = str(uuid.uuid4())
        with open(id_file, "w") as f:
            f.write(device_id)
    return device_id


def load_questions_from_excel(filepath=None):
    """
    Loads questions from an Excel file or uses the mock data if no filepath is provided.
    
    Loads data using the specified column headers: SN, Question, A, B, C, D, Answer.
    """
    
    try:
        url = "https://script.google.com/macros/s/AKfycbxoqcO6l-xxXvvgvSYGzQ5fwkLoTXFqnIr2Xp4-x152crVv9wvSUeNUSUdSnT_Gd_Xd/exec" #Replace with your actual URL
        params = {
                "userId": f"{get_system_uuid()}",
                "filename": 'Fungi'
            }
        print(get_system_uuid())
        response = requests.get(url, params=params)

        print(f"Status Code: {response.status_code} {response.status_code == 200}")
    except requests.ConnectionError:
        is_connected = False
        

    if response.status_code == 200:
        # print(response.json())
        questions= response.json()['questions']
        columns = questions[0]
        data = questions[1:]
        df = pd.DataFrame(data, columns=columns)
        
    
    elif filepath and filepath.endswith(('.xlsx', '.ods')):
        try:
            # Assuming the user is running this locally and can access an actual file
            df = pd.read_excel(filepath, dtype=str)
        except Exception as e:
            print(f"Error reading Excel file: {e}. Using mock data instead.")
            df = pd.read_csv(io.StringIO(MOCK_EXCEL_DATA))
    else:
        # Use mock data (CSV in memory) for guaranteed runnability
        df = pd.read_csv(io.StringIO(MOCK_EXCEL_DATA))
    
    # Ensure mandatory columns exist
    required_cols = ['Question', 'A', 'B', 'C', 'D', 'Answer']
    if not all(col in df.columns for col in required_cols):
        print("Error: DataFrame missing required columns (Question, A, B, C, D, Answer).")
        return []
        
    questions = []
    
    for index, row in df.iterrows():
        # Map user's column names to internal structure keys
        answer_key = str(row['Answer']).strip().upper()
        
        # We map the single letter answer (A, B, C, D) to the full string 
        # ('option A', 'option B', etc.) that the RadioGroup uses for its value.
        if answer_key in ['A', 'B', 'C', 'D']:
            formatted_answer = "option " + answer_key
        else:
            print(f"Warning: Skipping question {row.get('SN', index+1)} due to invalid answer key.")
            continue

        q = {
            "qn": int(str(row['QN']).strip()),
            "question": str(row['Question']).strip(),
            "options": {
                "option A": str(row['A']).strip(),
                "option B": str(row['B']).strip(),
                "option C": str(row['C']).strip(),
                "option D": str(row['D']).strip(),
            },
            "answer": formatted_answer,
        }
        questions.append(q)
        
    return questions

# --- 2. MAIN APPLICATION FUNCTION (Functional Style) ---

def main(page: ft.Page):
    # --- State Management (local variables) ---
    questions = load_questions_from_excel(filepath=FILE_PATH) 
    if not questions:
        page.add(ft.Text("Could not load any questions. Check your Excel file format."))
        page.update()
        return

    # Using lists to make variables mutable within nested functions (if needed), 
    # but for simple values, we'll just modify them directly in the scope.
    current_q_index = 0
    score = 0
    
    # --- UI References ---
    question_text = ft.Ref[ft.Text]()
    score_display = ft.Ref[ft.Text]()
    feedback_message = ft.Ref[ft.Text]()
    check_button = ft.Ref[ft.ElevatedButton]()
    
    # RadioGroup instance (needs to be directly accessible, not just a Ref)
    radio_options = ft.RadioGroup(content=ft.Column())
    
    # Actions Row (needs to be directly accessible to change buttons)
    actions = ft.Row(alignment=ft.MainAxisAlignment.CENTER)

    # --- Helper Functions ---

    def _update_score_display():
        """Updates the score text in the top corner."""
        score_display.current.value = f"Question: {current_q_index + 1 if current_q_index < len(questions) else len(questions)} / {len(questions)} | Score: {score}"
    
    def _update_options_content():
        """Updates the radio buttons based on the current question."""
        current_q = questions[current_q_index]
        option_widgets = []
        
        # The key (e.g., 'option A') is the `value` of the Radio button
        for key, text in current_q["options"].items():
            option_widgets.append(
                ft.Radio(
                    value=key, 
                    label=text,
                    fill_color=ft.Colors.INDIGO_ACCENT_700
                )
            )
        
        radio_options.content.controls = option_widgets
        radio_options.value = None # Reset the selection

    def _disable_options():
        """Disables all radio buttons after checking the answer."""
        for radio in radio_options.content.controls:
            radio.disabled = True

    def _next_question_clicked(e):
        nonlocal current_q_index
        current_q_index += 1
        _update_ui()

    def _check_answer_clicked(e):
        nonlocal score
        
        if not radio_options.value:
            feedback_message.current.value = "Please select an option first."
            feedback_message.current.color = ft.Colors.AMBER_600
            page.update()
            return
            
        selected_key = radio_options.value
        correct_answer_key = questions[current_q_index]["answer"]
        
        is_correct = selected_key == correct_answer_key
        
        if is_correct:
            score += 1
            feedback_message.current.value = "✅ Correct! Well done."
            feedback_message.current.color = ft.Colors.GREEN_700
        else:
            correct_option_text = questions[current_q_index]["options"][correct_answer_key]
            feedback_message.current.value = f"❌ Incorrect. The correct answer was: {correct_option_text}"
            feedback_message.current.color = ft.Colors.RED_700
            
        # Change button to 'Next Question'
        check_button.current.text = "Next Question >>"
        check_button.current.icon = ft.Icons.ARROW_FORWARD
        check_button.current.on_click = _next_question_clicked
        _disable_options() # Prevent changing the answer after checking
        page.update()

    def _restart_quiz(e):
        nonlocal current_q_index, score
        current_q_index = 0
        score = 0
        actions.controls = [
            ft.ElevatedButton(
                "Check Answer", 
                icon=ft.Icons.CHECK_CIRCLE, 
                on_click=_check_answer_clicked,
                ref=check_button
            ),
        ]
        _update_ui()

    def _update_ui():
        """Updates all displayed elements for the current question or finishes the quiz."""
        if current_q_index < len(questions):
            question_text.current.value = questions[current_q_index]["question"]
            _update_options_content()
            feedback_message.current.value = ""
            
            # Ensure the button is set back to Check Answer for the new question
            if check_button.current: # Check if the button exists (it will after the first update)
                check_button.current.text = "Check Answer"
                check_button.current.on_click = _check_answer_clicked
                check_button.current.icon = ft.Icons.CHECK_CIRCLE

        else:
            # Quiz finished
            question_text.current.value = "Quiz Complete! 🎉"
            radio_options.content.controls = [
                ft.Text(f"Final Score: {score} out of {len(questions)}", size=24)
            ]
            actions.controls = [
                ft.ElevatedButton(
                    "Start Over", 
                    icon=ft.Icons.RESTART_ALT, 
                    on_click=_restart_quiz
                )
            ]
            feedback_message.current.value = ""
            
        _update_score_display()
        page.update()


    # --- 3. UI Initialization ---
    
    page.title = "Flet MCQ Quiz"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Initial control creation
    initial_question_text = ft.Text(
        questions[0]["question"], 
        size=20, 
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
        ref=question_text
    )
    
    actions.controls = [
        ft.ElevatedButton(
            "Check Answer", 
            icon=ft.Icons.CHECK_CIRCLE, 
            on_click=_check_answer_clicked,
            ref=check_button
        ),
    ]

    # Build the main layout container
    quiz_container = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text(ref=score_display),
                    padding=10,
                    alignment=ft.alignment.center_right
                ),
                initial_question_text,
                ft.Divider(height=20),
                radio_options,
                ft.Divider(height=20),
                actions,
                ft.Text(
                    ref=feedback_message, 
                    size=18, 
                    weight=ft.FontWeight.BOLD
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        ),
        padding=30,
        width=500,
        border_radius=15,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.BLACK45,
            offset=ft.Offset(0, 0),
            blur_style=ft.ShadowBlurStyle.OUTER,
        )
    )

    # Initial setup for options and score display
    _update_options_content()
    _update_score_display()
    
    page.add(quiz_container)


if __name__ == "__main__":
    ft.app(target=main)

# To use your actual Excel file, change the 'filepath=None' in load_questions_from_excel() 
# to 'filepath="path/to/your/quiz.xlsx"' (you need 'openpyxl' for .xlsx support).