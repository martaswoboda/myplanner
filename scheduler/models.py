from django.db import models

class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)  # New field for due date
    is_frog = models.BooleanField(default=False)
    urgency = models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')], default=2)
    importance = models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')], default=2)
    can_be_divided = models.BooleanField(default=False)
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2, default=1)

    def __str__(self):
        return self.title

    def calculate_priority(self):
        # ABC method based on urgency and importance
        if self.urgency == 3 and self.importance == 3:
            return 'A'  # Highest priority
        elif self.urgency == 3 or self.importance == 3:
            return 'B'  # Medium priority
        else:
            return 'C'  # Lowest priority
