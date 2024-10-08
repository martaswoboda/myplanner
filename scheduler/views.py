from django.shortcuts import render, redirect, get_object_or_404
from .forms import JobForm
from .models import Job
from datetime import datetime, timedelta, time, date
from decimal import Decimal


# Constants for working hours and blocked times
START_TIME = time(7, 0)          # 7:00 AM
END_TIME = time(16, 0)           # 4:00 PM
BLOCKED_TIME_START = time(12, 0) # 12:00 PM
BLOCKED_TIME_END = time(13, 0)   # 1:00 PM
MAX_DAYS = 30                    # Maximum number of days to look ahead for scheduling

def job_list(request):
    # Fetch only unscheduled jobs (where both date and start_time are null)
    jobs = Job.objects.filter(date__isnull=True, start_time__isnull=True).order_by('title')
    context = {
        'jobs': jobs,
    }
    return render(request, 'scheduler/job_list.html', context)


def get_week_dates(current_date):
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

# Weekly plan view (index.html shows one week)
def weekly_plan_view(request):
    week_offset = int(request.GET.get('week', 0))  # Get the week offset for navigating
    current_date = datetime.now().date()
    start_of_week, end_of_week = get_week_dates(current_date + timedelta(weeks=week_offset))
    
    # Filter jobs for this week and order by date and start_time
    jobs = Job.objects.filter(date__range=[start_of_week, end_of_week]).order_by('date', 'start_time')
    
    context = {
        'jobs': jobs,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'week_offset': week_offset,
    }
    return render(request, 'scheduler/index.html', context)

def today_view(request):
    current_time = datetime.now().time()  # Get the current time
    today_jobs = Job.objects.filter(date=date.today()).order_by('start_time')

    for job in today_jobs:
        # If the job's end time has passed and it's not completed, mark it as unscheduled
        if job.end_time and job.end_time < current_time and not job.completed:
            job.start_time = None
            job.end_time = None
            job.date = None
            job.save()

        # Add attributes to determine if the job is overdue or close to overdue
        if job.end_time and job.end_time < current_time and not job.completed:
            job.is_overdue = True
        elif job.end_time and (datetime.combine(date.today(), job.end_time) - datetime.now()).total_seconds() < 3600 and not job.completed:
            job.is_close_to_overdue = True
        else:
            job.is_overdue = False
            job.is_close_to_overdue = False

    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        job = Job.objects.get(id=job_id)
        job.completed = True
        job.save()
        return redirect('today')

    context = {
        'jobs': today_jobs,
        'today': date.today(),
        'current_time': current_time,
    }
    return render(request, 'scheduler/today.html', context)

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
    
    # Combine jobs by priority
    return a_jobs + b_jobs + c_jobs

def divide_task(job):
    chunks = []
    # Convert duration_hours to Decimal
    duration_hours = Decimal(str(job.duration_hours))
    # Check if job can be divided and duration is greater than 1 hour
    if job.can_be_divided and duration_hours > Decimal('1'):
        hours_remaining = duration_hours
        # Loop until all hours are allocated
        while hours_remaining > Decimal('0'):
            # Allocate chunks of 1 hour or the remaining time if less than 1 hour
            task_duration = min(Decimal('1'), hours_remaining)
            chunks.append({
                'title': job.title,
                'urgency': job.urgency,
                'importance': job.importance,
                'duration': task_duration,  # This is a Decimal
                'is_frog': job.is_frog,
                'can_be_divided': job.can_be_divided
            })
            # Subtract allocated time from hours_remaining
            hours_remaining -= task_duration
        return chunks
    else:
        # If job cannot be divided, return it as a single task
        return [{
            'title': job.title,
            'urgency': job.urgency,
            'importance': job.importance,
            'duration': Decimal(str(job.duration_hours)),
            'is_frog': job.is_frog,
            'can_be_divided': job.can_be_divided
        }]
    
