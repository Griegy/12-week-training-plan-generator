import tkinter as tk
import tkinter.ttk as ttk
# Generates a full 12 week training plan based on user inputs. title makes sure its not case sensitive  
def generate_training_plan(intensity, goal):
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
        week_plan = generate_week(mileage, goal, week_num, intensity)
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
# Generates each week based on the mileage, goal, week_num, and intensity
def generate_week(mileage, goal, week_num, intensity):
    # Generates workouts based on weekly mileage
    easy = round(mileage * 0.15, 1)
    long_run = round(mileage * 0.25, 1)
# Basic weekly training structure
    week = {
        "Monday": f"{easy} mi easy",
        "Tuesday": get_workout(goal, week_num, intensity),
        "Wednesday": f"{easy} mi easy",
        "Thursday": get_workout(goal, week_num, intensity),
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


# GUI menu
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
# Makes the buttons
    def create_widgets(self):
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
            self.plan = generate_training_plan(
                self.intensity_entry.get(),
                self.goal_entry.get()
            )

        # Starts at week 1
            self.current_week = 0
        # Build tabs so user can switch between each week
            self.build_tabs()
        # Destroys the widget if the input is invalid
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