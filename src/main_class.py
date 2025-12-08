FILE_PATH = "mcq_algae.ods"

# To run this file, you must have flet and pandas installed:
# pip install flet pandas openpyxl

import flet as ft
# Removed: from flet import icons # Reverting to ft.Icons
import pandas as pd
import io

# --- 1. MOCK DATA (Replace with actual Excel reading) ---

# This string simulates the data structure found in your Excel file.
# Headers: question, option A, option B, option C, option D, answer
MOCK_EXCEL_DATA = """
Question,A,B,C,D,Answer
What is the capital of France?,Berlin,Madrid,Paris,Rome,option C
What is the chemical symbol for water?,O2,H2O,CO2,NaCl,option B
Which planet is known as the Red Planet?,Venus,Mars,Jupiter,Saturn,option B
Who wrote 'To Kill a Mockingbird'?,J.K. Rowling,Ernest Hemingway,Harper Lee,F. Scott Fitzgerald,option C
"""

def load_questions_from_excel(filepath=None):
    """
    Loads questions from an Excel file or uses the mock data if no filepath is provided.
    
    In a real application, you would replace io.StringIO(MOCK_EXCEL_DATA) 
    with pd.read_excel(filepath).
    """
    if filepath and filepath.endswith('.xlsx'):
        try:
            # Assuming the user is running this locally and can access an actual file
            df = pd.read_excel(filepath, sheet_name="Question")
        except Exception as e:
            print(f"Error reading Excel file: {e}. Using mock data instead.")
            df = pd.read_csv(io.StringIO(MOCK_EXCEL_DATA))
    else:
        # Use mock data (CSV in memory) for guaranteed runnability
        df = pd.read_csv(io.StringIO(MOCK_EXCEL_DATA))
        
    questions = []
    
    for index, row in df.iterrows():
        # Clean data and ensure option keys are strings for dictionary access
        q = {
            "question": str(row['Question']).strip(),
            "options": {
                "option A": str(row['A']).strip(),
                "option B": str(row['B']).strip(),
                "option C": str(row['C']).strip(),
                "option D": str(row['D']).strip(),
            },
            # The answer must exactly match one of the option keys (e.g., 'option A')
            "answer": str(row['Answer']).strip(),
        }
        questions.append(q)
        
    return questions

# --- 2. FLET APPLICATION CLASS ---

