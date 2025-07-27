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
- **SQLite Database**: Efficient local database storage with a proper schema design
- **Assignment Management**: Store and manage multiple assignments with answer keys
- **Student Records**: Track individual student performance across assignments.
- **Detailed Analytics**: Question-by-question analysis and performance statistics.
- **Data Export**: Export results to CSV format for external analysis.
- **Image Archiving**: Automatically save graded OMR sheets with results overlay

### Advanced Features
- **Statistics Dashboard**: View assignment statistics including grade distributions
- **Student Performance Tracking**: Monitor individual student progress over time.
- **Error Handling**: Robust error validation and user feedback.
- **Modular Architecture**: Well-organized, maintainable code structure.

## Installation

### Prerequisites
- Python 3.7 or higher
- Webcam or mobile device with IP camera app

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Git-with-gideon/Peer-Learning-Project-II_Group-23
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
   python OptiGrade.py
   ```
. **More Info**
   ```bash
   Go Through the QUICK_START.md
   ```
## Usage Guide

### Starting a Grading Session

1. **Launch the application**
   - Run `python OptiGrade.py`
   - Select "1. Start New Grading Session"

2. **Setup Assignment**
   - Enter assignment name
   - Specify number of questions
   - Select the option style (4) for four options (A, B, C, D) and (5) for five options (A, B, C, D, E).
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

## Database Schema

### Tables Structure

#### assignments
- `id`: Primary key
- `assignment_name`: Name of the assignment
- `num_questions`: Total number of questions
- `answer_key`: JSON string of correct answers
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update

#### grading_sessions
- `id`: Primary key
- `assignment_id`: Foreign key to assignments
- `student_name`: Name of the student
- `student_id`: Unique student identifier
- `score`: Percentage score achieved
- `correct_answers`: Number of correct answers
- `total_questions`: Total questions in assignment
- `image_path`: Path to saved OMR result image
- `processed_at`: Timestamp of grading

#### detailed_results
- `id`: Primary key
- `session_id`: Foreign key to grading_sessions
- `question_number`: Question number (1-based)
- `correct_answer`: Correct answer (A-E)
- `student_answer`: Student's selected answer
- `is_correct`: Boolean indicating if answer was correct

## File Structure

```
Peer-Learning-Project-II_Group-23/
├── database_manager.py         # Database operations
├── database_setup.py           # Database initialization
├── database_viewer.py          # Database exploration tool
├── setup.py                    # Complete setup script
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive documentation
├── data/                       # Database storage
│   └── optigrade.db            # SQLite database
├── optigrade_env/              # Python virtual environment
└── images/                     # Archived OMR result images
    └── omr_result_*.jpg        # Graded OMR sheets with results
```

## Technical Implementation

### Computer Vision Pipeline
1. **Image Capture**: Real-time camera feed with manual capture trigger
2. **Preprocessing**: Grayscale conversion, Gaussian blur, Canny edge detection
3. **Document Detection**: Contour detection and perspective transformation
4. **Bubble Detection**: Contour analysis to identify answer bubbles
5. **Answer Recognition**: Pixel density analysis to determine marked answers
6. **Grading**: Comparison with answer key and score calculation

### Database Design Principles
- **Normalization**: Proper table relationships and data integrity
- **Indexing**: Optimized queries with strategic indexes
- **Error Handling**: Comprehensive exception handling and validation
- **Data Validation**: Input sanitization and constraint enforcement

### Security Features
- **Input Validation**: All user inputs are validated and sanitized
- **Error Handling**: Graceful error handling with user-friendly messages
- **Data Integrity**: Foreign key constraints and transaction management

## Performance Optimization

### Database Optimizations
- **Indexed Queries**: Strategic indexes on frequently queried columns
- **Connection Pooling**: Efficient database connection management
- **Batch Operations**: Optimized bulk data operations

### Image Processing Optimizations
- **Contour Filtering**: Efficient bubble detection algorithms
- **Memory Management**: Proper image cleanup and resource management
- **Real-time Processing**: Optimized for live camera feed processing

## Troubleshooting

### Common Issues

1. **Camera Not Opening**
   - Ensure webcam is connected and not in use by other applications
   - Check camera permissions in system settings

2. **OMR Sheet Not Detected**
   - Ensure good lighting conditions
   - Check that OMR sheet is flat and well-positioned
   - Verify sheet has clear, dark borders

3. **Database Errors**
   - Ensure database directory has write permissions
   - Run `python database_setup.py` to reinitialize database

4. **Bubble Detection Issues**
   - Use the debug option to view thresholded image
   - Adjust lighting or camera position
   - Ensure bubbles are clearly marked

### Debug Features
- **Threshold Image Display**: View processed image for troubleshooting
- **Detailed Error Messages**: Comprehensive error reporting
- **Database Logging**: Track database operations for debugging

### Contributors
-   **Queen Ruth Uwera** 
-   **Megane Keza Mwizerwa** 
-   **Micheal Okinyi Odhiambo** 
-   **Olowoyo Erioluwa Gideon** 
-   **Tumba || Zikoranachukwudi Micheal Kongolo**

### Development Guidelines
- Follow PEP 8 coding standards
- Add comprehensive error handling
- Include docstrings for all functions
- Test thoroughly before committing

### Code Structure
- Modular design with clear separation of concerns
- Database operations isolated in dedicated manager class
- Configuration management for easy customization

## License

This project is developed for educational purposes as part of the Peer Learning Project II.

## Contact

For questions or support, please refer to the project documentation or contact the development team.

---

**Note**: This enhanced version of OptiGrade provides comprehensive database integration and archiving capabilities, meeting the requirements for efficient database implementation, well-designed schema, and optimized database interactions as specified in the project rubric.