# 4/29/26
import tkinter as tk
import sqlite3
import json
import re
# Generates a full 12 week training plan based on user inputs. They can put in a custom workut they want to work on  
def generate_week_plan(intensity, goal, week_num,
                       previous_completion=1.0,
                       previous_mileage=None,
                       custom_workout=None):

    if previous_mileage is None:
        mileage = get_base_mileage(goal)
    else:
        mileage = previous_mileage
    # endurance progression
    if goal == "Endurance":

        if intensity == "Light":
            mileage *= 1
        elif intensity == "Moderate":
            mileage *= 1.05

        elif intensity == "Hard":
            mileage *= 1.08

        else:
            raise ValueError("Invalid intensity")

    else:
        mileage *= 1

    # adaptive adjustment
    if previous_completion >= 0.8:
        mileage *= 1.10

    elif previous_completion >= 0.6:
        mileage *= 0.85
    else:
        mileage *= 0.75

    # recovery week
    if week_num % 4 == 0:
        mileage *= 0.75

    mileage = round(mileage, 1)

    week_plan = generate_week(
        mileage,
        goal,
        week_num,
        intensity,
        custom_workout
    )

    return {
        "week": week_num,
        "mileage": mileage,
        "plan": week_plan,
        "completed": {}
    }
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
def calculate_completion_rate(week):

    completed = 0
    total = 0

    for day, value in week["completed"].items():
        total += 1
        if value:
            completed += 1

    return completed / total if total > 0 else 0
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
        self.last_mileage = None
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
            self.plan = []

            first_week = generate_week_plan(
                intensity,
                goal,
                1,
                1.0,
                custom_workout
)

            self.plan.append(first_week)
            self.last_mileage = first_week["mileage"]
            self.show_week(first_week)
            # Saves plan
            save_plan(intensity, goal, self.plan)

            self.current_week = 0
            self.intensity = intensity
            self.goal = goal
            self.custom_workout = custom_workout
        except ValueError as e:
            for widget in self.output_frame.winfo_children():
                widget.destroy()

            tk.Label(
                self.output_frame,
                text=f"Error: {e}",
                fg="red"
            ).pack()

    def show_week(self, week):

        for widget in self.output_frame.winfo_children():
            widget.destroy()

        tk.Label(
            self.output_frame,
            text=f"Week {week['week']} - {week['mileage']} miles"
        ).pack()

        week["completed"] = {}

        def make_callback(day, var):
            def update():
                week["completed"][day] = var.get()
            return update

        for day, activity in week["plan"].items():

            var = tk.BooleanVar()

            week["completed"][day] = False  # default value

            cb = tk.Checkbutton(
                self.output_frame,
                text=f"{day}: {activity}",
                variable=var,
                command=make_callback(day, var)
            )

            cb.pack(anchor="w")

        tk.Button(
            self.output_frame,
            text="Generate Next Week",
            command=self.next_week
        ).pack()
    def next_week(self):

        previous_week = self.plan[-1]

        completion_rate = calculate_completion_rate(previous_week)

        next_week_num = previous_week["week"] + 1

        if next_week_num > 12:
            tk.Label(
                self.output_frame,
                text="Training Plan Complete!"
            ).pack()

            return

        next_week = generate_week_plan(
            self.intensity,
            self.goal,
            next_week_num,
            completion_rate,
            self.last_mileage,
            self.custom_workout
        )

        self.plan.append(next_week)

        self.last_mileage = next_week["mileage"]
        self.show_week(next_week)

     

root = tk.Tk()
root.title("Training Planner")

app = Application(master=root)
app.mainloop()