import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime, timedelta
import pandas as pd
import os
import json
import hashlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configuration
DATA_FILE = "fitness_tracker_data.xlsx"
USERS_SHEET = "Users"
WEIGHT_SHEET = "Weight"
FOOD_SHEET = "Food"
WORKOUT_SHEET = "Workout"

# Muscle group exercise plan
muscle_workout_plan = {
    "Monday": ("Cardio + Shoulders", ["Running (30min)", "Military Press", "Lateral Raise"]),
    "Tuesday": ("Cardio + Chest", ["Cycling (30min)", "Bench Press", "Incline Dumbbell Press"]),
    "Wednesday": ("Cardio + Back", ["Swimming (30min)", "Pull-ups", "Deadlift"]),
    "Thursday": ("Cardio + Abs", ["Jump Rope (30min)", "Plank", "Crunches"]),
    "Friday": ("Cardio + Arms", ["Rowing (30min)", "Barbell Curl", "Skull Crusher"]),
    "Saturday": ("Cardio + Legs", ["HIIT (30min)", "Squats", "Lunges"]),
    "Sunday": ("Rest", [])
}

# Meal plans
meal_plans = {
    "Weight Loss": {
        "Vegetarian": {
            "Breakfast": {"item": "Oats with berries", "calories": 250, "protein": 10},
            "Lunch": {"item": "Salad with lentils", "calories": 300, "protein": 15},
            "Dinner": {"item": "Grilled vegetables with quinoa", "calories": 350, "protein": 12},
            "Snacks": {"item": "Greek yogurt", "calories": 100, "protein": 8}
        },
        "Non-Vegetarian": {
            "Breakfast": {"item": "Egg whites with spinach", "calories": 250, "protein": 20},
            "Lunch": {"item": "Grilled chicken with vegetables", "calories": 300, "protein": 30},
            "Dinner": {"item": "Baked fish with asparagus", "calories": 350, "protein": 25},
            "Snacks": {"item": "Protein shake", "calories": 100, "protein": 20}
        }
    },
    "Weight Gain": {
        "Vegetarian": {
            "Breakfast": {"item": "Paneer + Oats", "calories": 500, "protein": 30},
            "Lunch": {"item": "Lentils + Rice + Curd", "calories": 600, "protein": 35},
            "Dinner": {"item": "Tofu + Veggies + Quinoa", "calories": 550, "protein": 40},
            "Snacks": {"item": "Nuts + Banana", "calories": 300, "protein": 10}
        },
        "Non-Vegetarian": {
            "Breakfast": {"item": "Eggs + Toast", "calories": 500, "protein": 30},
            "Lunch": {"item": "Chicken + Rice + Veggies", "calories": 600, "protein": 35},
            "Dinner": {"item": "Fish + Brown Rice + Salad", "calories": 550, "protein": 40},
            "Snacks": {"item": "Protein bar", "calories": 300, "protein": 20}
        }
    }
}

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_data_file():
    if not os.path.exists(DATA_FILE):
        with pd.ExcelWriter(DATA_FILE, engine='openpyxl') as writer:
            # Users sheet
            pd.DataFrame(columns=["Username", "PasswordHash"]).to_excel(
                writer, sheet_name=USERS_SHEET, index=False)
            # Weight sheet
            pd.DataFrame(columns=["Username", "Date", "Weight (kg)", "Goal Type", "Current Goal (kg)", "Active"]).to_excel(
                writer, sheet_name=WEIGHT_SHEET, index=False)
            # Food sheet
            pd.DataFrame(columns=["Username", "Date", "Meal Type", "Food Item", "Calories", "Protein (g)", "Vegetarian"]).to_excel(
                writer, sheet_name=FOOD_SHEET, index=False)
            # Workout sheet
            pd.DataFrame(columns=["Username", "Date", "Muscle Group", "Exercise", "Sets", "Reps", "Duration (min)", "Completed"]).to_excel(
                writer, sheet_name=WORKOUT_SHEET, index=False)

