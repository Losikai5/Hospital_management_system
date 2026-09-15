export type Appointment = {
  id: number;
  patient_name: string;
  patient_email: string;
  doctor_name: string;
  doctor_email: string;
  doctor_specialization: string;
  appointment_date: string;
  appointment_time: string;
  reason: string;
  status: string;
};

export type Doctor = {
  id: number;
  first_name: string;
  last_name: string;
  specialization_display: string;
  is_available: boolean;
  bio: string;
  years_of_experience: number;
  consultation_fee: string | number;
};

export type Patient = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
};

export type PatientProfile = {
  id: number;
  blood_type?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  medical_history_summary?: string;
  insurance_details?: string;
};

export type Medicine = {
  id: number;
  name: string;
  description?: string;
  unit_cost?: string | number;
  unit_type?: string;
  stock_quantity?: number;
  is_low_stock?: boolean;
};

export type Prescription = {
  id: number;
  medicine_name: string;
  medicine_unit?: string;
  dosage: string;
  frequency: string;
  duration: string;
  patient_email: string;
  doctor_email: string;
  prescribed_at: string;
  quantity_prescribed: number;
  status: string;
};

export type MedicalRecord = {
  id: number;
  diagnosis: string;
  treatment_prescribed?: string;
  notes?: string;
  doctor_email: string;
  patient_email: string;
  appointment_date: string;
};

export type Invoice = {
  id: number;
  appointment: number;
  patient_email: string;
  status: string;
  total_amount: string;
  amount_paid: string;
  balance: string;
  created_at: string;
};

export type AuditLog = {
  id: number;
  actor_email: string;
  action: string;
  method: string;
  path: string;
  request_id: string;
  status_code: number;
  created_at: string;
};

export type PermissionInfo = { code: string; name: string; description?: string };
export type RoleDetail = {
  code: string;
  name: string;
  description?: string;
  permissions: string[];
  is_system: boolean;
};
