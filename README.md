# DK2 Positional Tracking Calibration Tool

A Python utility for testing and calibrating Oculus Rift DK2 positional tracking accuracy. (Even though it's outdated)

## Features

### 🎯 Real-time Monitoring
- Live tracking status display
- Position and rotation values in real-time
- Frame rate monitoring
- Connection status indicators

### 📊 3D Visualization
- Interactive pygame-based 3D visualization
- Real-time head position tracking
- Movement trail history
- Tracking boundary visualization
- Coordinate system display

### 🔧 Calibration System
- Interactive multi-point calibration process
- Progress tracking and visual feedback
- Save/load calibration configurations
- One-click tracking center reset

### 📈 Analysis Tools
- Position accuracy metrics
- Jitter measurement (RMS)
- Drift rate calculation
- Comprehensive tracking reports
- CSV data export for external analysis

### ⚙️ Settings Management
- Adjustable tracking bounds (X, Y, Z limits)
- Configurable parameters
- Settings persistence

## Installation

### Prerequisites
- Python 3.7 or higher
- Windows (for Oculus SDK support)

### Required Python Packages
```bash
pip install pygame numpy
```

### For Hardware Support (Optional)
To use with an actual DK2 headset:
1. Install the [Oculus SDK](https://developer.oculus.com/downloads/package/oculus-sdk-for-windows/)
2. Install Python OVR bindings:
```bash
pip install ovr
```

**Note:** The tool works in simulation mode without hardware, perfect for testing and development.

## Usage

### Quick Start
1. Clone the repository:
```bash
git clone https://github.com/CPScript/DK2-Positonal-Calibrator.git
cd DK2-Positonal-Calibrator
```

2. Run the tool:
```bash
python main.py.py
```

### Basic Workflow
1. **Start Tracking**: Click "Start Tracking" in the Real-time Monitor tab
2. **View Visualization**: The pygame window shows live 3D tracking data
3. **Calibrate**: Use the Calibration tab to run accuracy tests
4. **Analyze**: Check the Analysis tab for performance metrics
5. **Export**: Save tracking data and reports for further analysis

### Interface Overview

#### Real-time Monitor Tab
- **Status Indicators**: Connection, tracking status, and frame rate
- **Live Data**: Current position (X, Y, Z) and rotation values
- **Controls**: Start/stop tracking, reset center position

#### Calibration Tab
- **Interactive Calibration**: Step-by-step calibration process
- **Progress Tracking**: Visual progress bar and status updates
- **Data Management**: Save and load calibration profiles

#### Analysis Tab
- **Accuracy Metrics**: Position accuracy, rotation accuracy, jitter, drift
- **Data Export**: Export tracking data to CSV format
- **Report Generation**: Generate comprehensive tracking reports

#### Settings Tab
- **Tracking Bounds**: Configure X, Y, Z tracking limits
- **Parameter Adjustment**: Fine-tune tracking parameters

## Hardware Requirements

### Minimum Requirements
- **CPU**: Intel Core i5-4590 / AMD FX 8350 equivalent or better
- **Memory**: 4 GB RAM
- **Graphics**: NVIDIA GTX 970 / AMD R9 280 equivalent or better
- **USB**: USB 3.0 port
- **OS**: Windows 7 SP1 64-bit or newer

### Recommended Setup
- Oculus Rift DK2 headset
- Proper lighting conditions (avoid direct sunlight)
- Clear tracking area (2m x 1.5m minimum)
- Stable mounting for the tracking camera

## Configuration

The tool saves configuration data in JSON format:

```json
{
  "tracking_bounds": {
    "x_min": -2.0,
    "x_max": 2.0,
    "y_min": -1.5,
    "y_max": 1.5,
    "z_min": 0.5,
    "z_max": 3.0
  },
  "calibration_points": [...],
  "timestamp": "2025-01-01T12:00:00"
}
```

## Troubleshooting

### Common Issues

**"OVR SDK not found" Warning**
- This is normal if you don't have a DK2 connected
- The tool will run in simulation mode for testing

**Tracking Data Shows Zeros**
- Check USB 3.0 connection
- Ensure proper lighting conditions
- Verify DK2 camera is connected and recognized

**Poor Tracking Accuracy**
- Run the calibration process
- Check for reflective surfaces in the tracking area
- Ensure the camera has a clear view of the headset

**Performance Issues**
- Close unnecessary applications
- Check system requirements
- Reduce visualization quality in settings
