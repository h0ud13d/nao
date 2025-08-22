# -*- coding: future_fstrings -*-
import Tkinter as tk
import ttk
import time
import math
from datetime import datetime

class NaoControlGUI:
    def __init__(self, agent):
        self.agent = agent
        self.root = tk.Tk()
        self.root.title("NAO Robot Control Dashboard")
        self.root.configure(bg='#1e1e2f')  # Dark blue background
        
        # Set a minimum size for the window
        self.root.minsize(980, 600)
        
        # Movement variables
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.head_yaw = 0.0
        self.head_pitch = 0.0
        
        # Smoothing parameters for head movement
        self.head_smoothing = 0.2  # Lower value means smoother movement
        self.target_head_yaw = 0.0
        self.target_head_pitch = 0.0
        
        # Track which keys are currently pressed
        self.keys_pressed = set()
        
        # System stats
        self.start_time = time.time()
        self.operation_time = "00:00:00"
        
        # Initialize status_var
        self.status_var = tk.StringVar(value="Ready")
        
        self.setup_styles()
        self.setup_ui()
        
    def setup_styles(self):
        # Create custom styles for the widgets
        style = ttk.Style()
        
        # Configure the main background
        style.configure("Dashboard.TFrame", background='#1e1e2f')
        
        # Configure labels
        style.configure("Dashboard.TLabel", 
                       background='#1e1e2f', 
                       foreground='#ffffff',
                       font=('Helvetica', 10))
        
        # Configure headers
        style.configure("Header.TLabel", 
                       background='#1e1e2f', 
                       foreground='#5cccef',
                       font=('Helvetica', 12, 'bold'))
        
        # Configure control panel frames
        style.configure("ControlPanel.TFrame", 
                       background='#27293d', 
                       relief='raised',
                       borderwidth=1)
        
        # Configure buttons
        style.configure("Dashboard.TButton", 
                       background='#1d8cf8',
                       foreground='white',
                       font=('Helvetica', 10, 'bold'),
                       padding=5)
        
        # Configure status panel
        style.configure("Status.TLabel", 
                       background='#27293d', 
                       foreground='#00f2c3',
                       font=('Helvetica', 10))
        
        # Configure warning elements
        style.configure("Warning.TLabel", 
                       background='#27293d', 
                       foreground='#fd5d93',
                       font=('Helvetica', 10, 'bold'))
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, style="Dashboard.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top row - Title and system stats
        top_frame = ttk.Frame(main_frame, style="Dashboard.TFrame")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(top_frame, text="NAO ROBOT CONTROL SYSTEM", 
                              style="Header.TLabel", font=('Helvetica', 16, 'bold'))
        title_label.pack(side=tk.LEFT, padx=10)
        
        # System stats frame
        stats_frame = ttk.Frame(top_frame, style="ControlPanel.TFrame")
        stats_frame.pack(side=tk.RIGHT, padx=10)
        
        # Current time
        self.time_var = tk.StringVar(value="Time: 00:00:00")
        time_label = ttk.Label(stats_frame, textvariable=self.time_var, style="Status.TLabel")
        time_label.grid(row=0, column=0, padx=10, pady=5)
        
        # System uptime
        self.uptime_var = tk.StringVar(value="Uptime: 00:00:00")
        uptime_label = ttk.Label(stats_frame, textvariable=self.uptime_var, style="Status.TLabel")
        uptime_label.grid(row=0, column=1, padx=10, pady=5)
        
        # Bottom row - Content
        content_frame = ttk.Frame(main_frame, style="Dashboard.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left column - Control panels
        left_column = ttk.Frame(content_frame, style="Dashboard.TFrame")
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Body movement panel
        self.create_body_control_panel(left_column)
        
        # Head movement panel
        self.create_head_control_panel(left_column)
        
        # Center column - Camera view
        center_column = ttk.Frame(content_frame, style="Dashboard.TFrame")
        center_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Camera view panel
        self.create_camera_panel(center_column)
        
        # Right column - System status and indicators
        right_column = ttk.Frame(content_frame, style="Dashboard.TFrame")
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))
        
        # System status panel
        self.create_status_panel(right_column)
        
        # Current status display at the bottom
        status_display = ttk.Frame(main_frame, style="ControlPanel.TFrame")
        status_display.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        status_label = ttk.Label(status_display, textvariable=self.status_var, style="Status.TLabel")
        status_label.pack(fill=tk.X, padx=10, pady=5)
        
        # Initialize keybindings
        self.setup_keybindings()
        
        # Start system time update
        self.update_system_time()
        
    def create_body_control_panel(self, parent):
        panel = ttk.Frame(parent, style="ControlPanel.TFrame")
        panel.pack(fill=tk.X, pady=(0, 10))
        
        # Panel header
        header = ttk.Label(panel, text="BODY MOVEMENT CONTROL", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=3, padx=10, pady=5)
        
        # Current velocity indicators
        velocity_frame = ttk.Frame(panel, style="ControlPanel.TFrame")
        velocity_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky='ew')
        
        # X velocity indicator
        ttk.Label(velocity_frame, text="FWD/BWD:", style="Dashboard.TLabel").grid(row=0, column=0, padx=5, pady=2)
        self.x_velocity = tk.StringVar(value="0.0")
        ttk.Label(velocity_frame, textvariable=self.x_velocity, style="Status.TLabel").grid(row=0, column=1, padx=5, pady=2)
        
        # Y velocity indicator
        ttk.Label(velocity_frame, text="LEFT/RIGHT:", style="Dashboard.TLabel").grid(row=1, column=0, padx=5, pady=2)
        self.y_velocity = tk.StringVar(value="0.0")
        ttk.Label(velocity_frame, textvariable=self.y_velocity, style="Status.TLabel").grid(row=1, column=1, padx=5, pady=2)
        
        # Theta velocity indicator
        ttk.Label(velocity_frame, text="ROTATION:", style="Dashboard.TLabel").grid(row=2, column=0, padx=5, pady=2)
        self.theta_velocity = tk.StringVar(value="0.0")
        ttk.Label(velocity_frame, textvariable=self.theta_velocity, style="Status.TLabel").grid(row=2, column=1, padx=5, pady=2)
        
        # Control buttons with direction indicators
        ttk.Label(panel, text="W", style="Dashboard.TLabel").grid(row=2, column=1)
        forward_btn = ttk.Button(panel, text="FORWARD", style="Dashboard.TButton",
                               command=lambda: self.set_movement('w'))
        forward_btn.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(panel, text="A", style="Dashboard.TLabel").grid(row=4, column=0)
        left_btn = ttk.Button(panel, text="LEFT", style="Dashboard.TButton",
                            command=lambda: self.set_movement('a'))
        left_btn.grid(row=5, column=0, padx=5, pady=5)
        
        stop_btn = ttk.Button(panel, text="STOP", style="Dashboard.TButton",
                            command=self.stop_movement)
        stop_btn.grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(panel, text="D", style="Dashboard.TLabel").grid(row=4, column=2)
        right_btn = ttk.Button(panel, text="RIGHT", style="Dashboard.TButton",
                             command=lambda: self.set_movement('d'))
        right_btn.grid(row=5, column=2, padx=5, pady=5)
        
        ttk.Label(panel, text="S", style="Dashboard.TLabel").grid(row=6, column=1)
        backward_btn = ttk.Button(panel, text="BACKWARD", style="Dashboard.TButton",
                                command=lambda: self.set_movement('s'))
        backward_btn.grid(row=7, column=1, padx=5, pady=5)
        
        # Add some spacing at bottom
        ttk.Frame(panel, height=10, style="ControlPanel.TFrame").grid(row=8, column=0, columnspan=3)
    
    def create_head_control_panel(self, parent):
        panel = ttk.Frame(parent, style="ControlPanel.TFrame")
        panel.pack(fill=tk.X)
        
        # Panel header
        header = ttk.Label(panel, text="HEAD MOVEMENT CONTROL", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=3, padx=10, pady=5)
        
        # Current position indicators
        position_frame = ttk.Frame(panel, style="ControlPanel.TFrame")
        position_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky='ew')
        
        # Yaw position indicator
        ttk.Label(position_frame, text="YAW:", style="Dashboard.TLabel").grid(row=0, column=0, padx=5, pady=2)
        self.yaw_position = tk.StringVar(value="0.0°")
        ttk.Label(position_frame, textvariable=self.yaw_position, style="Status.TLabel").grid(row=0, column=1, padx=5, pady=2)
        
        # Pitch position indicator
        ttk.Label(position_frame, text="PITCH:", style="Dashboard.TLabel").grid(row=1, column=0, padx=5, pady=2)
        self.pitch_position = tk.StringVar(value="0.0°")
        ttk.Label(position_frame, textvariable=self.pitch_position, style="Status.TLabel").grid(row=1, column=1, padx=5, pady=2)
        
        # Control buttons with direction indicators
        ttk.Label(panel, text="↑", style="Dashboard.TLabel").grid(row=2, column=1)
        up_btn = ttk.Button(panel, text="UP", style="Dashboard.TButton",
                          command=lambda: self.set_head_movement('Up'))
        up_btn.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(panel, text="←", style="Dashboard.TLabel").grid(row=4, column=0)
        left_btn = ttk.Button(panel, text="LEFT", style="Dashboard.TButton",
                            command=lambda: self.set_head_movement('Left'))
        left_btn.grid(row=5, column=0, padx=5, pady=5)
        
        center_btn = ttk.Button(panel, text="CENTER", style="Dashboard.TButton",
                              command=self.center_head)
        center_btn.grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(panel, text="→", style="Dashboard.TLabel").grid(row=4, column=2)
        right_btn = ttk.Button(panel, text="RIGHT", style="Dashboard.TButton",
                             command=lambda: self.set_head_movement('Right'))
        right_btn.grid(row=5, column=2, padx=5, pady=5)
        
        ttk.Label(panel, text="↓", style="Dashboard.TLabel").grid(row=6, column=1)
        down_btn = ttk.Button(panel, text="DOWN", style="Dashboard.TButton",
                            command=lambda: self.set_head_movement('Down'))
        down_btn.grid(row=7, column=1, padx=5, pady=5)
        
        # Add some spacing at bottom
        ttk.Frame(panel, height=10, style="ControlPanel.TFrame").grid(row=8, column=0, columnspan=3)
    
    def create_camera_panel(self, parent):
        panel = ttk.Frame(parent, style="ControlPanel.TFrame")
        panel.pack(fill=tk.BOTH, expand=True)
        
        # Panel header
        header_frame = ttk.Frame(panel, style="ControlPanel.TFrame")
        header_frame.pack(fill=tk.X)
        
        header = ttk.Label(header_frame, text="CAMERA FEED", style="Header.TLabel")
        header.pack(side=tk.LEFT, padx=10, pady=5)
        
        # FPS indicator
        self.fps_display = tk.StringVar(value="FPS: 0")
        fps_label = ttk.Label(header_frame, textvariable=self.fps_display, style="Status.TLabel")
        fps_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Create a frame for the camera canvas with beveled border effect
        camera_border = ttk.Frame(panel, style="ControlPanel.TFrame")
        camera_border.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas for displaying camera image
        self.camera_canvas = tk.Canvas(camera_border, width=480, height=360, bg='black', 
                                    highlightthickness=1, highlightbackground='#4d5163')
        self.camera_canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Bind canvas resize event to update image position
        self.camera_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Add overlay elements to the canvas
        # Crosshair
        self.draw_crosshair()
        
        # Camera info overlay
        self.camera_info = self.camera_canvas.create_text(
            10, 10, text="CAM: MAIN | RES: 640x480", fill="#00f2c3", 
            font=('Helvetica', 10), anchor=tk.NW
        )
        
        # Initialize camera variables
        self.camera_id = 0
        self.camera_img = None
        self.camera_image_id = None
    
    def on_canvas_resize(self, event):
        """Handle canvas resize events to reposition image and overlays"""
        if hasattr(self, 'camera_image_id') and self.camera_image_id is not None:
            # Get new canvas dimensions
            canvas_width = event.width
            canvas_height = event.height
            center_x = canvas_width / 2
            center_y = canvas_height / 2
            
            # Update image position
            self.camera_canvas.coords(self.camera_image_id, center_x, center_y)
            
            # Redraw overlay elements with new dimensions
            self.draw_overlay_elements()
    
    def draw_crosshair(self):
        # Calculate canvas dimensions
        width = 480
        height = 360
        center_x = width / 2
        center_y = height / 2
        
        # Create crosshairs
        self.crosshair_h = self.camera_canvas.create_line(
            center_x - 20, center_y, center_x + 20, center_y, 
            fill="#5cccef", width=1, dash=(4, 4)
        )
        self.crosshair_v = self.camera_canvas.create_line(
            center_x, center_y - 20, center_x, center_y + 20, 
            fill="#5cccef", width=1, dash=(4, 4)
        )
        
        # Create target circle
        self.target_circle = self.camera_canvas.create_oval(
            center_x - 40, center_y - 40, center_x + 40, center_y + 40,
            outline="#5cccef", width=1, dash=(4, 4)
        )
    
    def create_status_panel(self, parent):
        panel = ttk.Frame(parent, style="ControlPanel.TFrame")
        panel.pack(fill=tk.X, pady=(0, 10))
        
        # Panel header
        header = ttk.Label(panel, text="SYSTEM STATUS", style="Header.TLabel")
        header.pack(padx=10, pady=5, fill=tk.X)
        
        # Status indicators
        status_frame = ttk.Frame(panel, style="ControlPanel.TFrame")
        status_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # Connection status
        ttk.Label(status_frame, text="CONNECTION:", style="Dashboard.TLabel").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.connection_status = tk.StringVar(value="ONLINE")
        ttk.Label(status_frame, textvariable=self.connection_status, style="Status.TLabel").grid(row=0, column=1, sticky='w', padx=5, pady=3)
        
        # Battery status
        ttk.Label(status_frame, text="BATTERY:", style="Dashboard.TLabel").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.battery_status = tk.StringVar(value="75%")
        ttk.Label(status_frame, textvariable=self.battery_status, style="Status.TLabel").grid(row=1, column=1, sticky='w', padx=5, pady=3)
        
        # Motor status
        ttk.Label(status_frame, text="MOTORS:", style="Dashboard.TLabel").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.motor_status = tk.StringVar(value="ACTIVE")
        ttk.Label(status_frame, textvariable=self.motor_status, style="Status.TLabel").grid(row=2, column=1, sticky='w', padx=5, pady=3)
        
        # System load
        ttk.Label(status_frame, text="CPU LOAD:", style="Dashboard.TLabel").grid(row=3, column=0, sticky='w', padx=5, pady=3)
        self.cpu_status = tk.StringVar(value="32%")
        ttk.Label(status_frame, textvariable=self.cpu_status, style="Status.TLabel").grid(row=3, column=1, sticky='w', padx=5, pady=3)
        
        # Add operation log panel
        log_panel = ttk.Frame(parent, style="ControlPanel.TFrame")
        log_panel.pack(fill=tk.BOTH, expand=True)
        
        log_header = ttk.Label(log_panel, text="OPERATION LOG", style="Header.TLabel")
        log_header.pack(padx=10, pady=5, fill=tk.X)
        
        # Log text area
        self.log_frame = ttk.Frame(log_panel, style="ControlPanel.TFrame")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(self.log_frame, height=10, width=30, bg='#2b2d42', fg='#00f2c3',
                              font=('Courier', 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Add some initial log entries
        self.add_log_entry("System initialized")
        self.add_log_entry("Camera system online")
        self.add_log_entry("NAO robot connected")
        self.add_log_entry("Motors activated")
        self.add_log_entry("Ready for operation")
        
        # Create emergency stop button
        emergency_panel = ttk.Frame(parent, style="ControlPanel.TFrame")
        emergency_panel.pack(fill=tk.X, pady=(10, 0))
        
        emergency_btn = ttk.Button(emergency_panel, text="EMERGENCY STOP", 
                                 style="Dashboard.TButton",
                                 command=self.emergency_stop)
        emergency_btn.pack(fill=tk.X, padx=10, pady=10)
    
    def setup_keybindings(self):
        # Keyboard bindings for WASD (body movement)
        for key in ['w', 'a', 's', 'd', 'W', 'A', 'S', 'D']:
            lower_key = key.lower()
            self.root.bind(f"<KeyPress-{key}>", lambda e, k=lower_key: self.key_press(k))
            self.root.bind(f"<KeyRelease-{key}>", lambda e, k=lower_key: self.key_release(k))
        
        # Keyboard bindings for arrow keys (head movement)
        self.root.bind("<KeyPress-Up>", lambda e: self.head_key_press('Up'))
        self.root.bind("<KeyPress-Down>", lambda e: self.head_key_press('Down'))
        self.root.bind("<KeyPress-Left>", lambda e: self.head_key_press('Left'))
        self.root.bind("<KeyPress-Right>", lambda e: self.head_key_press('Right'))
        self.root.bind("<KeyRelease-Up>", lambda e: self.head_key_release('Up'))
        self.root.bind("<KeyRelease-Down>", lambda e: self.head_key_release('Down'))
        self.root.bind("<KeyRelease-Left>", lambda e: self.head_key_release('Left'))
        self.root.bind("<KeyRelease-Right>", lambda e: self.head_key_release('Right'))
        
        # Quit keybindings
        self.root.bind("<KeyPress-q>", lambda e: self.quit_program())
        self.root.bind("<KeyPress-Q>", lambda e: self.quit_program())
        
        # Emergency stop keybinding
        self.root.bind("<KeyPress-Escape>", self.emergency_stop)
        
        # Prevent window closing via the 'X' button from causing errors
        self.root.protocol("WM_DELETE_WINDOW", self.quit_program)
    
    def update_system_time(self):
        # Update time display
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_var.set(f"Time: {current_time}")
        
        # Update uptime
        elapsed_seconds = int(time.time() - self.start_time)
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.uptime_var.set(f"Uptime: {uptime_str}")
        
        # Schedule next update
        self.root.after(1000, self.update_system_time)
        
        # Update simulated status values (for demonstration)
        self.update_status_indicators()
    
    def update_status_indicators(self):
        # Simulate changing values for indicators
        # In a real implementation, these would be updated from the robot
        
        # CPU load - simulated oscillation
        cpu_load = 25 + 10 * math.sin(time.time() / 10.0)
        self.cpu_status.set(f"{int(cpu_load)}%")
        
        # Battery - slowly decreasing
        current_battery = int(self.battery_status.get().replace('%', ''))
        new_battery = max(0, current_battery - (0.1 if time.time() % 10 < 0.1 else 0))
        self.battery_status.set(f"{int(new_battery)}%")
    
    def add_log_entry(self, message):
        # Add timestamp and message to log
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Insert at the end
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # Scroll to the end
        self.log_text.configure(state='disabled')
    
    def key_press(self, key):
        """Add key to the set of pressed keys and update body movement"""
        self.keys_pressed.add(key)
        self.update_movement_vector()
        
    def key_release(self, key):
        """Remove key from the set of pressed keys and update body movement"""
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
        self.update_movement_vector()
        
    def head_key_press(self, key):
        """Update head movement based on arrow keys with smoothing"""
        if key == 'Up':
            self.head_pitch = 0.1  # Look up
            self.target_head_pitch = 0.1
        elif key == 'Down':
            self.head_pitch = -0.1  # Look down
            self.target_head_pitch = -0.1
        elif key == 'Left':
            self.head_yaw = 0.2  # Turn head left
            self.target_head_yaw = 0.2
        elif key == 'Right':
            self.head_yaw = -0.1  # Turn head right
            self.target_head_yaw = -0.1
        # Update display
        self.yaw_position.set(f"{self.head_yaw * 57.3:.1f}°")
        self.pitch_position.set(f"{self.head_pitch * 57.3:.1f}°")
        
    def head_key_release(self, key):
        """Stop head movement when arrow keys are released"""
        if key in ['Up', 'Down']:
            self.head_pitch = 0.0
            self.target_head_pitch = 0.0
        elif key in ['Left', 'Right']:
            self.head_yaw = 0.0
            self.target_head_yaw = 0.0
        # Update display
        self.yaw_position.set(f"{self.head_yaw * 57.3:.1f}°")
        self.pitch_position.set(f"{self.head_pitch * 57.3:.1f}°")
        
    def set_movement(self, key):
        """Button press handler for body movement"""
        self.keys_pressed.add(key)
        self.update_movement_vector()
        
        # Add to log
        movement_type = {
            'w': 'forward', 
            'a': 'left', 
            's': 'backward', 
            'd': 'right'
        }
        self.add_log_entry(f"Body movement: {movement_type.get(key, 'unknown')}")
    
    def set_head_movement(self, key):
        """Button press handler for head movement"""
        self.head_key_press(key)
        
        # Add to log
        movement_type = {
            'Up': 'up', 
            'Down': 'down', 
            'Left': 'left', 
            'Right': 'right'
        }
        self.add_log_entry(f"Head movement: {movement_type.get(key, 'unknown')}")
        
        # Auto-reset head movement values after a short delay
        # Using a longer delay for more noticeable movement
        self.root.after(1000, lambda: self.head_key_release(key))
    
    def center_head(self):
        """Center the head position"""
        # Set immediate values directly
        self.target_head_yaw = 0.0
        self.target_head_pitch = 0.0
        self.head_yaw = 0.0
        self.head_pitch = 0.0
        
        # Update display
        self.yaw_position.set(f"{self.head_yaw * 57.3:.1f}°")
        self.pitch_position.set(f"{self.head_pitch * 57.3:.1f}°")
        
        # Send a special command to return head to center position
        self.agent.movehead(0, 0, center=True)
        
        # Add to log
        self.add_log_entry("Head centered")
        
    def emergency_stop(self, event=None):
        """Emergency stop - halt all movement"""
        self.stop_movement()
        self.center_head()
        
        # Add to log with warning
        self.add_log_entry("EMERGENCY STOP ACTIVATED")
        
        # Flash the log red briefly
        current_bg = self.log_text.cget("background")
        self.log_text.configure(background="#8B0000")  # Dark red
        self.root.after(500, lambda: self.log_text.configure(background=current_bg))
        
        # Add an option to quit
        quit_button = ttk.Button(self.root, text="QUIT PROGRAM", 
                              style="Dashboard.TButton",
                              command=self.quit_program)
        quit_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.root.after(5000, quit_button.destroy)  # Remove after 5 seconds
    
    def quit_program(self):
        """Safely quit the program"""
        self.add_log_entry("Shutting down system")
        self.agent.stop_camera()
        self.root.quit()
        self.root.destroy()
        
    def stop_movement(self):
        """Stop all movement"""
        self.keys_pressed.clear()
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.update_movement_vector()
        
        # Add to log
        self.add_log_entry("Movement stopped")
        
    def update_movement_vector(self):
        """Calculate movement based on currently pressed keys"""
        # Reset movement values
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        # Add movement for each pressed key
        if 'w' in self.keys_pressed:
            self.x += 0.5  # Forward
        if 's' in self.keys_pressed:
            self.x -= 0.5  # Backward
        if 'a' in self.keys_pressed:
            self.y += 0.5  # Left
        if 'd' in self.keys_pressed:
            self.y -= 0.5  # Right
            
        # Update display values
        self.x_velocity.set(f"{self.x:.1f}")
        self.y_velocity.set(f"{self.y:.1f}")
        self.theta_velocity.set(f"{self.theta:.1f}")
        
    def update_head_position(self):
        """Update head position with smoothing"""
        # Apply smoothing - gradually move towards target position
        if self.head_yaw != self.target_head_yaw:
            delta = self.target_head_yaw - self.head_yaw
            self.head_yaw += delta * self.head_smoothing
            
            # If very close to target, snap to it
            if abs(delta) < 0.01:
                self.head_yaw = self.target_head_yaw
        
        if self.head_pitch != self.target_head_pitch:
            delta = self.target_head_pitch - self.head_pitch
            self.head_pitch += delta * self.head_smoothing
            
            # If very close to target, snap to it
            if abs(delta) < 0.01:
                self.head_pitch = self.target_head_pitch
        
        # Update display values (convert to degrees for display)
        self.yaw_position.set(f"{self.head_yaw * 57.3:.1f}°")  # Convert radians to degrees
        self.pitch_position.set(f"{self.head_pitch * 57.3:.1f}°")
    
    def update_camera_display(self, image, fps):
        """Callback function for camera controller"""
        if image:
            # Store current image reference to avoid garbage collection
            self.camera_img = image
            
            # Get canvas dimensions
            canvas_width = self.camera_canvas.winfo_width() or 480
            canvas_height = self.camera_canvas.winfo_height() or 360
            
            # Center the image on the canvas
            center_x = canvas_width / 2
            center_y = canvas_height / 2
            
            # Check if camera image already exists on canvas
            if not hasattr(self, 'camera_image_id') or self.camera_image_id is None:
                # Create image for the first time
                self.camera_image_id = self.camera_canvas.create_image(
                    center_x, center_y, anchor='center', 
                    image=self.camera_img, tags="camera_image"
                )
            else:
                # Update existing image position and content
                self.camera_canvas.coords(self.camera_image_id, center_x, center_y)
                self.camera_canvas.itemconfig(self.camera_image_id, image=self.camera_img)
            
            # Redraw the overlay elements (they get covered by the new image)
            # This will be called on each frame update
            self.draw_overlay_elements()
            
            # Update FPS display
            self.fps_display.set(f"FPS: {fps}")
    
    def draw_overlay_elements(self):
        """Redraw overlay elements on the camera feed"""
        width = self.camera_canvas.winfo_width() or 480
        height = self.camera_canvas.winfo_height() or 360
        center_x = width / 2
        center_y = height / 2
        
        # Update crosshair position
        self.camera_canvas.coords(self.crosshair_h, center_x - 20, center_y, center_x + 20, center_y)
        self.camera_canvas.coords(self.crosshair_v, center_x, center_y - 20, center_x, center_y + 20)
        
        # Update target circle
        self.camera_canvas.coords(self.target_circle, 
                               center_x - 40, center_y - 40, 
                               center_x + 40, center_y + 40)
        
        # Update camera info text - add current time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.camera_canvas.itemconfig(
            self.camera_info, 
            text=f"CAM: MAIN | RES: 640x480 | {current_time}"
        )
    
    def update_status(self):
        """Send the current movement values to the robot every 100ms"""
        # Send movement commands to robot
        self.agent.walk(self.x, self.y, self.theta)
        
        # Always send head movement to ensure responsiveness
        self.agent.movehead(self.head_yaw, self.head_pitch)
        
        # Schedule next update
        self.root.after(50, self.update_status)  # Faster updates for smoother movement
        
    def run(self):
        # Fixed to use only the top camera (ID=0)
        self.camera_id = 0
        
        # Start camera with callback function
        self.agent.camera_controller.camera_id = 0  # Ensure using top camera
        self.agent.start_camera(self.update_camera_display)
        
        # Start the movement update loop
        self.update_status()
        
        # Add initialization log
        self.add_log_entry("Control system ready")
        
        # Start the GUI event loop
        self.root.mainloop()
        
        # Clean up when GUI is closed
        self.agent.stop_camera()
        
    def key_press(self, key):
        """Add key to the set of pressed keys and update body movement"""
        self.keys_pressed.add(key)
        self.update_movement_vector()
        
    def key_release(self, key):
        """Remove key from the set of pressed keys and update body movement"""
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
        self.update_movement_vector()
        
    def head_key_press(self, key):
        """Update head movement based on arrow keys"""
        if key == 'Up':
            self.head_pitch = 0.1  # Look up
        elif key == 'Down':
            self.head_pitch = -0.1  # Look down
        elif key == 'Left':
            self.head_yaw = 0.2  # Turn head left
        elif key == 'Right':
            self.head_yaw = -0.1  # Turn head right
            
        # Update head position displays
        self.yaw_position.set(f"{self.head_yaw * 57.3:.1f}°")  # Convert radians to degrees
        self.pitch_position.set(f"{self.head_pitch * 57.3:.1f}°")
        
        self.update_status_display()
        
    def head_key_release(self, key):
        """Stop head movement when arrow keys are released"""
        if key in ['Up', 'Down']:
            self.head_pitch = 0.0
        elif key in ['Left', 'Right']:
            self.head_yaw = 0.0
            
        # Update head position displays
        self.yaw_position.set(f"{self.head_yaw * 57.3:.1f}°")  # Convert radians to degrees
        self.pitch_position.set(f"{self.head_pitch * 57.3:.1f}°")
        
        self.update_status_display()
        
    def set_movement(self, key):
        """Button press handler for body movement"""
        self.keys_pressed.add(key)
        self.update_movement_vector()
    
    def set_head_movement(self, key):
        """Button press handler for head movement"""
        self.head_key_press(key)
        # Auto-reset head movement values after a short delay
        self.root.after(100, lambda: self.head_key_release(key))
    
    def center_head(self):
        """Center the head position"""
        self.head_yaw = 0.0
        self.head_pitch = 0.0
        
        # Update head position displays
        self.yaw_position.set(f"{self.head_yaw * 57.3:.1f}°")  # Convert radians to degrees
        self.pitch_position.set(f"{self.head_pitch * 57.3:.1f}°")
        
        self.update_status_display()
        # Send a special command to return head to center position
        self.agent.movehead(0, 0, center=True)
        
    def stop_movement(self):
        """Stop all movement"""
        self.keys_pressed.clear()
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        # Update velocity displays
        self.x_velocity.set(f"{self.x:.1f}")
        self.y_velocity.set(f"{self.y:.1f}")
        self.theta_velocity.set(f"{self.theta:.1f}")
        
        self.update_status_display()
        
    def update_movement_vector(self):
        """Calculate movement based on currently pressed keys"""
        # Reset movement values
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        # Add movement for each pressed key
        if 'w' in self.keys_pressed:
            self.x += 0.5  # Forward
        if 's' in self.keys_pressed:
            self.x -= 0.5  # Backward
        if 'a' in self.keys_pressed:
            self.y += 0.5  # Left
        if 'd' in self.keys_pressed:
            self.y -= 0.5  # Right
        
        # Update velocity displays
        self.x_velocity.set(f"{self.x:.1f}")
        self.y_velocity.set(f"{self.y:.1f}")
        self.theta_velocity.set(f"{self.theta:.1f}")
            
        self.update_status_display()
        
    def update_camera_display_legacy(self, image, fps):
        """Legacy callback function for camera controller"""
        if image:
            # Clear previous image
            self.camera_canvas.delete("camera_image")
            
            # Store current image reference to avoid garbage collection
            self.camera_img = image
            
            # Get canvas dimensions
            canvas_width = self.camera_canvas.winfo_width() or 480
            canvas_height = self.camera_canvas.winfo_height() or 360
            
            # Center the image on the canvas
            center_x = canvas_width / 2
            center_y = canvas_height / 2
            
            # Update canvas with the image, centered
            self.camera_canvas.create_image(center_x, center_y, anchor='center', 
                                           image=self.camera_img, tags="camera_image")
            
            # Update FPS display
            self.fps_display.set(f"FPS: {fps}")

    def update_status_display(self):
        """Update the status display with current movement values"""
        status = f"Body: x={self.x:.1f}, y={self.y:.1f}, θ={self.theta:.1f}"
        if self.head_yaw != 0.0 or self.head_pitch != 0.0:
            status += f" | Head: yaw={self.head_yaw:.1f}, pitch={self.head_pitch:.1f}"
        self.status_var.set(status)
        
    def update_status(self):
        """Send the current movement values to the robot every 100ms"""
        self.agent.walk(self.x, self.y, self.theta)
        if self.head_yaw != 0.0 or self.head_pitch != 0.0:
            self.agent.movehead(self.head_yaw, self.head_pitch)
        self.root.after(100, self.update_status)
        
    def run(self):
        # Fixed to use only the top camera (ID=0)
        self.camera_id = 0
        
        # Start camera with callback function
        self.agent.camera_controller.camera_id = 0  # Ensure using top camera
        self.agent.start_camera(self.update_camera_display)
        
        # Start the movement update loop
        self.update_status()
        
        # Start the GUI event loop
        self.root.mainloop()
        
        # Clean up when GUI is closed
        self.agent.stop_camera()