def save_data(data, sheet_name):
    try:
        existing_data = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        new_data = pd.DataFrame([data] if isinstance(data, dict) else data)
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        combined_data = combined_data.drop_duplicates()
        
        with pd.ExcelWriter(DATA_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            combined_data.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save data: {str(e)}")

def get_user_goals(username):
    try:
        df = pd.read_excel(DATA_FILE, sheet_name=WEIGHT_SHEET)
        user_goals = df[df['Username'] == username]
        return user_goals
    except Exception:
        return pd.DataFrame()

def get_active_goal(username):
    user_goals = get_user_goals(username)
    if not user_goals.empty:
        active_goals = user_goals[user_goals['Active'] == True]
        if not active_goals.empty:
            return active_goals.iloc[-1]  # Return most recent active goal
    return None

def authenticate_user(username, password):
    try:
        users_df = pd.read_excel(DATA_FILE, sheet_name=USERS_SHEET)
        user_record = users_df[users_df['Username'] == username]
        if not user_record.empty and user_record.iloc[0]['PasswordHash'] == hash_password(password):
            return True
        return False
    except Exception:
        return False

def register_user(username, password):
    try:
        users_df = pd.read_excel(DATA_FILE, sheet_name=USERS_SHEET)
        if username in users_df['Username'].values:
            return False  # Username exists
        
        new_user = {
            "Username": username,
            "PasswordHash": hash_password(password)
        }
        save_data(new_user, USERS_SHEET)
        return True
    except Exception:
        return False

# Initialize data file
initialize_data_file()

# Global variable to track current user
current_user = None

# --- Login/Signup Window ---
class AuthWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Fitness Tracker - Login")
        self.root.geometry("800x600")
        self.root.configure(bg="#121212")
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 600) // 2
        self.root.geometry(f"800x600+{x}+{y}")
        
        self.create_widgets()
    
    def create_widgets(self):
        self.title_label = tk.Label(self.root, text="\U0001F9EC FITNESS TRACKER", 
                                   font=("Segoe UI Black", 22), bg="#121212", fg="#ffffff")
        self.title_label.pack(pady=20)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, padx=20, pady=20)
        
        # Login Tab
        self.login_frame = tk.Frame(self.notebook, bg="#1e1e1e")
        self.notebook.add(self.login_frame, text="Login")
        
        tk.Label(self.login_frame, text="Username:", font=("Segoe UI", 12), 
                bg="#1e1e1e", fg="#ffffff").pack(pady=(20, 5))
        self.login_username = tk.Entry(self.login_frame, font=("Segoe UI", 12), 
                                     bg="#2c2c2c", fg="white", insertbackground="white")
        self.login_username.pack(pady=5)
        
        tk.Label(self.login_frame, text="Password:", font=("Segoe UI", 12), 
                bg="#1e1e1e", fg="#ffffff").pack(pady=(10, 5))
        self.login_password = tk.Entry(self.login_frame, show="*", font=("Segoe UI", 12), 
                                     bg="#2c2c2c", fg="white", insertbackground="white")
        self.login_password.pack(pady=5)
        
        self.login_btn = tk.Button(self.login_frame, text="Login", command=self.login,
                                 font=("Segoe UI Black", 12), bg="#0984e3", fg="white")
        self.login_btn.pack(pady=20)
        
        self.login_status = tk.Label(self.login_frame, text="", font=("Segoe UI", 12), 
                                   bg="#1e1e1e", fg="#ffffff")
        self.login_status.pack()
        
        # Signup Tab
        self.signup_frame = tk.Frame(self.notebook, bg="#1e1e1e")
        self.notebook.add(self.signup_frame, text="Sign Up")
        
        tk.Label(self.signup_frame, text="Username:", font=("Segoe UI", 12), 
                bg="#1e1e1e", fg="#ffffff").pack(pady=(20, 5))
        self.signup_username = tk.Entry(self.signup_frame, font=("Segoe UI", 12), 
                                      bg="#2c2c2c", fg="white", insertbackground="white")
        self.signup_username.pack(pady=5)
        
        tk.Label(self.signup_frame, text="Password:", font=("Segoe UI", 12), 
                bg="#1e1e1e", fg="#ffffff").pack(pady=(10, 5))
        self.signup_password = tk.Entry(self.signup_frame, show="*", font=("Segoe UI", 12), 
                                      bg="#2c2c2c", fg="white", insertbackground="white")
        self.signup_password.pack(pady=5)
        
        tk.Label(self.signup_frame, text="Confirm Password:", font=("Segoe UI", 12), 
                bg="#1e1e1e", fg="#ffffff").pack(pady=(10, 5))
        self.signup_confirm = tk.Entry(self.signup_frame, show="*", font=("Segoe UI", 12), 
                                     bg="#2c2c2c", fg="white", insertbackground="white")
        self.signup_confirm.pack(pady=5)
        
        self.signup_btn = tk.Button(self.signup_frame, text="Create Account", command=self.signup,
                                  font=("Segoe UI Black", 12), bg="#00b894", fg="white")
        self.signup_btn.pack(pady=20)
        
        self.signup_status = tk.Label(self.signup_frame, text="", font=("Segoe UI", 12), 
                                    bg="#1e1e1e", fg="#ffffff")
        self.signup_status.pack()
    
    def login(self):
        username = self.login_username.get()
        password = self.login_password.get()
        
        if not username or not password:
            self.login_status.config(text="Username and password required", fg="#d63031")
            return
        
        if authenticate_user(username, password):
            global current_user
            current_user = username
            self.root.destroy()
            show_main_window()
        else:
            self.login_status.config(text="Invalid username or password", fg="#d63031")
    
    def signup(self):
        username = self.signup_username.get()
        password = self.signup_password.get()
        confirm = self.signup_confirm.get()
        
        if not username or not password:
            self.signup_status.config(text="Username and password required", fg="#d63031")
            return
        
        if password != confirm:
            self.signup_status.config(text="Passwords don't match", fg="#d63031")
            return
        
        if register_user(username, password):
            self.signup_status.config(text="Account created successfully! Please login.", fg="#00b894")
            self.notebook.select(0)  # Switch to login tab
        else:
            self.signup_status.config(text="Username already exists", fg="#d63031")

