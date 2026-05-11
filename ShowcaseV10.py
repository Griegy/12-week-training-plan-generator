#5/11/26
# Fixed Custom workout bug
import tkinter as tk
import sqlite3
import json
import re
# Generates a week of training
def generate_week_plan(*,
                       intensity,
                       goal,
                       week_num,
                       previous_completion=1.0,
                       previous_mileage=None,
                       custom_workout=None):
    # Ensures string values aren't used for mileage
    if isinstance(previous_mileage, str):
        raise TypeError(f"previous_mileage should be float, got {previous_mileage}")
# Sets a base mileage for week 1
    if previous_mileage is None:
        mileage = float(get_base_mileage(goal))
# Uses the previous weeks mileage
    else:
        mileage = float(previous_mileage)
    # Adds more mileage for endurance
    if goal == "Endurance":
        # Stays the same
        if intensity == "Light":
            mileage *= 1
        # Increases moderately
        elif intensity == "Moderate":
            mileage *= 1.05
        # Increases rapidly
        elif intensity == "Hard":
            mileage *= 1.08

        else:
            raise ValueError("Invalid intensity")
    # keeps the mileage consistent for sprinting
    elif goal == "Sprint" and previous_mileage is not None:
        mileage = float(previous_mileage)

    # Adjusts each week based on the previous weeks performance
    # If completion is good it slightly adds mileage
    if previous_completion >= 0.8:
        mileage *= 1.10
    # If completion is not good it reduces mileage
    elif previous_completion >= 0.6:
        mileage *= 0.85
    else:
        mileage *= 0.75

    # Recovery week
    if week_num % 4 == 0:
        mileage *= 0.75
    # Rounds mileage to nearest tenth 
    mileage = round(mileage, 1)
    # Week structure 
    week_plan = generate_week(
        mileage,
        goal,
        week_num,
        intensity,
        custom_workout
    )
    # Returns week
    return Week(
    week=week_num,
    mileage=mileage,
    plan=week_plan
)
# Gets base mileage based on goal
def get_base_mileage(goal):
    goal = goal.strip().title() # 

    if goal == "Sprint":
        return 10   # low mileage, more speed.
    elif goal == "Endurance":
        return 20   # higher mileage to build aerobic base
    else:
        raise ValueError("Invalid goal")
# Week class
class Week:
    def __init__(self, week, mileage, plan, completed=None):
        self.week = week
        self.mileage = mileage
        self.plan = plan
        self.completed = completed or {}
# Generates each weeks structure based on the mileage, goal, week_num, intensity, and if the user enters a custom workout
def generate_week(mileage, goal, week_num, intensity, custom_workout):
    workout = custom_workout if custom_workout else get_workout(goal, week_num, intensity)
    # Generates workouts based on weekly mileage. # The mutiplier for each workouts is commonly used by many coaches
    easy = round(mileage * 0.15, 1)     
    long_run = round(mileage * 0.25, 1)
    week = {
        "Monday": f"{easy} mi easy",
        "Tuesday": workout,
        "Wednesday": f"{easy} mi easy",
        "Thursday": workout,
        "Friday": "Rest",
        "Saturday": f"{long_run} mi long run",
        "Sunday": f"{easy} mi recovery"
    }

    return week
  
# Generates workouts based on goal, week_num, and intensity if there isn't a custom workout
def get_workout(goal, week_num, intensity):
    goal = goal.strip().title()

    # Intensity multiplier for sprinting 
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
# Counts how many workouts the user completed in a week to calculate completion rate
def calculate_completion_rate(week: Week):
    completed = 0
    total = 7

    for value in week.completed.values():
        if value:
            completed += 1
    
    return completed / total 
#_____________________________
# BACKEND INTEGRATION
#____________________________
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
#_________________________
# REGEX
#_________________________
# Validates the inputs to ensure they are valid
def validate_input(text, valid_options):
    text = text.strip()

    for option in valid_options:
        if re.fullmatch(rf"\s*{option}\s*", text, re.IGNORECASE):
            return option

    raise ValueError(f"Invalid input: {text}")
# Parses custom workout and makes sure the format is valid
def parse_workout(text):
    if not text.strip():
        return None  #
# S = Spaces d+ = one or more digits \d+ = reps x = x (amount of reps) the second \d+ = distance m = m for meters 
    match = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)m\s*", text.lower())
    if match:
        reps = int(match.group(1))
        distance = int(match.group(2))
        return f"{reps}x{distance}m"
    else:
        raise ValueError("Invalid workout format (use e.g. 8x400m)")
#__________________________
# GUI MENU
#__________________________
class Application(tk.Frame): # Application inherits from tk.frame
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.last_mileage = None
        self.current_week = 0
        self.plan: list[Week] = []
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
        try: # gets the intensity, goal, and if there is a custom workout
            intensity = validate_input(
                self.intensity_entry.get(),
                ["Light", "Moderate", "Hard"]
            )

            goal = validate_input(
                self.goal_entry.get(),
                ["Sprint", "Endurance"]
            )
            raw = self.workout_entry.get()
            custom_workout = parse_workout(raw) if raw.strip() else None
            # Generates the first week
            first_week = generate_week_plan(
                intensity=intensity,
                goal=goal,
                week_num=1,
                previous_completion=1.0,
                previous_mileage=None,
                custom_workout=custom_workout
            )
            # Saves mileage
            self.last_mileage = float(first_week.mileage)
            # Calls the function show_week to show the first week
            self.show_week(first_week)
            # Saves plan
            self.plan = [first_week]
            save_plan(
                intensity,
                goal,
                [w.__dict__ for w in self.plan]
            )

            self.current_week = 0
            # Saves this stuff for later weeks
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
    # Displays the week
    def show_week(self, week):
        # Clears previous widgets
        for widget in self.output_frame.winfo_children():
            widget.destroy()
        # Writes which week it is and how many miles are in the week
        tk.Label(
            self.output_frame,
            text=f"Week {week.week} - {week.mileage} miles"
        ).pack()
        # Creates a checkbox for each day
        for day, activity in week.plan.items():
            # Tracks whether the checkbox is clicked or not
            var = tk.BooleanVar(value=week.completed.get(day, False))
            # Updates completion to true when a checkbox is clicked
            def make_callback(d, v):
                return lambda: week.completed.__setitem__(d, v.get())
            # This makes the checkbox
            cb = tk.Checkbutton(
            self.output_frame,
            text=f"{day}: {activity}",
            variable=var,
            command=make_callback(day, var)
        )

            cb.pack(anchor="w")
        # Generates the next week when clicked
        tk.Button(
            self.output_frame,
            text="Generate Next Week",
            command=self.next_week
        ).pack()
    def next_week(self):

        previous_week = self.plan[-1]
        # Calculate completion %
        completion_rate = calculate_completion_rate(previous_week)
        # Next weeks number
        next_week_num = previous_week.week + 1
        # Stop after 12 weeks
        if next_week_num > 12:
            tk.Label(
                self.output_frame,
                text="Training Plan Complete!"
            ).pack()

            return
        # Generates next week
        next_week = generate_week_plan(
        intensity=self.intensity,
        goal=self.goal,
        week_num=next_week_num,
        previous_completion=completion_rate,
        previous_mileage=self.last_mileage,
        custom_workout=self.custom_workout
    )

        self.plan.append(next_week)

        self.last_mileage = next_week.mileage
        self.show_week(next_week)
root = tk.Tk()
root.title("Training Planner")

app = Application(master=root)
app.mainloop()
