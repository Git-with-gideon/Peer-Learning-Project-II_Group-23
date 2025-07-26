# OptiGrade - OMR Sheet Grading System with Database Integration

## Project Overview

OptiGrade is an intelligent Optical Mark Recognition (OMR) sheet grading system that automatically grades multiple-choice answer sheets using computer vision and stores results in a comprehensive database for archiving and analysis.

## Features

### Core Functionality
- **Automatic OMR Detection**: Uses computer vision to detect and process OMR sheets
- **Real-time Camera Integration**: Supports both local webcam and IP camera (mobile device)
- **Intelligent Answer Recognition**: Automatically detects marked bubbles and grades answers
- **Visual Feedback**: Shows grading results with color-coded correct/incorrect answers

### Database Integration & Archiving
- **SQLite Database**: Efficient local database storage with proper schema design
- **Assignment Management**: Store and manage multiple assignments with answer keys
- **Student Records**: Track individual student performance across assignments
- **Detailed Analytics**: Question-by-question analysis and performance statistics
- **Data Export**: Export results to CSV format for external analysis
- **Image Archiving**: Automatically save graded OMR sheets with results overlay

### Advanced Features
- **Statistics Dashboard**: View assignment statistics including grade distributions
- **Student Performance Tracking**: Monitor individual student progress over time
- **Error Handling**: Robust error validation and user feedback
- **Modular Architecture**: Well-organized, maintainable code structure

## Installation

### Prerequisites
- Python 3.7 or higher
- Webcam or mobile device with IP camera app

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Peer-Learning-Project-II_Group-23
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python database_setup.py
   ```

4. **Run the application**
   ```bash
   python OptiGrade_Enhanced.py
   ```

## Usage Guide

### Starting a Grading Session

1. **Launch the application**
   - Run `python OptiGrade_Enhanced.py`
   - Select "1. Start New Grading Session"

2. **Setup Assignment**
   - Enter assignment name
   - Specify number of questions
   - Input correct answers (A-E) for each question

3. **Configure Camera**
   - Choose between local webcam or IP camera
   - For mobile device: Install IP camera app and enter stream URL

4. **Capture OMR Sheet**
   - Position OMR sheet in camera view
   - Press 's' to capture when ready
   - Press 'q' to quit

5. **Enter Student Information**
   - Provide student name and ID
   - Results will be automatically saved to database

### Database Features

#### Viewing Statistics
- Select "2. View Assignment Statistics" from main menu
- View comprehensive statistics including:
  - Total sessions graded
  - Average, minimum, and maximum scores
  - Grade distribution (A, B, C, D, E)

#### Exporting Results
- Select "3. Export Results to CSV" from main menu
- Results are exported with timestamp for easy identification

#### Student Performance Tracking
- Select "4. View Student Results" from main menu
- Enter student ID to view all their graded assignments
