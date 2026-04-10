# Micro UAV Intelligent Wind Field Test and Evaluation System

## Project Structure

```
allin/
├── src/                          # Source code
│   ├── main.py                   # Main entry point
│   ├── config.py                 # Configuration
│   ├── requirements.txt          # Dependencies
│   │
│   ├── dashboard/                # Dashboard UI
│   │   ├── ui_main_window.py
│   │   ├── ui_docks.py
│   │   ├── ui_custom_widgets.py
│   │   ├── ui_chart_widget.py
│   │   ├── ui_motion_capture.py
│   │   ├── ui_sensor_collection.py
│   │   ├── ui_sensor_dock.py
│   │   ├── core_theme_manager.py
│   │   ├── core_data_simulator.py
│   │   └── debug.py
│   │
│   ├── modules/                  # Functional modules
│   │   ├── plc_monitoring/       # PLC monitoring
│   │   ├── motion_capture/       # Motion capture
│   │   ├── wind_field/           # Wind field related
│   │   ├── fan_control/          # Fan control
│   │   ├── hardware/             # Hardware control
│   │   └── core/                 # Core modules
│   │
│   ├── assets/                   # Assets
│   │   └── images/               # Images
│   │
│   └── tests/                    # Tests
│
├── data/                         # Data files
├── docs/                         # Documentation
├── see/                          # External modules (preserved)
├── sikao260410/                  # Project documentation (preserved)
├── startup.bat                   # Startup script
└── README.md                     # This file
```

## Installation

1. Install Python 3.11+ (recommended using Anaconda)
2. Install dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```

## Usage

### Method 1: Using startup script
   ```bash
   startup.bat
   ```

### Method 2: Command line
   ```bash
   cd src
   python main.py
   ```

## Dependencies

- PySide6: Qt6 for Python
- python-snap7: Siemens S7 PLC communication
- redis: Real-time data storage
- pymongo: MongoDB integration
- pandas: Data processing
- openpyxl: Excel file support
- numpy: Numerical computing
- matplotlib: Plotting

## Modules

### Dashboard
Main UI providing system monitoring, communication, environment display, motion capture, and fan control interfaces.

### PLC Monitoring
- Encoder monitoring with real-time plotting
- Point table monitoring from CSV/Excel
- Batch data reading optimized by DB blocks

### Motion Capture
Camera integration for motion tracking and analysis.

### Wind Field
- **Editor**: Wind field editing tools
- **Settings**: Wind field configuration
- **Preprocessing**: CFD preprocessing module

### Fan Control
Control and monitoring of the 40x40 fan array (1600 fans).

### Hardware
Integration with various hardware controllers (Modbus, EtherCAT, etc.).

## License

© 2026 Micro UAV Intelligent Wind Field Test and Evaluation System
