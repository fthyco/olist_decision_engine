import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import os
import sys

# ==========================================
# 1. SETUP & IMPORTS
# ==========================================
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from training_engine import OlistMasterEngineV5
except ImportError:
    print(" CRITICAL: 'final_simulation_engine.py' not found.")
    print("   Please save the engine code in the same folder as this launcher.")
    OlistMasterEngineV5 = None

# ==========================================
# 2. STYLING CONFIG
# ==========================================
OLIST_NAVY   = "#2D3270"
OLIST_TEAL   = "#00BFA5" 
OLIST_YELLOW = "#F9D500"
OLIST_BG     = "#F4F6F9"
OLIST_WHITE  = "#FFFFFF"
TEXT_DARK    = "#333333"

class OlistLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Olist Master Engine V5 | Control Center")
        self.root.geometry("700x680")
        self.root.configure(bg=OLIST_BG)
        
        self.set_icon()
        
        # Styles & Fonts
        self.title_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.normal_font = font.Font(family="Segoe UI", size=10)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=OLIST_WHITE, arrowcolor=OLIST_NAVY)

        # --- HEADER ---
        header = tk.Frame(root, bg=OLIST_NAVY, height=90)
        header.pack(fill="x")
        
        tk.Label(header, text="olist", bg=OLIST_NAVY, fg=OLIST_WHITE, 
                 font=("Century Gothic", 28, "bold")).pack(side="left", padx=20, pady=10)
        
        tk.Label(header, text="Master Simulation Engine V5", bg=OLIST_NAVY, fg=OLIST_YELLOW,
                 font=("Segoe UI", 10, "italic")).pack(side="left", pady=(30, 15))

        # --- MAIN FORM ---
        main_frame = tk.Frame(root, bg=OLIST_BG)
        main_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # 1. Scenario Name
        self.create_section_label(main_frame, "1. Simulation Identity")
        card1 = self.create_card(main_frame)
        
        tk.Label(card1, text="Batch / Scenario Name:", bg=OLIST_WHITE, font=self.normal_font).pack(anchor="w")
        self.entry_name = ttk.Entry(card1, font=("Segoe UI", 11))
        self.entry_name.pack(fill="x", pady=(5, 0))
        self.entry_name.insert(0, "Batch_01")

        # 2. Pattern Extraction Difficulty (Business Physics)
        self.create_section_label(main_frame, "2. Business Physics (Pattern Difficulty)")
        card2 = self.create_card(main_frame)
        
        tk.Label(card2, text="Market Volatility & Attribution Logic:", bg=OLIST_WHITE, font=self.normal_font).pack(anchor="w")
        self.var_market = tk.StringVar(value="Easy")
        cb_market = ttk.Combobox(card2, values=["Easy", "Medium", "Hard"], state="readonly", 
                                 textvariable=self.var_market, font=("Segoe UI", 10))
        cb_market.pack(fill="x", pady=5)
        cb_market.bind("<<ComboboxSelected>>", self.update_descriptions)
        
        self.lbl_market_desc = tk.Label(card2, text="", bg="#e3f2fd", fg="#1565c0", font=("Segoe UI", 9), anchor="w", padx=5)
        self.lbl_market_desc.pack(fill="x", pady=(5, 0))

        # 3. Preprocessing Difficulty (Data Engineering)
        self.create_section_label(main_frame, "3. Data Engineering (Chaos Layer)")
        card3 = self.create_card(main_frame)
        
        tk.Label(card3, text="Data Quality & Integrity Issues:", bg=OLIST_WHITE, font=self.normal_font).pack(anchor="w")
        self.var_data = tk.StringVar(value="Clean")
        cb_data = ttk.Combobox(card3, values=["Clean", "Messy", "Nightmare"], state="readonly", 
                               textvariable=self.var_data, font=("Segoe UI", 10))
        cb_data.pack(fill="x", pady=5)
        cb_data.bind("<<ComboboxSelected>>", self.update_descriptions)
        
        self.lbl_data_desc = tk.Label(card3, text="", bg="#e0f2f1", fg="#00695c", font=("Segoe UI", 9), anchor="w", padx=5)
        self.lbl_data_desc.pack(fill="x", pady=(5, 0))

        # --- ACTION BUTTON ---
        self.btn_run = tk.Button(root, text=" INITIALIZE MASTER ENGINE", bg=OLIST_YELLOW, fg=OLIST_NAVY,
                                 font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
                                 command=self.start_simulation)
        self.btn_run.pack(fill="x", side="bottom", padx=30, pady=20, ipady=5)

        self.status_bar = tk.Label(root, text="System Ready.", bg=OLIST_BG, fg="#777")
        self.status_bar.pack(side="bottom", fill="x", padx=30)

        # Initialize descriptions
        self.update_descriptions(None)

    # --- UI HELPERS ---
    def create_section_label(self, parent, text):
        tk.Label(parent, text=text, bg=OLIST_BG, fg=OLIST_NAVY, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(15, 5))

    def create_card(self, parent):
        frame = tk.Frame(parent, bg=OLIST_WHITE, bd=1, relief="solid")
        frame.pack(fill="x", pady=0, ipady=10)
        inner = tk.Frame(frame, bg=OLIST_WHITE)
        inner.pack(fill="x", padx=15, pady=5)
        return inner

    def set_icon(self):
        try:
            fallback_icon = tk.PhotoImage(width=32, height=32)
            fallback_icon.put(OLIST_NAVY, to=(0, 0, 31, 31))
            fallback_icon.put(OLIST_YELLOW, to=(10, 10, 22, 22))
            self.root.iconphoto(True, fallback_icon)
        except: pass

    def update_descriptions(self, event):
        # Market Physics Desc
        m_val = self.var_market.get()
        if m_val == "Easy": m_msg = "ℹ️ Clear Signals. High ROAS. Low Funnel Burn. Simple Linear Patterns."
        elif m_val == "Medium": m_msg = "ℹ️ Realistic Noise. Average ROAS. 30% Funnel Loss (Burn)."
        else: m_msg = "ℹ️ Crisis Mode. Low Efficiency. 60% Funnel Loss (Burn). Ops Constraints."
        self.lbl_market_desc.config(text=m_msg)

        # Data Quality Desc
        d_val = self.var_data.get()
        if d_val == "Clean": d_msg = " Pristine Data. No Nulls. No API Failures. Perfect Tracking."
        elif d_val == "Messy": d_msg = " Realistic Gaps. 5% Missing Attribution (Nulls). Occasional API drops."
        else: d_msg = " Data Hell. 20% Missing Pixels. Multi-day API Outages. Human Errors."
        self.lbl_data_desc.config(text=d_msg)

    # --- ENGINE LOGIC ---
    def start_simulation(self):
        name = self.entry_name.get()
        market_diff = self.var_market.get()
        data_diff = self.var_data.get()
        
        if not name:
            messagebox.showwarning("Validation Error", "Please enter a Scenario Name.")
            return

        # Folder structure: Name_Market-Hard_Data-Messy
        output_folder = os.path.join("Training_Output", f"{name}_M-{market_diff}_D-{data_diff}")
        
        self.btn_run.config(state="disabled", text=" ENGINE V5 PROCESSING...", bg="#ccc")
        self.status_bar.config(text="Running Simulation Pipeline...", fg=OLIST_NAVY)
        
        # Run in thread to keep GUI responsive
        threading.Thread(target=self.run_engine_logic, args=(market_diff, data_diff, output_folder)).start()

    def run_engine_logic(self, market_diff, data_diff, folder):
        try:
            if OlistMasterEngineV5 is None:
                raise Exception("Engine Class not found. Check 'final_simulation_engine.py'.")

            # 1. Initialize Engine with Market Physics
            sim = OlistMasterEngineV5(difficulty=market_diff, output_folder=folder)
            
            # 2. OVERRIDE Chaos Parameters based on Data Difficulty (Decoupling Logic)
            if data_diff == "Clean":
                sim.params['chaos_level'] = 0.0
                sim.params['missing_data_prob'] = 0.0
            elif data_diff == "Messy":
                sim.params['chaos_level'] = 0.05
                sim.params['missing_data_prob'] = 0.05
            elif data_diff == "Nightmare":
                sim.params['chaos_level'] = 0.20
                sim.params['missing_data_prob'] = 0.15
            
            print(f"🔧 GUI INJECTION: Chaos={sim.params['chaos_level']}, MissingProb={sim.params['missing_data_prob']}")

            # 3. Execute Pipeline
            sim.load_context()
            sim.simulate_marketing()
            sim.run_attribution_engine()
            sim.calculate_financials()
            sim.export() # This now handles CSV + Full DWH export

            self.root.after(0, lambda: self.finish_success(folder))

        except Exception as e:
            self.root.after(0, lambda: self.finish_error(str(e)))

    def finish_success(self, folder):
        self.btn_run.config(state="normal", text=" INITIALIZE MASTER ENGINE", bg=OLIST_YELLOW)
        self.status_bar.config(text="Simulation Complete.", fg="green")
        
        msg = f"Engine V5 Execution Successful!\n\n📂 Output Folder:\n{folder}\n\n📦 Note: A full 'dwh(ready_to_be_analyzed)' folder was also updated in the project root."
        resp = messagebox.askyesno("Success", msg + "\n\nOpen Output Folder?")
        if resp and os.name == 'nt':
            os.startfile(os.path.abspath(folder))

    def finish_error(self, err):
        self.btn_run.config(state="normal", text=" INITIALIZE MASTER ENGINE", bg=OLIST_YELLOW)
        self.status_bar.config(text="Execution Failed.", fg="red")
        messagebox.showerror("Simulation Error", f"Traceback:\n{err}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OlistLauncherApp(root)
    root.mainloop()