def get_available_time_slots(day, scheduled_intervals):
    from datetime import datetime, timedelta

    # Define the working day start and end datetime
    day_start = datetime.combine(day, START_TIME)
    day_end = datetime.combine(day, END_TIME)

    # Start with the full working day as an available slot
    available_slots = [(day_start, day_end)]

    # Include blocked times (e.g., lunch break)
    blocked_start = datetime.combine(day, BLOCKED_TIME_START)
    blocked_end = datetime.combine(day, BLOCKED_TIME_END)

    # Add blocked time to scheduled intervals
    all_scheduled = scheduled_intervals + [(blocked_start, blocked_end)]

    # Sort all scheduled intervals
    all_scheduled.sort(key=lambda x: x[0])

    # Subtract scheduled intervals from available slots
    for scheduled_start, scheduled_end in all_scheduled:
        temp_slots = []
        for slot_start, slot_end in available_slots:
            # No overlap
            if scheduled_end <= slot_start or scheduled_start >= slot_end:
                temp_slots.append((slot_start, slot_end))
            else:
                # Before scheduled interval
                if scheduled_start > slot_start:
                    temp_slots.append((slot_start, scheduled_start))
                # After scheduled interval
                if scheduled_end < slot_end:
                    temp_slots.append((scheduled_end, slot_end))
        available_slots = temp_slots

    return available_slots

# Main function to schedule jobs
def schedule_jobs(jobs):
    current_datetime = datetime.now()
    current_day = current_datetime.date()

    # Sort the jobs by priority (A -> B -> C)
    prioritized_jobs = prioritize_jobs(jobs)

    # Collect existing scheduled jobs (excluding the jobs we're about to schedule)
    existing_jobs = Job.objects.filter(date__gte=current_day).exclude(id__in=[job.id for job in jobs])
    scheduled_times = {}

    for job in existing_jobs:
        day = job.date
        if day not in scheduled_times:
            scheduled_times[day] = []
        scheduled_times[day].append((datetime.combine(day, job.start_time), datetime.combine(day, job.end_time)))

    # Store days where frogs have been scheduled
    frog_scheduled_days = set()

    # Track titles of jobs that are divided
    divided_task_titles = {}

    for job in prioritized_jobs:
        # If the job is already scheduled, skip it
        if job.start_time and job.date:
            continue  # Skip this job, it's already manually scheduled

        # First divide the job if necessary
        divided_jobs = divide_task(job)

        # If the job is not divided (single task), we can try to schedule it and update the original job
        if len(divided_jobs) == 1:
            task = divided_jobs[0]
            scheduled = False
            for day_offset in range(MAX_DAYS):
                day = current_day + timedelta(days=day_offset)

                # Skip if day is in the past
                if day < current_day:
                    continue

                if is_time_available(day):
                    # Check if a 'frog' task has already been scheduled for that day
                    if task['is_frog'] and day in frog_scheduled_days:
                        continue  # Skip day if a frog is already scheduled

                    # Build a list of available time slots for the day
                    available_slots = get_available_time_slots(day, scheduled_times.get(day, []))

                    # Try to find a slot for the task
                    for slot_start, slot_end in available_slots:
                        # Adjust slot_start if it's before current time (avoid scheduling in the past)
                        if day == current_day and slot_start < current_datetime:
                            slot_start = current_datetime

                        task_duration = timedelta(hours=float(task['duration']))
                        potential_end = slot_start + task_duration

                        # Check if the slot is big enough for the task
                        if potential_end <= slot_end:
                            # Schedule the task by updating the original job
                            job.start_time = slot_start.time()
                            job.date = slot_start.date()
                            job.end_time = potential_end.time()
                            job.save()

                            # Update scheduled_times
                            if day not in scheduled_times:
                                scheduled_times[day] = []
                            scheduled_times[day].append((slot_start, potential_end))

                            # Sort the scheduled times for the day
                            scheduled_times[day].sort(key=lambda x: x[0])

                            scheduled = True

                            # Mark the day as having a frog if the task is a frog
                            if task['is_frog']:
                                frog_scheduled_days.add(day)

                            break  # Exit the slot loop

                    if scheduled:
                        break  # Exit the day loop

            # If we couldn't schedule the job, it remains unscheduled

        else:
            # The job was divided into multiple chunks
            scheduled_any_chunk = False
            for task in divided_jobs:
                scheduled = False
                for day_offset in range(MAX_DAYS):
                    day = current_day + timedelta(days=day_offset)

                    # Skip if day is in the past
                    if day < current_day:
                        continue

                    # Ensure tasks with the same title are not scheduled on the same day
                    if task['title'] in divided_task_titles and day in divided_task_titles[task['title']]:
                        continue

                    if is_time_available(day):
                        # Check if a 'frog' task has already been scheduled for that day
                        if task['is_frog'] and day in frog_scheduled_days:
                            continue  # Skip day if a frog is already scheduled

                        # Build a list of available time slots for the day
                        available_slots = get_available_time_slots(day, scheduled_times.get(day, []))

                        # Try to find a slot for the task
                        for slot_start, slot_end in available_slots:
                            # Adjust slot_start if it's before current time (avoid scheduling in the past)
                            if day == current_day and slot_start < current_datetime:
                                slot_start = current_datetime

                            task_duration = timedelta(hours=float(task['duration']))
                            potential_end = slot_start + task_duration

                            # Check if the slot is big enough for the task
                            if potential_end <= slot_end:
                                # Schedule the task by creating a new job instance
                                job_instance = Job(
                                    title=task['title'],
                                    urgency=task['urgency'],
                                    importance=task['importance'],
                                    start_time=slot_start.time(),
                                    date=slot_start.date(),
                                    end_time=potential_end.time(),
                                    duration_hours=task['duration'],
                                    is_frog=task['is_frog'],
                                    can_be_divided=task['can_be_divided']
                                )
                                job_instance.save()

                                # Update scheduled_times
                                if day not in scheduled_times:
                                    scheduled_times[day] = []
                                scheduled_times[day].append((slot_start, potential_end))

                                # Sort the scheduled times for the day
                                scheduled_times[day].sort(key=lambda x: x[0])

                                scheduled = True
                                scheduled_any_chunk = True

                                # Mark the day as having a frog if the task is a frog
                                if task['is_frog']:
                                    frog_scheduled_days.add(day)

                                # Track the task title and the day it was scheduled
                                if task['title'] not in divided_task_titles:
                                    divided_task_titles[task['title']] = set()
                                divided_task_titles[task['title']].add(day)

                                break  # Exit the slot loop

                        if scheduled:
                            break  # Exit the day loop

            # After scheduling all chunks, delete the original job
            if scheduled_any_chunk:
                job.delete()
            else:
                # Could not schedule any chunk; job remains unscheduled
                pass

