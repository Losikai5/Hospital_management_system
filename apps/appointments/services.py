from django.utils import timezone
from .models import Appointment, AppointmentStatus
from apps.doctors.models import DoctorSchedule


def get_available_slots(doctor, date):
    """Get all available time slots for a doctor on a given date"""
    day_of_week = date.weekday()
    
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor,
        day_of_week=day_of_week,
        is_available=True
    ).first()

    if not schedule:
        return []

    slots = []
    from datetime import datetime, timedelta

    current_time = datetime.combine(date, schedule.start_time)
    end_time = datetime.combine(date, schedule.end_time)
    duration = timedelta(minutes=schedule.session_duration)

    while current_time + duration <= end_time:
        slot_time = current_time.time()

        is_booked = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            appointment_time=slot_time,
            status__in=[
                AppointmentStatus.PENDING,
                AppointmentStatus.CONFIRMED
            ]
        ).exists()

        if not is_booked:
            slots.append(slot_time)

        current_time += duration

    return slots


def book_appointment(patient, doctor, appointment_date, appointment_time, reason=None):
    """Book an appointment with full validation"""

    # Gate 1 - does doctor work on this day?
    day_of_week = appointment_date.weekday()
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor,
        day_of_week=day_of_week,
        is_available=True
    ).first()

    if not schedule:
        raise ValueError(
            f"Doctor is not available on {appointment_date.strftime('%A')}"
        )

    # Gate 2 - is the time within working hours?
    if not (schedule.start_time <= appointment_time <= schedule.end_time):
        raise ValueError(
            f"Appointment time must be between "
            f"{schedule.start_time} and {schedule.end_time}"
        )

    # Gate 3 - is the slot already taken?
    conflict = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status__in=[
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED
        ]
    ).exists()

    if conflict:
        raise ValueError("This time slot is already booked")

    # Gate 4 - all clear, create the appointment
    appointment = Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status=AppointmentStatus.PENDING,
        reason=reason
    )

    return appointment


def cancel_appointment(appointment, cancelled_by):
    """Cancel an appointment"""
    if appointment.status == AppointmentStatus.COMPLETED:
        raise ValueError("Cannot cancel a completed appointment")

    if appointment.status == AppointmentStatus.CANCELLED:
        raise ValueError("Appointment is already cancelled")

    appointment.status = AppointmentStatus.CANCELLED
    appointment.save()
    return appointment