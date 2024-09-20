from django.shortcuts import render, redirect, get_object_or_404
from .forms import JobForm
from .models import Job
from datetime import datetime, timedelta, time, date

# Define constants for working hours
START_TIME = time(7, 0)
END_TIME = time(21, 0)
BLOCKED_TIME_START = time(16, 0)
BLOCKED_TIME_END = time(19, 0)
MAX_DAYS = 7 # Define max number of days ahead to schedule

def index(request):
    return job_list(request)

def get_week_dates(current_date):
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

# Weekly plan view (index.html shows one week)
def weekly_plan_view(request):
    week_offset = int(request.GET.get('week', 0))  # Get the week offset for navigating
    current_date = datetime.now().date()
    start_of_week, end_of_week = get_week_dates(current_date + timedelta(weeks=week_offset))
    
    # Filter jobs for this week
    jobs = Job.objects.filter(date__range=[start_of_week, end_of_week]).order_by('date', 'start_time')
    
    context = {
        'jobs': jobs,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'week_offset': week_offset,
    }
    return render(request, 'scheduler/index.html', context)


def today_view(request):
    today_jobs = Job.objects.filter(date=date.today())  # Use date.today() correctly
    context = {'jobs': today_jobs, 'today': date.today()}
    return render(request, 'scheduler/today.html', context)
# Helper function to block weekends and Jasmine's time


def is_time_available(day):
    # Block weekends
    if day.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
    return True

# Function to prioritize jobs by urgency and importance
def prioritize_jobs(jobs):
    # ABC Priority Method: A -> High Importance and Urgency, B -> Medium, C -> Low
    a_jobs, b_jobs, c_jobs = [], [], []
    
    for job in jobs:
        if job.calculate_priority() == 'A':
            a_jobs.append(job)
        elif job.calculate_priority() == 'B':
            b_jobs.append(job)
        else:
            c_jobs.append(job)
    
    # Combine jobs by priority: Frogs should be done first each day
    return a_jobs + b_jobs + c_jobs

def divide_task(job):
    chunks = []
    if job.can_be_divided and float(job.duration_hours) > 1:
        hours_remaining = float(job.duration_hours)
        while hours_remaining > 0:
            task_duration = min(1, hours_remaining)  # Divide into 1-hour chunks
            chunks.append({
                'title': job.title,
                'urgency': job.urgency,
                'importance': job.importance,
                'duration': task_duration,
                'is_frog': job.is_frog,
                'can_be_divided': job.can_be_divided
            })
            hours_remaining -= task_duration
        return chunks
    else:
        # Return the whole job if it cannot be divided
        return [{
            'title': job.title,
            'urgency': job.urgency,
            'importance': job.importance,
            'duration': float(job.duration_hours),
            'is_frog': job.is_frog,
            'can_be_divided': job.can_be_divided
        }]

# Main function to schedule jobs
def schedule_jobs(jobs):
    current_day = datetime.now().date()
    
    # Sort the jobs by priority (A -> B -> C)
    prioritized_jobs = prioritize_jobs(jobs)

    # Track last_end_time for each day
    last_end_times = {}
    
    # Store days where frogs have been scheduled
    frog_scheduled_days = set()

    # Track titles of jobs that are divided
    divided_task_titles = {}

    for job in prioritized_jobs:
        # First divide the job if necessary
        divided_jobs = divide_task(job)

        for task in divided_jobs:
            scheduled = False
            for day_offset in range(MAX_DAYS):
                day = current_day + timedelta(days=day_offset)

                # Ensure tasks with the same title are not scheduled on the same day
                if task['title'] in divided_task_titles and day in divided_task_titles[task['title']]:
                    continue

                if is_time_available(day):
                    # Check if frog has already been scheduled for that day
                    if task['is_frog'] and day in frog_scheduled_days:
                        continue  # Skip day if frog is already scheduled

                    # Get the last end time for the day, or start at 7:00 AM
                    last_end_time = last_end_times.get(day, START_TIME)

                    # Ensure task does not start during blocked hours
                    if BLOCKED_TIME_START <= last_end_time <= BLOCKED_TIME_END:
                        last_end_time = BLOCKED_TIME_END

                    # Calculate the end time for the task
                    end_time = (datetime.combine(day, last_end_time) + timedelta(hours=task['duration'])).time()

                    # Check if the task fits within working hours
                    if end_time <= END_TIME:
                        # Create and save the scheduled task
                        job_instance = Job(
                            title=task['title'],
                            urgency=task['urgency'],
                            importance=task['importance'],
                            start_time=last_end_time,
                            date=day,
                            end_time=end_time,
                            duration_hours=task['duration'],
                            is_frog=task['is_frog'],
                            can_be_divided=task['can_be_divided']
                        )
                        job_instance.save()

                        # Update last_end_time for this day
                        last_end_times[day] = end_time
                        scheduled = True

                        # Mark the day as having a frog if the task is a frog
                        if task['is_frog']:
                            frog_scheduled_days.add(day)

                        # Track the task title and the day it was scheduled
                        if task['title'] not in divided_task_titles:
                            divided_task_titles[task['title']] = set()
                        divided_task_titles[task['title']].add(day)

                        break  # Move to the next task once scheduled

            # Delete the original job if divided into smaller chunks
            if task != job:
                job.delete()



# View function to schedule all unscheduled jobs
def schedule_all_jobs(request):
    if request.method == 'POST':
        unscheduled_jobs = Job.objects.filter(start_time__isnull=True)
        schedule_jobs(unscheduled_jobs)
        return redirect('job_list')
    else:
        return redirect('job_list')

def job_list(request):
    # Sort jobs by start_time, with null values (unscheduled jobs) coming last
    jobs = Job.objects.all().order_by('date', 'start_time')
    for job in jobs:
        job.priority = job.calculate_priority()  # Calculate the priority dynamically
    return render(request, 'scheduler/index.html', {'jobs': jobs})



def add_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            duration_hours = form.cleaned_data.get('duration_hours', 0.25)

            if not form.cleaned_data.get('unspecific_time'):
                start_datetime = datetime.combine(job.date, job.start_time)
                end_datetime = start_datetime + timedelta(hours=float(duration_hours))
                job.end_time = end_datetime.time()

            job.save()
            return redirect('job_list')
    else:
        form = JobForm()

    return render(request, 'scheduler/add_job.html', {'form': form})

def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            duration_hours = form.cleaned_data.get('duration_hours', 0.25)

            if not form.cleaned_data.get('unspecific_time'):
                start_datetime = datetime.combine(job.date, job.start_time)
                end_datetime = start_datetime + timedelta(hours=float(duration_hours))
                job.end_time = end_datetime.time()

            job.save()
            return redirect('job_list')
    else:
        form = JobForm(instance=job)

    return render(request, 'scheduler/edit_job.html', {'form': form, 'job': job})

def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        job.delete()
        return redirect('job_list')

    return render(request, 'scheduler/delete_job.html', {'job': job})

def reset_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)  # Get the job using the ID passed in the URL
    if request.method == 'POST':
        job.start_time = None
        job.end_time = None
        job.date = None  # Reset the time and date
        job.save()
        return redirect('job_list')  # Redirect back to job list
    else:
        return redirect('job_list')

    
def reset_jobs(request):
    if request.method == 'POST':
        # Reset start_time, end_time, and date for all jobs
        Job.objects.all().update(start_time=None, end_time=None, date=None)
        return redirect('job_list')
    else:
        return redirect('job_list')
