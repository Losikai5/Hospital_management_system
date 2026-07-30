from django.db import IntegrityError, transaction
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


@transaction.atomic
def book_appointment(patient, doctor, appointment_date, appointment_time, reason=None):
    """Book an appointment using the doctor's generated available slots."""

    available_slots = get_available_slots(
        doctor=doctor,
        date=appointment_date,
    )

    if appointment_time not in available_slots:
        raise ValueError(
            "The selected time is not an available appointment slot."
        )

    try:
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status=AppointmentStatus.PENDING,
            reason=reason
        )
    except IntegrityError as error:
        raise ValueError(
            "This appointment slot was just booked by another patient."
        ) from error

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