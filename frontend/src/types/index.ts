// 共用類型定義

export interface User {
  user_id: number;
  name: string;
}

export interface Patient extends User {
  national_id: string;
  birth_date: string;
  sex: 'M' | 'F' | 'O';
  phone: string;
}

export interface Provider extends User {
  dept_id: number;
  license_no: string;
}

export interface Department {
  dept_id: number;
  name: string;
}

export interface ClinicSession {
  session_id: number;
  provider_id: number;
  provider_name?: string;
  dept_id?: number;
  dept_name?: string;
  date: string;
  period: number;  // 1=早診(09:00-12:00), 2=午診(14:00-17:00), 3=晚診(18:00-21:00)
  start_time?: string;  // 向後兼容，由 period 計算得出
  end_time?: string;    // 向後兼容，由 period 計算得出
  capacity: number;
  booked_count: number;  // 後端返回的是 booked_count
  status: number;
}

export interface Appointment {
  appt_id: number;
  patient_id: number;
  patient_name: string;
  session_id: number;
  session_date: string;
  session_start_time: string;
  session_end_time: string;
  provider_name: string;
  dept_name: string;
  slot_seq: number;
  status: number;
  status_name: string;
}

export interface Encounter {
  enct_id: number;
  appt_id: number;
  provider_id: number;
  status: number;
  chief_complaint?: string;
  subjective?: string;
  assessment?: string;
  plan?: string;
  encounter_at: string;
  patient_id?: number;
}

export interface Diagnosis {
  enct_id: number;
  code_icd: string;
  disease_name: string;
  is_primary: boolean;
}

export interface PrescriptionItem {
  med_id: number;
  med_name: string;
  dosage?: string;
  frequency?: string;
  days: number;
  quantity: number;
}

export interface Prescription {
  rx_id: number;
  enct_id: number;
  items: PrescriptionItem[];
}

export interface LabResult {
  lab_id: number;
  enct_id: number;
  loinc_code?: string;
  item_name: string;
  value?: string;
  unit?: string;
  ref_low?: string;
  ref_high?: string;
  abnormal_flag?: 'H' | 'L' | 'N';
  reported_at: string;
}

export interface Payment {
  payment_id: number;
  enct_id: number;
  amount: number;
  method: 'cash' | 'card' | 'insurer';
  invoice_no?: string;
  paid_at?: string;
}

export interface PatientHistory {
  encounters: Encounter[];
  prescriptions: Prescription[];
  lab_results: LabResult[];
  payments: Payment[];
}

