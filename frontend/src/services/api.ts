// API 服務層
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== 病人端 API ====================

export const patientApi = {
  // 註冊
  register: async (data: {
    name: string;
    password: string;
    national_id: string;
    birth_date: string;
    sex: 'M' | 'F' | 'O';
    phone: string;
  }) => {
    const response = await api.post('/patient/register', data);
    return response.data;
  },

  // 登入
  login: async (data: { national_id: string; password: string }) => {
    const response = await api.post('/patient/login', data);
    return response.data;
  },

  // 取得病人資料
  getProfile: async (patientId: number) => {
    const response = await api.get(`/patient/${patientId}/profile`);
    return response.data;
  },

  // 查詢可預約門診時段
  listSessions: async (params?: {
    dept_id?: number;
    provider_id?: number;
    date?: string;
  }) => {
    const response = await api.get('/patient/sessions', { params });
    return response.data;
  },

  // 列出所有掛號
  listAppointments: async (patientId: number) => {
    const response = await api.get('/patient/appointments', {
      params: { patient_id: patientId },
    });
    return response.data;
  },

  // 建立掛號
  createAppointment: async (patientId: number, sessionId: number) => {
    const response = await api.post(
      '/patient/appointments',
      { session_id: sessionId },
      { params: { patient_id: patientId } }
    );
    return response.data;
  },

  // 取消掛號
  cancelAppointment: async (apptId: number, patientId: number) => {
    const response = await api.delete(`/patient/appointments/${apptId}`, {
      params: { patient_id: patientId },
    });
    return response.data;
  },

  // 修改掛號（改期）
  rescheduleAppointment: async (
    apptId: number,
    patientId: number,
    newSessionId: number
  ) => {
    const response = await api.patch(
      `/patient/appointments/${apptId}/reschedule`,
      { new_session_id: newSessionId },
      { params: { patient_id: patientId } }
    );
    return response.data;
  },

  // 病人報到
  checkin: async (apptId: number, patientId: number) => {
    const response = await api.post(
      `/patient/appointments/${apptId}/checkin`,
      {},
      { params: { patient_id: patientId } }
    );
    return response.data;
  },

  // 取得完整歷史記錄
  getHistory: async (patientId: number) => {
    const response = await api.get('/patient/history', {
      params: { patient_id: patientId },
    });
    return response.data;
  },

  // 列出繳費記錄
  listPayments: async (patientId: number) => {
    const response = await api.get('/patient/payments', {
      params: { patient_id: patientId },
    });
    return response.data;
  },

  // 線上繳費
  payOnline: async (
    paymentId: number,
    patientId: number,
    data: { method: string; invoice_no?: string }
  ) => {
    const response = await api.post(
      `/patient/payments/${paymentId}/pay`,
      data,
      { params: { patient_id: patientId } }
    );
    return response.data;
  },

  // 列出所有部門
  listDepartments: async () => {
    try {
      const response = await api.get('/departments');
      return response.data;
    } catch (error: any) {
      // 如果端點不存在，返回空陣列，讓前端使用預設列表
      if (error.response?.status === 404) {
        return [];
      }
      throw error;
    }
  },

  // 列出所有分類
  listCategories: async () => {
    try {
      const response = await api.get('/departments/categories');
      return response.data;
    } catch (error: any) {
      // 如果端點不存在，返回空陣列
      if (error.response?.status === 404) {
        return [];
      }
      throw error;
    }
  },

  // 根據名稱獲取部門
  getDepartmentByName: async (name: string) => {
    try {
      const response = await api.get('/departments/by-name', {
        params: { name },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },
};

// ==================== 醫師端 API ====================

export const providerApi = {
  // 註冊
  register: async (data: {
    name: string;
    password: string;
    license_no: string;
    dept_id: number;
  }) => {
    const response = await api.post('/provider/register', data);
    return response.data;
  },

  // 登入
  login: async (data: { license_no: string; password: string }) => {
    const response = await api.post('/provider/login', data);
    return response.data;
  },

  // 取得醫師資料
  getProfile: async (providerId: number) => {
    const response = await api.get(`/provider/${providerId}/profile`);
    return response.data;
  },

  // 列出門診時段
  listSessions: async (
    providerId: number,
    params?: {
      from_date?: string;
      to_date?: string;
      status?: number;
    }
  ) => {
    const response = await api.get(`/provider/${providerId}/sessions`, {
      params,
    });
    return response.data;
  },

  // 建立診次
  createSession: async (
    providerId: number,
    data: {
      date: string;
      period: number;  // 1=早診, 2=午診, 3=晚診
      capacity: number;
    }
  ) => {
    const response = await api.post(
      `/provider/${providerId}/sessions`,
      data
    );
    return response.data;
  },

  // 更新診次
  updateSession: async (
    providerId: number,
    sessionId: number,
    data: {
      date: string;
      period: number;  // 1=早診, 2=午診, 3=晚診
      capacity: number;
      status?: number;
    }
  ) => {
    const response = await api.put(
      `/provider/${providerId}/sessions/${sessionId}`,
      data
    );
    return response.data;
  },

  // 取消診次
  cancelSession: async (providerId: number, sessionId: number) => {
    const response = await api.post(
      `/provider/${providerId}/sessions/${sessionId}/cancel`
    );
    return response.data;
  },

  // 列出預約
  listAppointments: async (providerId: number, sessionId: number) => {
    const response = await api.get(
      `/provider/${providerId}/sessions/${sessionId}/appointments`
    );
    return response.data;
  },

  // 取得就診記錄
  getEncounter: async (providerId: number, apptId: number) => {
    const response = await api.get(
      `/provider/${providerId}/appointments/${apptId}/encounter`
    );
    return response.data;
  },

  // 鎖定 encounter（防止其他裝置同時編輯）
  lockEncounter: async (providerId: number, apptId: number) => {
    const response = await api.post(
      `/provider/${providerId}/appointments/${apptId}/encounter/lock`
    );
    return response.data;
  },

  // 釋放 encounter 鎖定
  unlockEncounter: async (providerId: number, apptId: number) => {
    const response = await api.post(
      `/provider/${providerId}/appointments/${apptId}/encounter/unlock`
    );
    return response.data;
  },

  // 建立/更新就診記錄
  upsertEncounter: async (
    providerId: number,
    apptId: number,
    data: {
      status: number;
      chief_complaint?: string;
      subjective?: string;
      assessment?: string;
      plan?: string;
    }
  ) => {
    const response = await api.put(
      `/provider/${providerId}/appointments/${apptId}/encounter`,
      data
    );
    return response.data;
  },

  // 取得診斷列表
  getDiagnoses: async (providerId: number, enctId: number) => {
    const response = await api.get(
      `/provider/${providerId}/encounters/${enctId}/diagnoses`
    );
    return response.data;
  },

  // 建立/更新診斷
  upsertDiagnosis: async (
    providerId: number,
    enctId: number,
    codeIcd: string,
    isPrimary: boolean
  ) => {
    const response = await api.put(
      `/provider/${providerId}/encounters/${enctId}/diagnoses/${codeIcd}`,
      { is_primary: isPrimary }
    );
    return response.data;
  },

  // 設定主要診斷
  setPrimaryDiagnosis: async (
    providerId: number,
    enctId: number,
    codeIcd: string
  ) => {
    const response = await api.post(
      `/provider/${providerId}/encounters/${enctId}/primary-diagnosis`,
      { code_icd: codeIcd }
    );
    return response.data;
  },

  // 取得處方
  getPrescription: async (providerId: number, enctId: number) => {
    const response = await api.get(
      `/provider/${providerId}/encounters/${enctId}/prescription`
    );
    return response.data;
  },

  // 建立/更新處方（草稿）
  upsertPrescription: async (
    providerId: number,
    enctId: number,
    data: {
      items: Array<{
        med_id: number;
        dosage?: string;
        frequency?: string;
        days: number;
        quantity: number;
      }>;
    }
  ) => {
    const response = await api.put(
      `/provider/${providerId}/encounters/${enctId}/prescription`,
      data
    );
    return response.data;
  },

  // 開立處方（定稿）
  finalizePrescription: async (
    providerId: number,
    enctId: number,
    data: {
      items: Array<{
        med_id: number;
        dosage?: string;
        frequency?: string;
        days: number;
        quantity: number;
      }>;
    }
  ) => {
    const response = await api.post(
      `/provider/${providerId}/encounters/${enctId}/prescription/finalize`,
      data
    );
    return response.data;
  },

  // 取得檢驗結果列表
  getLabResults: async (providerId: number, enctId: number) => {
    const response = await api.get(
      `/provider/${providerId}/encounters/${enctId}/lab-results`
    );
    return response.data;
  },

  // 新增檢驗結果
  addLabResult: async (
    providerId: number,
    enctId: number,
    data: {
      loinc_code?: string;
      item_name: string;
      value?: string;
      unit?: string;
      ref_low?: string;
      ref_high?: string;
      abnormal_flag?: 'H' | 'L' | 'N';
      reported_at?: string;
    }
  ) => {
    const response = await api.post(
      `/provider/${providerId}/encounters/${enctId}/lab-results`,
      data
    );
    return response.data;
  },

  // 取得繳費資訊
  getPayment: async (providerId: number, enctId: number) => {
    const response = await api.get(
      `/provider/${providerId}/encounters/${enctId}/payment`
    );
    return response.data;
  },

  // 建立/更新繳費資料
  upsertPayment: async (
    providerId: number,
    enctId: number,
    data: {
      amount: number;
      method: 'cash' | 'card' | 'insurer';
      invoice_no?: string;
    }
  ) => {
    const response = await api.post(
      `/provider/${providerId}/encounters/${enctId}/payment`,
      data
    );
    return response.data;
  },

  // 搜尋疾病（ICD 代碼）
  searchDiseases: async (query?: string, limit: number = 50) => {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    params.append('limit', limit.toString());
    const response = await api.get(`/provider/diseases?${params.toString()}`);
    return response.data;
  },

  // 搜尋藥品
  searchMedications: async (query?: string, limit: number = 50) => {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    params.append('limit', limit.toString());
    const response = await api.get(`/provider/medications?${params.toString()}`);
    return response.data;
  },

  // 取得掛號對應的病人 ID
  getAppointmentPatientId: async (providerId: number, apptId: number) => {
    const response = await api.get(
      `/provider/${providerId}/appointments/${apptId}/patient-id`
    );
    return response.data;
  },

  // 取得病人過往所有就診記錄、診斷與檢驗報告
  getPatientHistory: async (providerId: number, patientId: number) => {
    const response = await api.get(
      `/provider/${providerId}/patients/${patientId}/history`
    );
    return response.data;
  },
};

export default api;

