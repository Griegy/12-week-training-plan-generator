# 4/29/26
import tkinter as tk
import tkinter.ttk as ttk
import sqlite3
import json
import re
# Generates a full 12 week training plan based on user inputs. They can put in a custom workut they want to work on  
def generate_training_plan(intensity, goal, custom_workout=None):
    intensity = intensity.strip().title()
    goal = goal.strip().title()
# Calls the function get_base_mileage to find base_mileage
    base_mileage = get_base_mileage(goal)
    # Makes an empty list
    weeks = []
    # generates a 12 week training plan
    for week_num in range(1, 13):
        # Increases weekly mileage only if goal is endurance since sprinters don't need as much mileage
        if goal == "Endurance":
            if intensity == "Light": # No increase to mileage. Used for maintaining or slightly improving fitness
                mileage = base_mileage

            elif intensity == "Moderate":   # Gradual increase in mileage to build aerobic base. Best option improving with low injury risks
                mileage = base_mileage * (1 + 0.05 * (week_num - 1))

            elif intensity == "Hard": # Faster increase for competitive runners. Higher risk of overtraining.
                mileage = base_mileage * (1 + 0.08 * (week_num - 1))

            else:
                raise ValueError("Invalid intensity")
        # Sprinting plans mostly keep the same mileage
        else:
            mileage = base_mileage
        # Every 4 weeks reduce mileage to help with recovery and prevent burnout
        if week_num % 4 == 0:
            mileage *= 0.75
        # Rounds any unwhole numbers
        mileage = round(mileage, 1)
        # Calls the function generate_week to generate weekly plan
        week_plan = generate_week(mileage, goal, week_num, intensity, custom_workout)
        # Stores the structures
        weeks.append({
            "week": week_num,
            "mileage": mileage,
            "plan": week_plan
        })
# Returns the training plan
    return weeks
# Gets weekly mileage based on goal
def get_base_mileage(goal):
    goal = goal.strip().title()

    if goal == "Sprint":
        return 10   # low mileage, more speed.
    elif goal == "Endurance":
        return 20   # higher mileage to build aerobic base
    else:
        raise ValueError("Invalid goal")
# Generates each week based on the mileage, goal, week_num, intensity, and if the user enters a custom workout
def generate_week(mileage, goal, week_num, intensity, custom_workout):
    # Generates workouts based on weekly mileage. # The mutiplier for each workouts is commonly used by many coaches
    easy = round(mileage * 0.15, 1)     
    long_run = round(mileage * 0.25, 1)
# Basic weekly training structure   
    # Generates workouts for tuesday and thursday 
    workout = custom_workout if custom_workout else get_workout(goal, week_num, intensity)
    week = {
        "Monday": f"{easy} mi easy",
        "Tuesday": workout,
        "Wednesday": f"{easy} mi easy",
        "Thursday":workout,
        "Friday": "Rest",
        "Saturday": f"{long_run} mi long run",
        "Sunday": f"{easy} mi recovery"
    }

    return week
# Generates workouts based on goal, week_num, and intensity
def get_workout(goal, week_num, intensity):
    goal = goal.strip().title()

    # Intensity multiplier
    if intensity == "Light":
        mult = 0.8
    elif intensity == "Moderate":
        mult = 1.0
    elif intensity == "Hard":
        mult = 1.2
    else:
        raise ValueError("Invalid intensity")

    # Sprint
    if goal == "Sprint":
        base_reps = 6
        reps = int(base_reps + (week_num - 1) * 0.5)  # progressively adds more reps
        reps = int(reps * mult)

        return f"{reps}x100m sprints"

    # Endurance
    elif goal == "Endurance":
        return "Tempo run or 5x800m"

    else:
        raise ValueError("Invalid goal")
# Backend Integration
# Creates Database
def init_db():
    conn = sqlite3.connect("training_plans.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intensity TEXT,
        goal TEXT,
        plan TEXT
    )
    """)

    conn.commit()
    conn.close()

# Saves generated plan into database
def save_plan(intensity, goal, plan):
    conn = sqlite3.connect("training_plans.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO plans (intensity, goal, plan) VALUES (?, ?, ?)",
        (intensity, goal, json.dumps(plan))
    )

    conn.commit()
    conn.close()

# Loads all saved plans
def load_plans():
    conn = sqlite3.connect("training_plans.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM plans")
    rows = cursor.fetchall()

    conn.close()
    return rows
# Makes the database when program is ran
init_db()
# Validates the inputs to ensure they are valid
def validate_input(text, valid_options):
    text = text.strip()

    for option in valid_options:
        if re.fullmatch(rf"\s*{option}\s*", text, re.IGNORECASE):
            return option

    raise ValueError(f"Invalid input: {text}")
# Parses custom workout using Regex Scripting
def parse_workout(text):
    if not text.strip():
        return None  #
# S = Spaces \d+ = reps x = x (amount of reps) the second \d+ = distance m = m for meters 
    match = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)m\s*", text.lower())
    if match:
        reps = int(match.group(1))
        distance = int(match.group(2))
        return f"{reps}x{distance}m"
    else:
        raise ValueError("Invalid workout format (use e.g. 8x400m)")
# GUI menu
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
# Makes the buttons
    def create_widgets(self):
        # Output area
        self.output_frame = tk.Frame(self)
        self.output_frame.pack(fill="both", expand=True)
        # Allows the user to enter a custom workout
        tk.Label(self, text="Optional Custom Workout (e.g. 8x400m)").pack()
        self.workout_entry = tk.Entry(self)
        self.workout_entry.pack()
        # Tells user intensity options
        tk.Label(self, text="Enter Training Intensity (Light, Moderate, Hard)").pack()
        self.intensity_entry = tk.Entry(self)
        self.intensity_entry.pack()
        # Tells user goal options
        tk.Label(self, text="Enter Training Goal (Sprint, Endurance)").pack()
        self.goal_entry = tk.Entry(self)
        self.goal_entry.pack()
        # Button used to generate plan
        tk.Button(self, text="Generate Plan",
                  command=self.generate_schedule).pack()

        text_frame = tk.Frame(self)
        text_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
    # Gets called when user clicks generate plan
    def generate_schedule(self):
        try:
            intensity = validate_input(
                self.intensity_entry.get(),
                ["Light", "Moderate", "Hard"]
            )

            goal = validate_input(
                self.goal_entry.get(),
                ["Sprint", "Endurance"]
            )
            custom_workout = parse_workout(self.workout_entry.get())
            # Generates plan
            self.plan = generate_training_plan(intensity, goal, custom_workout)
            # Saves plan
            save_plan(intensity, goal, self.plan)

            self.current_week = 0
            self.build_tabs()

        except ValueError as e:
            for widget in self.output_frame.winfo_children():
                widget.destroy()

            tk.Label(
                self.output_frame,
                text=f"Error: {e}",
                fg="red"
            ).pack()
    # Builds tabs for each week
    def build_tabs(self):

    # clear old tabs
        for tab in self.notebook.winfo_children():
            tab.destroy()
        # Creates a tab for each week
        for week in self.plan:
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=f"Week {week['week']}")
            # Adds daily checkboxes 
            for day, activity in week["plan"].items():
                var = tk.BooleanVar()

                cb = tk.Checkbutton(
                    frame,
                    text=f"{day}: {activity}",
                    variable=var
                )

                cb.pack(anchor="w")       

root = tk.Tk()
root.title("Training Planner")

app = Application(master=root)
app.mainloop()