## Task Prioritization
The Job Scheduler prioritizes tasks using the following methods to ensure optimal efficiency and time management:

1. **"Eat the Frog" Method**
The concept of "Eating the Frog" refers to tackling your most difficult or important task first thing in the morning. In this scheduler:

- Frog tasks are identified as critical, high-priority jobs that should be completed before anything else.
- These tasks are scheduled at the earliest available time in the morning (starting at 7:00 AM).

2. **Managing by Urgency and Importance (ABC Method)**
The scheduler uses the ABC Method to prioritize tasks based on their urgency and importance:
A-priority tasks: High urgency and high importance. These tasks are crucial and must be done as soon as possible. They are scheduled earlier in the day after frog tasks.
B-priority tasks: Either urgent or important, but not both. These tasks are necessary but can be scheduled after the A-priority tasks.
C-priority tasks: Neither urgent nor important. These tasks are the least critical and are scheduled later in the day or after other tasks are completed.

## Features

- **Add Jobs**: Create new jobs with specific details like start time, duration, urgency, and importance.
- **Edit Jobs**: Modify existing jobs to update their details or reschedule them.
- **Unscheduled Jobs**: View and manage jobs that haven't been scheduled yet.
- **Job Scheduling**: Automatically schedule jobs based on priority (ABC method), importance, and time availability.
- **Responsive Design**: The interface adjusts to different screen sizes for an optimal user experience.


## Installation

### Prerequisites

- Python 3.8+
- Django 3.2+
- Git

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/martaswoboda/myplanner.git

2. **Navigate to the project directory**:
cd myplanner

3. **Create a virtual environment**:
python -m venv venv

4. **Activate the virtual environment**:
On Windows:

myenv\Scripts\activate

5. **Install dependencies**:

pip install -r requirements.txt

6. **Apply migrations to set up the database**:

python manage.py migrate


7. **Run the development server**:
python manage.py runserver

Access the application by navigating to the website provided in Terminal
