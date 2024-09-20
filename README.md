# myplanner

This is a **Job Scheduler** project that allows users to create, edit, schedule, and manage jobs (tasks) within a given time frame. It is built using Django and features scheduling logic to handle both scheduled and unscheduled jobs.

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
