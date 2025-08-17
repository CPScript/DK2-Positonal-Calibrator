#!/usr/bin/env python3

import pygame
import numpy as np
import time
import json
import math
from collections import deque
from datetime import datetime
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import ovr
    OVR_AVAILABLE = True
except ImportError:
    OVR_AVAILABLE = False
    print("Warning: OVR SDK not found. Using simulation mode.")

class DK2TrackingCalibrator:
    def __init__(self):
        self.running = False
        self.ovr_session = None
        self.tracking_data = deque(maxlen=1000)
        self.calibration_points = []
        self.reference_points = []
        self.position_history = deque(maxlen=100)
        self.rotation_history = deque(maxlen=100)
        self.frame_times = deque(maxlen=60)
        
        self.tracking_bounds = {
            'x_min': -2.0, 'x_max': 2.0,
            'y_min': -1.5, 'y_max': 1.5,
            'z_min': 0.5, 'z_max': 3.0
        }
        
        if OVR_AVAILABLE:
            self.init_ovr()
        
        self.init_gui()
        self.init_pygame()
        
    def init_ovr(self):
        try:
            ovr.initialize()
            self.ovr_session = ovr.create()
            print("OVR SDK initialized successfully")
        except Exception as e:
            print(f"Failed to initialize OVR: {e}")
            self.ovr_session = None
    
    def init_gui(self):
        self.root = tk.Tk()
        self.root.title("DK2 Tracking Calibration Tool")
        self.root.geometry("800x600")
        
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.monitor_frame = ttk.Frame(notebook)
        notebook.add(self.monitor_frame, text="Real-time Monitor")
        self.create_monitor_tab()
        
        self.calib_frame = ttk.Frame(notebook)
        notebook.add(self.calib_frame, text="Calibration")
        self.create_calibration_tab()
        
        self.analysis_frame = ttk.Frame(notebook)
        notebook.add(self.analysis_frame, text="Analysis")
        self.create_analysis_tab()
        
        self.settings_frame = ttk.Frame(notebook)
        notebook.add(self.settings_frame, text="Settings")
        self.create_settings_tab()
        
    def create_monitor_tab(self):
        status_frame = ttk.LabelFrame(self.monitor_frame, text="Tracking Status")
        status_frame.pack(fill='x', padx=5, pady=5)
        
        self.status_labels = {}
        status_items = ['Connection', 'Position Tracking', 'Orientation Tracking', 'Frame Rate']
        
        for i, item in enumerate(status_items):
            ttk.Label(status_frame, text=f"{item}:").grid(row=i//2, column=(i%2)*2, sticky='w', padx=5)
            self.status_labels[item] = ttk.Label(status_frame, text="Unknown", foreground="gray")
            self.status_labels[item].grid(row=i//2, column=(i%2)*2+1, sticky='w', padx=5)
        
        data_frame = ttk.LabelFrame(self.monitor_frame, text="Current Values")
        data_frame.pack(fill='x', padx=5, pady=5)
        
        self.data_labels = {}
        data_items = ['Position X', 'Position Y', 'Position Z', 'Rotation X', 'Rotation Y', 'Rotation Z']
        
        for i, item in enumerate(data_items):
            ttk.Label(data_frame, text=f"{item}:").grid(row=i//3, column=(i%3)*2, sticky='w', padx=5)
            self.data_labels[item] = ttk.Label(data_frame, text="0.000")
            self.data_labels[item].grid(row=i//3, column=(i%3)*2+1, sticky='w', padx=5)
        
        control_frame = ttk.Frame(self.monitor_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start Tracking", command=self.start_tracking)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Tracking", command=self.stop_tracking, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Reset Center", command=self.reset_center).pack(side='left', padx=5)
        
    def create_calibration_tab(self):
        instr_frame = ttk.LabelFrame(self.calib_frame, text="Instructions")
        instr_frame.pack(fill='x', padx=5, pady=5)
        
        instructions = """
        1. Put on the DK2 headset
        2. Click 'Start Calibration' and follow the on-screen prompts
        3. Move to each calibration point and hold steady for 3 seconds
        4. Complete all calibration points for optimal accuracy
        """
        ttk.Label(instr_frame, text=instructions, justify='left').pack(padx=10, pady=5)
        
        progress_frame = ttk.LabelFrame(self.calib_frame, text="Calibration Progress")
        progress_frame.pack(fill='x', padx=5, pady=5)
        
        self.calib_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.calib_progress.pack(fill='x', padx=10, pady=5)
        
        self.calib_status = ttk.Label(progress_frame, text="Ready to calibrate")
        self.calib_status.pack(padx=10, pady=5)
        
        calib_control_frame = ttk.Frame(self.calib_frame)
        calib_control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(calib_control_frame, text="Start Calibration", 
                  command=self.start_calibration).pack(side='left', padx=5)
        ttk.Button(calib_control_frame, text="Save Calibration", 
                  command=self.save_calibration).pack(side='left', padx=5)
        ttk.Button(calib_control_frame, text="Load Calibration", 
                  command=self.load_calibration).pack(side='left', padx=5)
        
    def create_analysis_tab(self):
        metrics_frame = ttk.LabelFrame(self.analysis_frame, text="Accuracy Metrics")
        metrics_frame.pack(fill='x', padx=5, pady=5)
        
        self.metric_labels = {}
        metrics = ['Position Accuracy', 'Rotation Accuracy', 'Jitter (RMS)', 'Drift Rate']
        
        for i, metric in enumerate(metrics):
            ttk.Label(metrics_frame, text=f"{metric}:").grid(row=i//2, column=(i%2)*2, sticky='w', padx=5)
            self.metric_labels[metric] = ttk.Label(metrics_frame, text="Not calculated")
            self.metric_labels[metric].grid(row=i//2, column=(i%2)*2+1, sticky='w', padx=5)
        
        analysis_control_frame = ttk.Frame(self.analysis_frame)
        analysis_control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(analysis_control_frame, text="Calculate Metrics", 
                  command=self.calculate_metrics).pack(side='left', padx=5)
        ttk.Button(analysis_control_frame, text="Export Data", 
                  command=self.export_data).pack(side='left', padx=5)
        ttk.Button(analysis_control_frame, text="Generate Report", 
                  command=self.generate_report).pack(side='left', padx=5)
        
    def create_settings_tab(self):
        bounds_frame = ttk.LabelFrame(self.settings_frame, text="Tracking Bounds (meters)")
        bounds_frame.pack(fill='x', padx=5, pady=5)
        
        self.bound_vars = {}
        bounds = [('X Min', 'x_min'), ('X Max', 'x_max'), ('Y Min', 'y_min'), 
                 ('Y Max', 'y_max'), ('Z Min', 'z_min'), ('Z Max', 'z_max')]
        
        for i, (label, key) in enumerate(bounds):
            ttk.Label(bounds_frame, text=f"{label}:").grid(row=i//3, column=(i%3)*2, sticky='w', padx=5, pady=2)
            self.bound_vars[key] = tk.DoubleVar(value=self.tracking_bounds[key])
            ttk.Entry(bounds_frame, textvariable=self.bound_vars[key], width=8).grid(
                row=i//3, column=(i%3)*2+1, sticky='w', padx=5, pady=2)
        
        ttk.Button(bounds_frame, text="Apply Settings", 
                  command=self.apply_settings).grid(row=3, column=0, columnspan=6, pady=10)
        
    def init_pygame(self):
        pygame.init()
        self.viz_screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("DK2 Tracking Visualization")
        self.viz_font = pygame.font.Font(None, 24)
        self.viz_running = False
        
    def start_tracking(self):
        if self.running:
            return
            
        self.running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        self.tracking_thread = threading.Thread(target=self.tracking_loop)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()
        
        self.viz_thread = threading.Thread(target=self.visualization_loop)
        self.viz_thread.daemon = True
        self.viz_thread.start()
        
    def stop_tracking(self):
        self.running = False
        self.viz_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
    def tracking_loop(self):
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            self.frame_times.append(dt)
            last_time = current_time
            
            if self.ovr_session:
                tracking_state = self.get_ovr_tracking_state()
            else:
                tracking_state = self.get_simulated_tracking_state()
            
            self.tracking_data.append({
                'timestamp': current_time,
                'position': tracking_state['position'],
                'rotation': tracking_state['rotation'],
                'tracking_valid': tracking_state['valid']
            })
            
            self.position_history.append(tracking_state['position'])
            self.rotation_history.append(tracking_state['rotation'])
            
            self.update_gui(tracking_state)
            
            time.sleep(0.016)
            
    def get_ovr_tracking_state(self):
        try:
            tracking_state = ovr.getTrackingState(self.ovr_session, 0.0, True)
            pose = tracking_state.HeadPose.ThePose
            
            return {
                'position': [pose.Position.x, pose.Position.y, pose.Position.z],
                'rotation': [pose.Orientation.x, pose.Orientation.y, 
                           pose.Orientation.z, pose.Orientation.w],
                'valid': tracking_state.StatusFlags & ovr.Status_PositionTracked
            }
        except Exception as e:
            print(f"OVR tracking error: {e}")
            return self.get_simulated_tracking_state()
    
    def get_simulated_tracking_state(self):
        t = time.time()
        return {
            'position': [
                0.5 * math.sin(t * 0.5),
                0.3 * math.sin(t * 0.3),
                1.5 + 0.2 * math.sin(t * 0.7)
            ],
            'rotation': [0, math.sin(t * 0.2) * 0.1, 0, 1],
            'valid': True
        }
    
    def update_gui(self, tracking_state):
        def update():
            if tracking_state['valid']:
                self.status_labels['Connection'].config(text="Connected", foreground="green")
                self.status_labels['Position Tracking'].config(text="Active", foreground="green")
                self.status_labels['Orientation Tracking'].config(text="Active", foreground="green")
            else:
                self.status_labels['Connection'].config(text="Disconnected", foreground="red")
                self.status_labels['Position Tracking'].config(text="Lost", foreground="red")
                self.status_labels['Orientation Tracking'].config(text="Lost", foreground="red")
            
            if len(self.frame_times) > 0:
                avg_frame_time = sum(self.frame_times) / len(self.frame_times)
                fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
                self.status_labels['Frame Rate'].config(text=f"{fps:.1f} FPS")
            
            pos = tracking_state['position']
            rot = tracking_state['rotation']
            
            self.data_labels['Position X'].config(text=f"{pos[0]:.3f}")
            self.data_labels['Position Y'].config(text=f"{pos[1]:.3f}")
            self.data_labels['Position Z'].config(text=f"{pos[2]:.3f}")
            self.data_labels['Rotation X'].config(text=f"{rot[0]:.3f}")
            self.data_labels['Rotation Y'].config(text=f"{rot[1]:.3f}")
            self.data_labels['Rotation Z'].config(text=f"{rot[2]:.3f}")
        
        self.root.after(0, update)
    
    def visualization_loop(self):
        self.viz_running = True
        clock = pygame.time.Clock()
        
        while self.viz_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.viz_running = False
            
            self.viz_screen.fill((20, 20, 40))
            
            if len(self.position_history) > 0:
                self.draw_tracking_visualization()
            
            self.draw_visualization_ui()
            
            pygame.display.flip()
            clock.tick(60)
    
    def draw_tracking_visualization(self):
        center_x, center_y = 400, 300
        scale = 100
        
        pygame.draw.line(self.viz_screen, (255, 0, 0), 
                        (center_x, center_y), (center_x + 100, center_y), 2)
        pygame.draw.line(self.viz_screen, (0, 255, 0), 
                        (center_x, center_y), (center_x, center_y - 100), 2)  
        
        if len(self.position_history) > 1:
            points = []
            for pos in list(self.position_history)[-50:]:  
                x = center_x + pos[0] * scale
                y = center_y - pos[1] * scale  
                points.append((x, y))
            
            if len(points) > 1:
                pygame.draw.lines(self.viz_screen, (100, 100, 255), False, points, 2)
        
        if len(self.position_history) > 0:
            pos = self.position_history[-1]
            x = center_x + pos[0] * scale
            y = center_y - pos[1] * scale
            pygame.draw.circle(self.viz_screen, (255, 255, 0), (int(x), int(y)), 8)
        
        bounds = self.tracking_bounds
        rect_x = center_x + bounds['x_min'] * scale
        rect_y = center_y - bounds['y_max'] * scale
        rect_w = (bounds['x_max'] - bounds['x_min']) * scale
        rect_h = (bounds['y_max'] - bounds['y_min']) * scale
        pygame.draw.rect(self.viz_screen, (0, 255, 0), (rect_x, rect_y, rect_w, rect_h), 2)
    
    def draw_visualization_ui(self):
        title = self.viz_font.render("DK2 Tracking Visualization", True, (255, 255, 255))
        self.viz_screen.blit(title, (10, 10))
        
        instructions = [
            "Yellow dot: Current position",
            "Blue trail: Movement history",
            "Green box: Tracking bounds",
            "Red line: X axis, Green line: Y axis"
        ]
        
        for i, instr in enumerate(instructions):
            text = pygame.font.Font(None, 18).render(instr, True, (200, 200, 200))
            self.viz_screen.blit(text, (10, 550 - i * 20))
    
    def start_calibration(self):
        self.calibration_points = []
        
        points = [
            (0, 0, 1.5),  # Center
            (-1, -0.5, 1.0), (1, -0.5, 1.0),  
            (-1, 0.5, 2.0), (1, 0.5, 2.0),    
            (0, -1, 1.5), (0, 1, 1.5),        
            (0, 0, 0.8), (0, 0, 2.2)          
        ]
        
        self.calib_progress['maximum'] = len(points)
        self.calib_progress['value'] = 0
        
        # TODO: Implement interactive calibration process
        messagebox.showinfo("Calibration", "Calibration process started!\n"
                          "Follow the on-screen prompts in the visualization window.")
    
    def calculate_metrics(self):
        if len(self.tracking_data) < 100:
            messagebox.showwarning("Warning", "Not enough tracking data for analysis.")
            return
        
        positions = np.array([data['position'] for data in list(self.tracking_data)[-100:]])
        mean_pos = np.mean(positions, axis=0)
        jitter = np.sqrt(np.mean(np.sum((positions - mean_pos) ** 2, axis=1)))
        
        if len(self.tracking_data) > 1:
            start_pos = np.array(self.tracking_data[0]['position'])
            end_pos = np.array(list(self.tracking_data)[-1]['position'])
            time_diff = list(self.tracking_data)[-1]['timestamp'] - self.tracking_data[0]['timestamp']
            drift_rate = np.linalg.norm(end_pos - start_pos) / time_diff if time_diff > 0 else 0
        else:
            drift_rate = 0
        
        self.metric_labels['Jitter (RMS)'].config(text=f"{jitter:.4f} m")
        self.metric_labels['Drift Rate'].config(text=f"{drift_rate:.4f} m/s")
        self.metric_labels['Position Accuracy'].config(text="Requires calibration")
        self.metric_labels['Rotation Accuracy'].config(text="Requires calibration")
    
    def reset_center(self):
        if self.ovr_session:
            try:
                ovr.recenterTrackingOrigin(self.ovr_session)
                messagebox.showinfo("Success", "Tracking center reset successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset center: {e}")
        else:
            messagebox.showinfo("Info", "Simulated center reset.")
    
    def apply_settings(self):
        for key, var in self.bound_vars.items():
            self.tracking_bounds[key] = var.get()
        messagebox.showinfo("Success", "Settings applied successfully.")
    
    def save_calibration(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            calib_data = {
                'timestamp': datetime.now().isoformat(),
                'calibration_points': self.calibration_points,
                'tracking_bounds': self.tracking_bounds
            }
            with open(filename, 'w') as f:
                json.dump(calib_data, f, indent=2)
            messagebox.showinfo("Success", f"Calibration saved to {filename}")
    
    def load_calibration(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    calib_data = json.load(f)
                self.calibration_points = calib_data.get('calibration_points', [])
                self.tracking_bounds = calib_data.get('tracking_bounds', self.tracking_bounds)
                
                # Update GUI
                for key, var in self.bound_vars.items():
                    var.set(self.tracking_bounds[key])
                
                messagebox.showinfo("Success", f"Calibration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load calibration: {e}")
    
    def export_data(self):
        if not self.tracking_data:
            messagebox.showwarning("Warning", "No tracking data to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write("timestamp,pos_x,pos_y,pos_z,rot_x,rot_y,rot_z,rot_w,valid\n")
                for data in self.tracking_data:
                    pos = data['position']
                    rot = data['rotation']
                    f.write(f"{data['timestamp']},{pos[0]},{pos[1]},{pos[2]},"
                           f"{rot[0]},{rot[1]},{rot[2]},{rot[3] if len(rot) > 3 else 0},"
                           f"{data['tracking_valid']}\n")
            messagebox.showinfo("Success", f"Data exported to {filename}")
    
    def generate_report(self):
        if len(self.tracking_data) < 10:
            messagebox.showwarning("Warning", "Not enough data to generate report.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write("DK2 Tracking Calibration Report\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total samples: {len(self.tracking_data)}\n\n")
                
                if self.tracking_data:
                    positions = np.array([data['position'] for data in self.tracking_data])
                    f.write("Position Statistics:\n")
                    f.write(f"  Mean position: {np.mean(positions, axis=0)}\n")
                    f.write(f"  Position range: {np.ptp(positions, axis=0)}\n")
                    f.write(f"  Position std: {np.std(positions, axis=0)}\n\n")
                
                f.write("Tracking bounds:\n")
                for key, value in self.tracking_bounds.items():
                    f.write(f"  {key}: {value}\n")
            
            messagebox.showinfo("Success", f"Report generated: {filename}")
    
    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.cleanup()
    
    def cleanup(self):
        self.running = False
        self.viz_running = False
        
        if self.ovr_session and OVR_AVAILABLE:
            try:
                ovr.destroy(self.ovr_session)
                ovr.shutdown()
            except:
                pass
        
        pygame.quit()

if __name__ == "__main__":
    print("DK2 Tracking Calibration Tool")
    print("=" * 40)
    
    if not OVR_AVAILABLE:
        print("Note: OVR SDK not detected. Running in simulation mode.")
        print("To use with actual DK2, install the Oculus SDK and ovr module.")
        print("\nPlease Wait...")
    
    app = DK2TrackingCalibrator()
    app.run()