# --- Main Application Window ---
def show_main_window():
    root = tk.Tk()
    root.title(f"Fitness Tracker - {current_user}")
    root.geometry("1000x700")
    root.configure(bg="#121212")
    
    # Check for active goal
    active_goal = get_active_goal(current_user)
    
    if active_goal is None:
        show_goal_window(root)
    else:
        show_calendar_dashboard(root, active_goal['Weight (kg)'], 
                               active_goal['Current Goal (kg)'], 
                               active_goal['Goal Type'])
    
    root.mainloop()

# --- Goal Window ---
def show_goal_window(root):
    for widget in root.winfo_children():
        widget.destroy()
    
    goal_label = tk.Label(root, text="WHAT IS YOUR GOAL?", 
                         font=("Segoe UI Black", 20), bg="#1e1e1e", fg="#ffffff")
    goal_label.pack(pady=20)
    
    button_frame = tk.Frame(root, bg="#1e1e1e")
    button_frame.pack(expand=True)
    
    tk.Button(button_frame, text="WEIGHT GAIN", font=("Segoe UI Black", 14), 
             bg="#00b894", fg="white", width=18, command=lambda: open_weight_input(root, "Weight Gain")).pack(pady=10)
    
    tk.Button(button_frame, text="WEIGHT LOSS", font=("Segoe UI Black", 14), 
             bg="#d63031", fg="white", width=18, command=lambda: open_weight_input(root, "Weight Loss")).pack(pady=10)

