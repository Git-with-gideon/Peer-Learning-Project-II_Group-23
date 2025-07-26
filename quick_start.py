# OptiGrade Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Setup (One-time)
```bash
# Create and activate virtual environment
python3 -m venv optigrade_env
source optigrade_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python setup.py
```
### 2. Run the Application
```bash
# Activate virtual environment (if not already active)
source optigrade_env/bin/activate

# Start the enhanced application
python OptiGrade_Enhanced.py
```
### 3. Basic Usage Flow
1. **Select "1. Start New Grading Session"**
2. **Enter assignment details:**
   - Assignment name (e.g., "Math Quiz 1")
   - Number of questions
   - Correct answers (A-E) for each question
3. **Choose camera source:**
   - Local webcam (option 1)
   - IP camera from mobile device (option 2)
4. **Capture OMR sheet:**
   - Position sheet in camera view
   - Press 's' to capture
5. **Enter student information:**
   - Student name and ID
6. **View results:**
   - Score and detailed breakdown
   - Results automatically saved to database