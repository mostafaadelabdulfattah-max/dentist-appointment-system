from django.contrib import admin
from .models import Specialty, Dentist, DentistSchedule


class DentistScheduleInline(admin.TabularInline):
    """Lets an admin edit a dentist's weekly schedule right on the Dentist page."""
    model = DentistSchedule
    extra = 1


@admin.register(Dentist)
class DentistAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'specialty', 'phone_number')
    inlines = [DentistScheduleInline]


admin.site.register(Specialty)