# --- Weight Input Window ---
def open_weight_input(root, goal_type):
    for widget in root.winfo_children():
        widget.destroy()
    
    input_frame = tk.Frame(root, bg="#1e1e1e")
    input_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    tk.Label(input_frame, text="Enter Current Weight (kg):", font=("Segoe UI", 14, "bold"),
             bg="#1e1e1e", fg="#ffffff").pack(pady=(20, 5))
    current_entry = tk.Entry(input_frame, font=("Segoe UI", 14), bg="#2c2c2c", fg="white")
    current_entry.pack(pady=5)
    
    tk.Label(input_frame, text=f"Enter Goal Weight (kg):", font=("Segoe UI", 14, "bold"),
             bg="#1e1e1e", fg="#ffffff").pack(pady=(15, 5))
    goal_entry = tk.Entry(input_frame, font=("Segoe UI", 14), bg="#2c2c2c", fg="white")
    goal_entry.pack(pady=5)
    
    status_label = tk.Label(input_frame, text="", font=("Segoe UI", 12), bg="#1e1e1e", fg="#ffffff")
    status_label.pack(pady=10)
    
    button_frame = tk.Frame(input_frame, bg="#1e1e1e")
    button_frame.pack(pady=10)
    
    def submit_goal():
        try:
            current_weight = float(current_entry.get())
            goal_weight = float(goal_entry.get())
            
            if goal_type == "Weight Gain" and goal_weight <= current_weight:
                status_label.config(text="Goal must be greater than current weight", fg="#e17055")
            elif goal_type == "Weight Loss" and goal_weight >= current_weight:
                status_label.config(text="Goal must be less than current weight", fg="#e17055")
            else:
                # Save the new goal (mark as active)
                today = datetime.today().strftime('%Y-%m-%d')
                weight_data = {
                    "Username": current_user,
                    "Date": today,
                    "Weight (kg)": current_weight,
                    "Goal Type": goal_type,
                    "Current Goal (kg)": goal_weight,
                    "Active": True
                }
                
                # Mark any previous goals as inactive
                try:
                    df = pd.read_excel(DATA_FILE, sheet_name=WEIGHT_SHEET)
                    df.loc[df['Username'] == current_user, 'Active'] = False
                    with pd.ExcelWriter(DATA_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        df.to_excel(writer, sheet_name=WEIGHT_SHEET, index=False)
                except Exception:
                    pass
                
                save_data(weight_data, WEIGHT_SHEET)
                show_calendar_dashboard(root, current_weight, goal_weight, goal_type)
        except ValueError:
            status_label.config(text="Please enter valid numbers", fg="#e17055")
    
    tk.Button(button_frame, text="Submit", font=("Segoe UI Black", 14), bg="#0984e3", 
             fg="white", command=submit_goal).pack(side=tk.LEFT, padx=10)
    
    tk.Button(button_frame, text="Back", font=("Segoe UI Black", 14), bg="#d63031", 
             fg="white", command=lambda: show_goal_window(root)).pack(side=tk.LEFT, padx=10)

# --- Calendar Dashboard ---
def show_calendar_dashboard(root, current_weight, goal_weight, goal_type):
    for widget in root.winfo_children():
        widget.destroy()
    
    main_frame = tk.Frame(root, bg="#1e1e1e")
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    top_frame = tk.Frame(main_frame, bg="#1e1e1e")
    top_frame.pack(fill='x', pady=10)
    
    tk.Label(top_frame, text=f"{goal_type} Progress Tracker", 
            font=("Segoe UI Black", 22), bg="#1e1e1e", fg="#ffffff").pack()
    
    calendar_frame = tk.Frame(main_frame, bg="#1e1e1e")
    calendar_frame.pack(fill='both', expand=True)
    
    calendar = Calendar(calendar_frame, selectmode='day', date_pattern='yyyy-mm-dd', 
                       font=("Segoe UI", 14), background="#2c2c2c", foreground='white')
    calendar.pack(fill='both', expand=True, padx=20, pady=10)
    
    info_label = tk.Label(main_frame, text="Select a date to view your plan and mark it as done.",
                         font=("Segoe UI", 13), bg="#1e1e1e", fg="#ffffff")
    info_label.pack()
    
    deadline_label = tk.Label(main_frame, text="", font=("Segoe UI", 14, "bold"), 
                            bg="#1e1e1e", fg="#00cec9")
    deadline_label.pack(pady=5)
    
    button_frame = tk.Frame(main_frame, bg="#1e1e1e")
    button_frame.pack(pady=10)
    
    def calculate_deadline():
        today = datetime.today()
        if goal_type == "Weight Gain":
            days_left = (goal_weight - current_weight) / 0.5  # 0.5kg per week
        else:
            days_left = (current_weight - goal_weight) / 0.5
            
        deadline = today + timedelta(days=days_left * 7)
        deadline_label.config(text=f"Estimated deadline: {deadline.strftime('%d %b, %Y')}")
    
    calculate_deadline()
    
    def show_day_plan():
        selected_date = calendar.get_date()
        selected_day = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A")
        muscle_group, exercises = muscle_workout_plan.get(selected_day, ("Rest", []))
        
        plan_win = tk.Toplevel(root)
        plan_win.title(f"Plan for {selected_date}")
        plan_win.geometry("500x600")
        plan_win.configure(bg="#1e1e1e")
        
        tk.Label(plan_win, text=f"Plan for {selected_date}", 
                font=("Segoe UI Black", 16), bg="#1e1e1e", fg="white").pack(pady=10)
        
        tk.Label(plan_win, text=f"Goal: {goal_type}", 
                font=("Segoe UI", 12, "italic"), bg="#1e1e1e", fg="#74b9ff").pack()
        
        tk.Label(plan_win, text="Are you a vegetarian?", 
                font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(pady=5)
        
        def show_meal_plan(is_veg):
            for widget in plan_win.winfo_children()[5:]:
                widget.destroy()
            
            meal_plan = meal_plans[goal_type]["Vegetarian" if is_veg else "Non-Vegetarian"]
            meal_data = []
            
            tk.Label(plan_win, text="\nMeal Plan:", 
                    font=("Segoe UI", 12, "bold"), bg="#1e1e1e", fg="white").pack(anchor='w', padx=20)
            
            for meal_type, details in meal_plan.items():
                meal_text = f"{meal_type}: {details['item']} ({details['calories']} cal, {details['protein']}g protein)"
                tk.Label(plan_win, text=meal_text, 
                        font=("Segoe UI", 12), bg="#1e1e1e", fg="#dfe6e9").pack(anchor='w', padx=20)
                
                meal_data.append({
                    "Username": current_user,
                    "Date": selected_date,
                    "Meal Type": meal_type,
                    "Food Item": details['item'],
                    "Calories": details['calories'],
                    "Protein (g)": details['protein'],
                    "Vegetarian": is_veg
                })
            
            if muscle_group != "Rest":
                tk.Label(plan_win, text=f"\nWorkout: {muscle_group}", 
                        font=("Segoe UI", 12, "bold"), bg="#1e1e1e", fg="white").pack(anchor='w', padx=20)
                
                workout_data = []
                for exercise in exercises:
                    tk.Label(plan_win, text=f"- {exercise}", 
                            font=("Segoe UI", 12), bg="#1e1e1e", fg="#dfe6e9").pack(anchor='w', padx=40)
                    
                    workout_data.append({
                        "Username": current_user,
                        "Date": selected_date,
                        "Muscle Group": muscle_group,
                        "Exercise": exercise,
                        "Sets": 3,
                        "Reps": 10,
                        "Duration (min)": 30 if "Cardio" in muscle_group else 0,
                        "Completed": True
                    })
            
            def save_and_close():
                save_data(meal_data, FOOD_SHEET)
                if muscle_group != "Rest":
                    save_data(workout_data, WORKOUT_SHEET)
                plan_win.destroy()
            
            tk.Button(plan_win, text="Mark as Done", 
                     font=("Segoe UI Black", 12), bg="#0984e3", fg="white",
                     command=save_and_close).pack(pady=20)
        
        tk.Button(plan_win, text="Vegetarian", 
                 font=("Segoe UI", 12), bg="#00b894", fg="white",
                 command=lambda: show_meal_plan(True)).pack(pady=10)
        
        tk.Button(plan_win, text="Non-Vegetarian", 
                 font=("Segoe UI", 12), bg="#d63031", fg="white",
                 command=lambda: show_meal_plan(False)).pack(pady=10)
    
    def log_weight():
        selected_date = calendar.get_date()
        
        log_win = tk.Toplevel(root)
        log_win.title("Log Weight")
        log_win.geometry("300x200")
        log_win.configure(bg="#1e1e1e")
        
        tk.Label(log_win, text=f"Enter weight for {selected_date}", 
                font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(pady=20)
        
        weight_entry = tk.Entry(log_win, font=("Segoe UI", 14, "bold"), 
                              bg="#2c2c2c", fg="white")
        weight_entry.pack(pady=5)
        
        def save_weight():
            try:
                weight = float(weight_entry.get())
                weight_data = {
                    "Username": current_user,
                    "Date": selected_date,
                    "Weight (kg)": weight,
                    "Goal Type": goal_type,
                    "Current Goal (kg)": goal_weight,
                    "Active": True
                }
                save_data(weight_data, WEIGHT_SHEET)
                log_win.destroy()
            except ValueError:
                tk.Label(log_win, text="Invalid number!", 
                        font=("Segoe UI", 10), bg="#1e1e1e", fg="red").pack()
        
        tk.Button(log_win, text="Save", 
                 font=("Segoe UI Black", 12), bg="#0984e3", fg="white",
                 command=save_weight).pack(pady=10)
    
    def show_reports():
        try:
            report_win = tk.Toplevel(root)
            report_win.title("Fitness Reports")
            report_win.geometry("1000x700")
            report_win.configure(bg="#1e1e1e")
            
            notebook = ttk.Notebook(report_win)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Weight Report
            weight_frame = tk.Frame(notebook, bg="#1e1e1e")
            notebook.add(weight_frame, text="Weight Progress")
            
            try:
                df = pd.read_excel(DATA_FILE, sheet_name=WEIGHT_SHEET)
                df = df[df['Username'] == current_user]
                if not df.empty:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.sort_values('Date')
                    
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.plot(df['Date'], df['Weight (kg)'], marker='o', color="#0984e3", label='Weight')
                    
                    if 'Current Goal (kg)' in df.columns:
                        goal_weight = df['Current Goal (kg)'].iloc[0]
                        ax.axhline(y=goal_weight, color='r', linestyle='--', label='Goal Weight')
                    
                    ax.set_title("Weight Progress")
                    ax.set_ylabel("Weight (kg)")
                    ax.legend()
                    ax.grid(True)
                    
                    canvas = FigureCanvasTkAgg(fig, master=weight_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
                else:
                    tk.Label(weight_frame, text="No weight data available", 
                            font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(pady=50)
            except Exception:
                tk.Label(weight_frame, text="Error loading weight data", 
                        font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(pady=50)
            
            # Nutrition Report
            nutrition_frame = tk.Frame(notebook, bg="#1e1e1e")
            notebook.add(nutrition_frame, text="Nutrition")
            
            try:
                df = pd.read_excel(DATA_FILE, sheet_name=FOOD_SHEET)
                df = df[df['Username'] == current_user]
                if not df.empty:
                    df['Date'] = pd.to_datetime(df['Date'])
                    nutrition_df = df.groupby('Date').agg({
                        'Calories': 'sum',
                        'Protein (g)': 'sum'
                    }).reset_index()
                    nutrition_df = nutrition_df.sort_values('Date')
                    
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
                    
                    ax1.plot(nutrition_df['Date'], nutrition_df['Calories'], 
                            marker='o', color="#00b894", label='Calories')
                    ax1.set_title("Daily Calorie Intake")
                    ax1.set_ylabel("Calories")
                    ax1.legend()
                    ax1.grid(True)
                    
                    ax2.plot(nutrition_df['Date'], nutrition_df['Protein (g)'], 
                            marker='o', color="#6c5ce7", label='Protein')
                    ax2.set_title("Daily Protein Intake")
                    ax2.set_ylabel("Protein (g)")
                    ax2.legend()
                    ax2.grid(True)
                    
                    plt.tight_layout()
                    
                    canvas = FigureCanvasTkAgg(fig, master=nutrition_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
                else:
                    tk.Label(nutrition_frame, text="No nutrition data available", 
                            font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(pady=50)
            except Exception:
                tk.Label(nutrition_frame, text="Error loading nutrition data", 
                        font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(pady=50)
            
            # Workout Report
            workout_frame = tk.Frame(notebook, bg="#1e1e1e")
            notebook.add(workout_frame, text="Workouts")
            
            try:
                df = pd.read_excel(DATA_FILE, sheet_name=WORKOUT_SHEET)
                df = df[df['Username'] == current_user]
                if not df.empty:
                    df['Date'] = pd.to_datetime(df['Date'])
                    workout_summary = df.groupby(['Date', 'Muscle Group']).size().unstack(fill_value=0)
                    
                    fig, ax = plt.subplots(figsize=(8, 4))
                    workout_summary.plot(kind='bar', stacked=True, ax=ax)
                    ax.set_title("Workout Frequency by Muscle Group")
                    ax.set_ylabel("Number of Exercises")
                    ax.legend(title="Muscle Group")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    canvas = FigureCanvasTkAgg(fig, master=workout_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
                else:
                    tk.Label(workout_frame, text="No workout data available", 
                            font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(pady=50)
            except Exception:
                tk.Label(workout_frame, text="Error loading workout data", 
                        font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(pady=50)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate reports: {str(e)}")
    
    def complete_goal():
        # Mark the current goal as inactive
        try:
            df = pd.read_excel(DATA_FILE, sheet_name=WEIGHT_SHEET)
            df.loc[(df['Username'] == current_user) & (df['Active'] == True), 'Active'] = False
            with pd.ExcelWriter(DATA_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=WEIGHT_SHEET, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Could not complete goal: {str(e)}")
        
        # Return to goal selection
        show_goal_window(root)
    
    tk.Button(button_frame, text="Show Plan", 
             font=("Segoe UI Black", 12), bg="#0984e3", fg="white",
             command=show_day_plan).pack(side=tk.LEFT, padx=5)
    
    tk.Button(button_frame, text="Log Weight", 
             font=("Segoe UI Black", 12), bg="#00b894", fg="white",
             command=log_weight).pack(side=tk.LEFT, padx=5)
    
    tk.Button(button_frame, text="View Reports", 
             font=("Segoe UI Black", 12), bg="#6c5ce7", fg="white",
             command=show_reports).pack(side=tk.LEFT, padx=5)
    
    tk.Button(main_frame, text="Complete Goal", 
             font=("Segoe UI Black", 12), bg="#d63031", fg="white",
             command=complete_goal).pack(pady=10)

# --- Main Application ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AuthWindow(root)
    root.mainloop()