class McqQuiz(ft.Control):    
    def __init__(self, questions):
        super().__init__()
        self.questions = questions
        self.current_q_index = 0
        self.score = 0
        # FIX: Removed ft.Ref for RadioGroup. We will store the instance directly.
        self.radio_options = None 
        
        # We keep the Refs for other controls that are created in build()
        self.feedback_message = ft.Ref[ft.Text]()
        self.score_display = ft.Ref[ft.Text]()
        self.check_button = ft.Ref[ft.ElevatedButton]()
    
    # This method MUST be overridden to return the control's name
    def _get_control_name(self) -> str:
        return "my_custom_control" # The name of your custom control

    # You would also typically need other methods like _get_children, build, etc.
    # depending on how complex your control is and how you structure it.

    def build(self):
        # 1. Question Text Display
        self.question_text = ft.Text(
            self.questions[self.current_q_index]["question"], 
            size=20, 
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER
        )

        # 2. Options as Radio Buttons inside a RadioGroup
        # FIX: Create the RadioGroup instance and store it directly.
        self.radio_options = ft.RadioGroup(
            content=ft.Column()
        )
        self._update_options_content()

        # 3. Action Buttons and Feedback
        self.actions = ft.Row(
            [
                ft.ElevatedButton(
                    "Check Answer", 
                    # FIX: Reverted to ft.Icons.CHECK_CIRCLE
                    icon=ft.Icons.CHECK_CIRCLE, 
                    on_click=self._check_answer_clicked,
                    ref=self.check_button
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # 4. Main Layout
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(ref=self.score_display),
                        padding=10,
                        alignment=ft.alignment.center_right
                    ),
                    self.question_text,
                    ft.Divider(height=20),
                    # Use the stored RadioGroup instance
                    self.radio_options,
                    ft.Divider(height=20),
                    self.actions,
                    ft.Text(
                        ref=self.feedback_message, 
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
        
    def _update_options_content(self):
        """Updates the radio buttons based on the current question."""
        current_q = self.questions[self.current_q_index]
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
        # FIX: Access content directly via the instance: self.radio_options.content.controls
        self.radio_options.content.controls = option_widgets
        # Reset the selection
        self.radio_options.value = None
        
    def _update_ui(self):
        """Updates all displayed elements for the current question."""
        if self.current_q_index < len(self.questions):
            self.question_text.value = self.questions[self.current_q_index]["question"]
            self._update_options_content()
            self.feedback_message.current.value = ""
            self.check_button.current.text = "Check Answer"
            self.check_button.current.on_click = self._check_answer_clicked
            # FIX: Reverted to ft.Icons.CHECK_CIRCLE
            self.check_button.current.icon = ft.Icons.CHECK_CIRCLE
        else:
            # Quiz finished
            self.question_text.value = "Quiz Complete! 🎉"
            # FIX: Access content directly via the instance: self.radio_options.content.controls
            self.radio_options.content.controls = [
                ft.Text(f"Final Score: {self.score} out of {len(self.questions)}", size=24)
            ]
            self.actions.controls = [
                ft.ElevatedButton(
                    "Start Over", 
                    # FIX: Reverted to ft.Icons.RESTART_ALT
                    icon=ft.Icons.RESTART_ALT, 
                    on_click=self._restart_quiz
                )
            ]
            self.feedback_message.current.value = ""
            
        self._update_score_display()
        self.update()

    def _update_score_display(self):
        """Updates the score text in the top corner."""
        self.score_display.current.value = f"Question {self.current_q_index + 1}/{len(self.questions)} | Score: {self.score}"
        
    def _check_answer_clicked(self, e):
        """Handles the 'Check Answer' button click."""
        # FIX: Access value directly via the instance: self.radio_options.value
        if not self.radio_options.value:
            self.feedback_message.current.value = "Please select an option first."
            self.feedback_message.current.color = ft.Colors.AMBER_600
            self.update()
            return
            
        # FIX: Access value directly via the instance: self.radio_options.value
        selected_key = self.radio_options.value
        correct_answer_key = self.questions[self.current_q_index]["answer"]
        
        is_correct = selected_key == correct_answer_key
        
        if is_correct:
            self.score += 1
            self.feedback_message.current.value = "✅ Correct! Well done."
            self.feedback_message.current.color = ft.Colors.GREEN_700
        else:
            correct_option_text = self.questions[self.current_q_index]["options"][correct_answer_key]
            self.feedback_message.current.value = f"❌ Incorrect. The correct answer was: {correct_option_text}"
            self.feedback_message.current.color = ft.Colors.RED_700
            
        # Change button to 'Next Question'
        self.check_button.current.text = "Next Question >>"
        # FIX: Reverted to ft.Icons.ARROW_FORWARD
        self.check_button.current.icon = ft.Icons.ARROW_FORWARD
        self.check_button.current.on_click = self._next_question_clicked
        self._disable_options() # Prevent changing the answer after checking
        self.update()

    def _disable_options(self):
        """Disables all radio buttons after checking the answer."""
        # FIX: Access content directly via the instance: self.radio_options.content.controls
        for radio in self.radio_options.content.controls:
            radio.disabled = True
        
    def _next_question_clicked(self, e):
        """Handles the 'Next Question' button click."""
        self.current_q_index += 1
        self._update_ui()

    def _restart_quiz(self, e):
        """Resets the quiz state and starts from the beginning."""
        self.current_q_index = 0
        self.score = 0
        # Re-initialize action buttons for the restart
        self.actions.controls = [
            ft.ElevatedButton(
                "Check Answer", 
                # FIX: Reverted to ft.Icons.CHECK_CIRCLE
                icon=ft.Icons.CHECK_CIRCLE, 
                on_click=self._check_answer_clicked,
                ref=self.check_button
            ),
        ]
        self._update_ui()


# --- 3. MAIN FUNCTION ---

def main(page: ft.Page):
    page.title = "Flet MCQ Quiz"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.theme_mode = ft.ThemeMode.LIGHT

    # Load questions (try to replace 'quiz.xlsx' with your actual file path)
    # If the file path is provided, it attempts to load it. Otherwise, it uses mock data.
    questions = load_questions_from_excel(filepath=FILE_PATH) 
    print(questions)

    if not questions:
        page.add(ft.Text("Could not load any questions. Check your Excel file format."))
        page.update()
        return

    # Create and add the quiz control
    quiz_app = McqQuiz(questions=questions)
    page.add(quiz_app)


if __name__ == "__main__":
    ft.app(target=main)

# To use your actual Excel file, change the 'filepath=None' in main() to 
# 'filepath="path/to/your/quiz.xlsx"' (you need 'openpyxl' for .xlsx support).