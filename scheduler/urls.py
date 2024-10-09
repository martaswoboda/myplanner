from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),  # job_list as the first page
    path('weekly-view/', views.weekly_plan_view, name='weekly_plan_view'),  # for the weekly view
    path('today/', views.today_view, name='today'),
    path('add-job/', views.add_job, name='add_job'),
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'),
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('schedule-all/', views.schedule_all_jobs, name='schedule_all_jobs'),
    path('schedule-job/<int:job_id>/', views.schedule_single_job, name='schedule_single_job'),
    path('reset-job/<int:job_id>/', views.reset_job, name='reset_job'),
    path('reset-jobs/', views.reset_jobs, name='reset_jobs'),
    path('complete-job/<int:job_id>/', views.complete_job, name='complete_job'),
    path('reset_jobs_confirm/', views.reset_jobs_confirm, name='reset_jobs_confirm'),


]
