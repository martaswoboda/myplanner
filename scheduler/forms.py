from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    unspecific_time = forms.BooleanField(required=False, label="Schedule unspecific time?", initial=False)
    duration_hours = forms.DecimalField(min_value=0.25, max_value=16, label="Duration (Hours)", initial=1)

    class Meta:
        model = Job
        fields = ['title', 'description', 'start_time', 'date', 'due_date', 'is_frog', 'urgency', 'importance', 'can_be_divided', 'duration_hours']
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'placeholder': 'HH:MM'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),  
        }

    def clean(self):
        cleaned_data = super().clean()
        unspecific_time = cleaned_data.get('unspecific_time')

        if not unspecific_time:
            if not cleaned_data.get('start_time'):
                self.add_error('start_time', "Please provide a start time.")
            if not cleaned_data.get('date'):
                self.add_error('date', "Please provide a date.")
        return cleaned_data