# View function to schedule all unscheduled jobs
def schedule_all_jobs(request):
    if request.method == 'POST':
        # Fetch only unscheduled jobs
        unscheduled_jobs = Job.objects.filter(date__isnull=True, start_time__isnull=True)
        schedule_jobs(unscheduled_jobs)
        return redirect('job_list')
    else:
        return redirect('job_list')

def schedule_single_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        # Schedule this single job using the existing scheduling logic
        schedule_jobs([job])
        return redirect('job_list')
    
    return redirect('job_list')


def add_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            duration_hours = form.cleaned_data.get('duration_hours', Decimal('0.25'))

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
            duration_hours = form.cleaned_data.get('duration_hours', Decimal('0.25'))

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
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        job.start_time = None
        job.end_time = None
        job.date = None  # Reset the time and date
        job.save()
        return redirect('job_list')
    else:
        return redirect('job_list')

def reset_jobs(request):
    if request.method == 'POST':
<<<<<<< HEAD
        # Reset start_time, end_time, and date for all jobs
        Job.objects.all().update(start_time=None, end_time=None, date=None)
        return redirect('job_list')
    else:
        return redirect('job_list')
=======
        # Perform the actual reset
        Job.objects.all().update(start_time=None, end_time=None, date=None)
        return redirect('job_list')
    else:
        # Show the confirmation page
        return render(request, 'scheduler/reset_all.html')
# views.py

def reset_jobs_confirm(request):
    if request.method == 'POST':
        return redirect('reset_jobs')  # Redirect to the actual reset view after confirmation

    return render(request, 'scheduler/reset_all.html')  # Renders the reset confirmation page
>>>>>>> e685cf0 (Added reset jobs confirmation and updated templates for reset logic)

def complete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        # Mark the job as completed
        job.completed = True
        job.save()
        return redirect('today')
    return redirect('today')

