// 醫師就診記錄頁面
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { providerApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { Encounter, Diagnosis, Prescription, LabResult, Payment } from '../../types';
import './ProviderEncounter.css';

export const ProviderEncounter: React.FC = () => {
  const { apptId } = useParams<{ apptId: string }>();
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [encounter, setEncounter] = useState<Encounter | null>(null);
  const [diagnoses, setDiagnoses] = useState<Diagnosis[]>([]);
  const [prescription, setPrescription] = useState<Prescription | null>(null);
  const [labResults, setLabResults] = useState<LabResult[]>([]);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'encounter' | 'diagnosis' | 'prescription' | 'lab' | 'payment'>('encounter');
  const [sessionId, setSessionId] = useState<number | null>(null);
  
  // 病人歷史記錄
  const [patientHistory, setPatientHistory] = useState<{
    encounters: any[];
    diagnoses: any[];
    lab_results: any[];
  } | null>(null);
  
  // 檢驗報告 Modal
  const [labReportModal, setLabReportModal] = useState<{
    show: boolean;
    encounterDate: string;
    labResults: any[];
  }>({ show: false, encounterDate: '', labResults: [] });
  
  // 疾病搜尋
  const [diseaseSearchQuery, setDiseaseSearchQuery] = useState('');
  const [diseaseOptions, setDiseaseOptions] = useState<Array<{ code_icd: string; description: string }>>([]);
  const [showDiseaseDropdown, setShowDiseaseDropdown] = useState(false);
  const [selectedDisease, setSelectedDisease] = useState<{ code_icd: string; description: string } | null>(null);
  
  // 藥品搜尋
  const [medicationSearchQuery, setMedicationSearchQuery] = useState('');
  const [medicationOptions, setMedicationOptions] = useState<Array<{ med_id: number; name: string; spec?: string; unit?: string }>>([]);
  const [showMedicationDropdown, setShowMedicationDropdown] = useState(false);
  const [selectedMedication, setSelectedMedication] = useState<{ med_id: number; name: string; spec?: string; unit?: string } | null>(null);
  
  // 表單狀態
  const [encounterForm, setEncounterForm] = useState({
    status: 1,
    chief_complaint: '',
    subjective: '',
    assessment: '',
    plan: '',
  });
  const [newDiagnosis, setNewDiagnosis] = useState({ code_icd: '', is_primary: false });
  const [prescriptionForm, setPrescriptionForm] = useState({
    items: [] as Array<{ med_id: number; med_name?: string; dosage: string; frequency: string; days: number; quantity: number }>,
  });
  const [currentPrescriptionItem, setCurrentPrescriptionItem] = useState({
    med_id: 0,
    med_name: '',
    dosage: '',
    frequency: '',
    days: 0,
    quantity: 0,
  });
  const [labForm, setLabForm] = useState({
    loinc_code: '',
    item_name: '',
    value: '',
    unit: '',
    ref_low: '',
    ref_high: '',
    abnormal_flag: 'N' as 'H' | 'L' | 'N',
    reported_at: '', // ISO format datetime string
  });
  const [paymentForm, setPaymentForm] = useState({
    amount: 0,
    method: 'cash' as 'cash' | 'card' | 'insurer',
    invoice_no: '',
  });

  useEffect(() => {
    if (userType !== 'provider' || !user || !apptId) {
      navigate('/provider/login');
      return;
    }
    loadData();
  }, [user, userType, apptId]);

  const loadData = async () => {
    if (!user || !apptId) return;
    let patientId: number | null = null;
    
    try {
      // 先獲取 appointment 的 patient_id 和 session_id（無論 encounter 是否存在）
      try {
        const apptInfo = await providerApi.getAppointmentPatientId(user.user_id, parseInt(apptId));
        patientId = apptInfo.patient_id;
        if (apptInfo.session_id) {
          setSessionId(apptInfo.session_id);
        }
      } catch (err) {
        console.error('獲取掛號資訊失敗:', err);
      }

      const enct = await providerApi.getEncounter(user.user_id, parseInt(apptId));
      setEncounter(enct);
      if (enct) {
        setEncounterForm({
          status: enct.status,
          chief_complaint: enct.chief_complaint || '',
          subjective: enct.subjective || '',
          assessment: enct.assessment || '',
          plan: enct.plan || '',
        });
        const enctId = enct.enct_id;
        
        // 載入相關資料
        const [diags, presc, labs, pay] = await Promise.all([
          providerApi.getDiagnoses(user.user_id, enctId).catch(() => []),
          providerApi.getPrescription(user.user_id, enctId).catch(() => null),
          providerApi.getLabResults(user.user_id, enctId).catch(() => []),
          providerApi.getPayment(user.user_id, enctId).catch(() => null),
        ]);
        setDiagnoses(diags);
        setPrescription(presc);
        if (presc) {
          // 如果處方已存在，載入處方項目（presc.items 應該包含 med_name）
          setPrescriptionForm({ items: (presc.items || []).map((item: any) => ({
            med_id: item.med_id,
            med_name: item.med_name || '',
            dosage: item.dosage || '',
            frequency: item.frequency || '',
            days: item.days || 0,
            quantity: item.quantity || 0,
          })) });
        } else {
          // 如果處方不存在，重置為空
          setPrescriptionForm({ items: [] });
        }
        setLabResults(labs);
        setPayment(pay);
        if (pay) {
          setPaymentForm({
            amount: pay.amount,
            method: pay.method,
            invoice_no: pay.invoice_no || '',
          });
        }
        
        // 使用 encounter 中的 patient_id（如果有的話），否則使用從 appointment 獲取的
        const finalPatientId = enct.patient_id || patientId;
        if (finalPatientId) {
          try {
            const history = await providerApi.getPatientHistory(user.user_id, finalPatientId);
            setPatientHistory(history);
          } catch (err) {
            console.error('載入病人歷史記錄失敗:', err);
          }
        }
      } else {
        // 如果 encounter 不存在，仍然載入病人歷史記錄
        if (patientId) {
          try {
            const history = await providerApi.getPatientHistory(user.user_id, patientId);
            setPatientHistory(history);
          } catch (err) {
            console.error('載入病人歷史記錄失敗:', err);
          }
        }
      }
    } catch (err: any) {
      // 如果 encounter 不存在（404），允許創建新的
      if (err.response?.status === 404) {
        console.log('就診記錄不存在，可以創建新的');
        setEncounter(null);
        // 重置表單為初始狀態
        setEncounterForm({
          status: 1,
          chief_complaint: '',
          subjective: '',
          assessment: '',
          plan: '',
        });
        setDiagnoses([]);
        setPrescription(null);
        setPrescriptionForm({ items: [] });
        setCurrentPrescriptionItem({
          med_id: 0,
          med_name: '',
          dosage: '',
          frequency: '',
          days: 0,
          quantity: 0,
        });
        setLabResults([]);
        setPayment(null);
        
        // 即使 encounter 不存在，也載入病人歷史記錄
        if (patientId) {
          try {
            const history = await providerApi.getPatientHistory(user.user_id, patientId);
            setPatientHistory(history);
          } catch (err) {
            console.error('載入病人歷史記錄失敗:', err);
          }
        }
      } else {
        console.error('載入資料失敗:', err);
        alert('載入資料失敗：' + (err.response?.data?.detail || err.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 搜尋疾病
  const searchDiseases = async (query: string) => {
    if (query.length < 1) {
      setDiseaseOptions([]);
      setShowDiseaseDropdown(false);
      setSelectedDisease(null);
      return;
    }
    try {
      const results = await providerApi.searchDiseases(query, 50);
      setDiseaseOptions(results);
      setShowDiseaseDropdown(true);
    } catch (err) {
      console.error('搜尋疾病失敗:', err);
    }
  };

  const searchMedications = async (query: string) => {
    if (query.length < 1) {
      setMedicationOptions([]);
      setShowMedicationDropdown(false);
      setSelectedMedication(null);
      return;
    }
    try {
      const results = await providerApi.searchMedications(query, 50);
      setMedicationOptions(results);
      setShowMedicationDropdown(true);
    } catch (err) {
      console.error('搜尋藥品失敗:', err);
    }
  };

  const handleSelectMedication = (medication: { med_id: number; name: string; spec?: string; unit?: string }) => {
    setSelectedMedication(medication);
    setCurrentPrescriptionItem({ 
      ...currentPrescriptionItem, 
      med_id: medication.med_id,
      med_name: medication.name
    });
    setMedicationSearchQuery(medication.name);
    setShowMedicationDropdown(false);
  };

  // 選擇疾病
  const handleSelectDisease = (disease: { code_icd: string; description: string }) => {
    setSelectedDisease(disease);
    setNewDiagnosis({ ...newDiagnosis, code_icd: disease.code_icd });
    setDiseaseSearchQuery(`${disease.code_icd} - ${disease.description}`);
    setShowDiseaseDropdown(false);
  };

  const handleSaveEncounter = async () => {
    if (!user || !apptId) return;
    try {
      await providerApi.upsertEncounter(user.user_id, parseInt(apptId), encounterForm);
      alert('儲存成功！');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '儲存失敗');
    }
  };

  const handleAddDiagnosis = async () => {
    if (!user || !newDiagnosis.code_icd) {
      alert('請選擇 ICD 代碼');
      return;
    }
    if (!encounter) {
      alert('請先建立就診記錄');
      setActiveTab('encounter');
      return;
    }
    try {
      console.log('新增診斷:', {
        providerId: user.user_id,
        enctId: encounter.enct_id,
        codeIcd: newDiagnosis.code_icd,
        isPrimary: newDiagnosis.is_primary
      });
      
      await providerApi.upsertDiagnosis(
        user.user_id,
        encounter.enct_id,
        newDiagnosis.code_icd,
        newDiagnosis.is_primary
      );
      alert('新增診斷成功！');
      setNewDiagnosis({ code_icd: '', is_primary: false });
      setDiseaseSearchQuery('');
      setSelectedDisease(null);
      setDiseaseOptions([]);
      loadData();
    } catch (err: any) {
      console.error('新增診斷錯誤:', err);
      console.error('錯誤詳情:', err.response?.data);
      const errorDetail = err.response?.data?.detail || err.message || '新增失敗';
      alert(`新增診斷失敗：${errorDetail}`);
    }
  };

  const handleSetPrimary = async (codeIcd: string) => {
    if (!user || !encounter) return;
    try {
      await providerApi.setPrimaryDiagnosis(user.user_id, encounter.enct_id, codeIcd);
      alert('設定主要診斷成功！');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '設定失敗');
    }
  };

  const handleAddPrescriptionItem = async () => {
    if (!user) return;
    if (!encounter) {
      alert('請先建立就診記錄');
      setActiveTab('encounter');
      return;
    }
    if (!currentPrescriptionItem.med_id) {
      alert('請選擇藥品');
      return;
    }
    try {
      // 將當前項目添加到列表（只傳送 med_id 給後端，但保留 med_name 用於顯示）
      const newItems = [...prescriptionForm.items, { ...currentPrescriptionItem }];
      
      // 添加項目時，如果處方不存在或未定稿，保持為草稿狀態（status = 1）
      // 只有點擊"開立處方"時才設為定稿（status = 2）
      const currentStatus = prescription?.status || 1;
      const newStatus = currentStatus === 2 ? 2 : 1; // 如果已定稿則保持定稿，否則保持草稿
      
      await providerApi.upsertPrescription(user.user_id, encounter.enct_id, {
        status: newStatus,
        items: newItems.map(item => ({
          med_id: item.med_id,
          dosage: item.dosage,
          frequency: item.frequency,
          days: item.days,
          quantity: item.quantity,
        })),
      });
      
      // 更新本地狀態
      setPrescriptionForm({ items: newItems });
      
      // 重置當前表單
      setCurrentPrescriptionItem({
        med_id: 0,
        med_name: '',
        dosage: '',
        frequency: '',
        days: 0,
        quantity: 0,
      });
      setMedicationSearchQuery('');
      setSelectedMedication(null);
      setMedicationOptions([]);
      
      alert('新增處方項目成功！');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '新增失敗');
    }
  };

  const handleRemovePrescriptionItem = async (index: number) => {
    if (!user || !encounter) return;
    if (!confirm('確定要刪除此處方項目嗎？')) return;
    
    try {
      const newItems = prescriptionForm.items.filter((_, i) => i !== index);
      
      // 刪除項目時，保持原有狀態（如果已定稿則保持定稿，否則保持草稿）
      const currentStatus = prescription?.status || 1;
      const newStatus = currentStatus === 2 ? 2 : 1;
      
      await providerApi.upsertPrescription(user.user_id, encounter.enct_id, {
        status: newStatus,
        items: newItems.map(item => ({
          med_id: item.med_id,
          dosage: item.dosage,
          frequency: item.frequency,
          days: item.days,
          quantity: item.quantity,
        })),
      });
      
      setPrescriptionForm({ items: newItems });
      alert('刪除處方項目成功！');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '刪除失敗');
    }
  };

  const handleFinalizePrescription = async () => {
    if (!user || !encounter) return;
    if (prescriptionForm.items.length === 0) {
      alert('請至少新增一個處方項目');
      return;
    }
    if (!confirm('確定要開立處方嗎？開立後將無法修改。')) return;
    
    try {
      await providerApi.upsertPrescription(user.user_id, encounter.enct_id, {
        status: 2,
        items: prescriptionForm.items.map(item => ({
          med_id: item.med_id,
          dosage: item.dosage,
          frequency: item.frequency,
          days: item.days,
          quantity: item.quantity,
        })),
      });
      alert('開立處方成功！');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '開立失敗');
    }
  };

  const handleAddLabResult = async () => {
    if (!user) return;
    if (!encounter) {
      alert('請先建立就診記錄');
      setActiveTab('encounter');
      return;
    }
    if (!labForm.item_name) {
      alert('請輸入項目名稱');
      return;
    }
    if (!labForm.reported_at) {
      alert('請輸入報告時間');
      return;
    }
    try {
      // 確保 reported_at 是 ISO 格式
      const reportedAt = labForm.reported_at 
        ? new Date(labForm.reported_at).toISOString()
        : new Date().toISOString();
      
      await providerApi.addLabResult(user.user_id, encounter.enct_id, {
        ...labForm,
        reported_at: reportedAt,
      });
      alert('新增檢驗結果成功！');
      setLabForm({
        loinc_code: '',
        item_name: '',
        value: '',
        unit: '',
        ref_low: '',
        ref_high: '',
        abnormal_flag: 'N',
        reported_at: '',
      });
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '新增失敗');
    }
  };

  const handleSavePayment = async () => {
    if (!user || !encounter) return;
    
    // 驗證金額
    if (!paymentForm.amount || paymentForm.amount <= 0) {
      alert('請輸入有效的金額（必須大於 0）');
      return;
    }
    
    try {
      await providerApi.upsertPayment(user.user_id, encounter.enct_id, {
        amount: paymentForm.amount,
        method: paymentForm.method,
        invoice_no: paymentForm.invoice_no || undefined,
      });
      alert('儲存繳費資料成功！');
      loadData();
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || err.message || '儲存失敗';
      alert(`儲存失敗：${errorDetail}`);
      if (import.meta.env.DEV) {
        console.error('Payment save error:', err);
      }
    }
  };

  if (loading) return <Layout><div>載入中...</div></Layout>;

  return (
    <Layout>
      <div className="provider-encounter">
        <button 
          className="btn btn-secondary" 
          onClick={() => navigate(-1)}
        >
          ← 返回預約管理
        </button>
        <h1>{encounter ? `就診記錄 - Encounter #${encounter.enct_id}` : '建立就診記錄'}</h1>
        
        <div className="tabs">
          <button
            className={activeTab === 'encounter' ? 'active' : ''}
            onClick={() => setActiveTab('encounter')}
          >
            就診記錄
          </button>
          <button
            className={activeTab === 'diagnosis' ? 'active' : ''}
            onClick={() => setActiveTab('diagnosis')}
          >
            診斷 ({diagnoses.length})
          </button>
          <button
            className={activeTab === 'prescription' ? 'active' : ''}
            onClick={() => setActiveTab('prescription')}
          >
            處方
          </button>
          <button
            className={activeTab === 'lab' ? 'active' : ''}
            onClick={() => setActiveTab('lab')}
          >
            檢驗結果 ({labResults.length})
          </button>
          <button
            className={activeTab === 'payment' ? 'active' : ''}
            onClick={() => setActiveTab('payment')}
          >
            繳費
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'encounter' && (
            <div className="encounter-form">
              <div className="form-group">
                <label>狀態</label>
                <select
                  value={encounterForm.status}
                  onChange={(e) => {
                    const val = parseInt(e.target.value, 10);
                    setEncounterForm({ ...encounterForm, status: isNaN(val) ? 1 : val });
                  }}
                  disabled={encounter?.status === 2}
                >
                  <option value="1">草稿</option>
                  <option value="2">定稿</option>
                </select>
              </div>
              <div className="form-group">
                <label>主訴</label>
                <textarea
                  value={encounterForm.chief_complaint}
                  onChange={(e) => setEncounterForm({ ...encounterForm, chief_complaint: e.target.value })}
                  disabled={encounter?.status === 2}
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>主觀描述</label>
                <textarea
                  value={encounterForm.subjective}
                  onChange={(e) => setEncounterForm({ ...encounterForm, subjective: e.target.value })}
                  disabled={encounter?.status === 2}
                  rows={5}
                />
              </div>
              <div className="form-group">
                <label>評估</label>
                <textarea
                  value={encounterForm.assessment}
                  onChange={(e) => setEncounterForm({ ...encounterForm, assessment: e.target.value })}
                  disabled={encounter?.status === 2}
                  rows={5}
                />
              </div>
              <div className="form-group">
                <label>計畫</label>
                <textarea
                  value={encounterForm.plan}
                  onChange={(e) => setEncounterForm({ ...encounterForm, plan: e.target.value })}
                  disabled={encounter?.status === 2}
                  rows={5}
                />
              </div>
              {(!encounter || encounter.status !== 2) && (
                <button className="btn btn-primary" onClick={handleSaveEncounter}>
                  {encounter ? '儲存' : '建立就診記錄'}
                </button>
              )}
            </div>
          )}

          {activeTab === 'diagnosis' && (
            <div className="diagnosis-section">
              <div className="add-diagnosis-form">
                <h3>新增診斷</h3>
                <div className="form-row">
                  <div className="disease-search-container">
                    <input
                      type="text"
                      placeholder="搜尋 ICD 代碼..."
                      value={diseaseSearchQuery}
                      onChange={(e) => {
                        const query = e.target.value;
                        setDiseaseSearchQuery(query);
                        if (query.length > 0) {
                          searchDiseases(query);
                        } else {
                          setDiseaseOptions([]);
                          setShowDiseaseDropdown(false);
                          setSelectedDisease(null);
                          setNewDiagnosis({ ...newDiagnosis, code_icd: '' });
                        }
                      }}
                      onFocus={() => {
                        if (diseaseSearchQuery.length > 0 && diseaseOptions.length > 0) {
                          setShowDiseaseDropdown(true);
                        }
                      }}
                      onBlur={() => {
                        // 延遲關閉，讓點擊選項有時間執行
                        setTimeout(() => setShowDiseaseDropdown(false), 200);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Escape') {
                          setShowDiseaseDropdown(false);
                        }
                      }}
                    />
                    {showDiseaseDropdown && (
                      <div className="disease-dropdown">
                        {diseaseOptions.length > 0 ? (
                          <>
                            <div className="disease-dropdown-header">
                              找到 {diseaseOptions.length} 個結果
                            </div>
                            {diseaseOptions.map((disease) => (
                              <div
                                key={disease.code_icd}
                                className={`disease-option ${selectedDisease?.code_icd === disease.code_icd ? 'selected' : ''}`}
                                onClick={() => handleSelectDisease(disease)}
                                onMouseEnter={() => setSelectedDisease(disease)}
                              >
                                <div className="disease-code">{disease.code_icd}</div>
                              </div>
                            ))}
                          </>
                        ) : diseaseSearchQuery.length > 0 ? (
                          <div className="disease-option no-results">
                            沒有找到相關疾病
                          </div>
                        ) : null}
                      </div>
                    )}
                    {selectedDisease && (
                      <div className="selected-disease-info">
                        已選擇：<strong>{selectedDisease.code_icd}</strong>
                      </div>
                    )}
                  </div>
                  <label className="primary-diagnosis-label">
                    <input
                      type="checkbox"
                      checked={newDiagnosis.is_primary}
                      onChange={(e) => setNewDiagnosis({ ...newDiagnosis, is_primary: e.target.checked })}
                    />
                    設為主要診斷
                  </label>
                  <button 
                    className="btn btn-primary" 
                    onClick={handleAddDiagnosis}
                    disabled={!newDiagnosis.code_icd}
                  >
                    新增
                  </button>
                </div>
              </div>
              <div className="diagnoses-list">
                <h3>診斷列表</h3>
                {diagnoses.length === 0 ? (
                  <p>目前沒有診斷</p>
                ) : (
                  <table className="diagnoses-table">
                    <thead>
                      <tr>
                        <th>ICD 代碼</th>
                        <th>疾病名稱</th>
                        <th>主要診斷</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {diagnoses.map((diag, idx) => (
                        <tr key={idx}>
                          <td>{diag.code_icd}</td>
                          <td>{diag.disease_name}</td>
                          <td>{diag.is_primary ? '✓' : ''}</td>
                          <td>
                            {!diag.is_primary && (
                              <button
                                className="btn-small btn-primary"
                                onClick={() => handleSetPrimary(diag.code_icd)}
                              >
                                設為主要
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {activeTab === 'prescription' && (
            <div className="prescription-section">
              {prescription && prescription.status === 2 && (
                <>
                  <div className="prescription-info">
                    <p className="prescription-notice">處方已開立，無法修改</p>
                  </div>
                  <div className="prescription-display">
                    <h3>處方內容</h3>
                    <table className="prescription-table">
                      <thead>
                        <tr>
                          <th>藥品名稱</th>
                          <th>劑量</th>
                          <th>頻率</th>
                          <th>天數</th>
                          <th>數量</th>
                        </tr>
                      </thead>
                      <tbody>
                        {prescription.items.map((item: any, idx: number) => (
                          <tr key={idx}>
                            <td>{item.med_name || item.med_id}</td>
                            <td>{item.dosage || '-'}</td>
                            <td>{item.frequency || '-'}</td>
                            <td>{item.days}</td>
                            <td>{item.quantity}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
              {(!prescription || (prescription && prescription.status !== 2)) && (
                <>
                  {prescription && prescription.status !== 2 && (
                    <div className="prescription-info">
                      <p className="prescription-notice">處方草稿中，可繼續新增項目</p>
                    </div>
                  )}
                  <div className="prescription-items">
                    <h3>{prescription ? '繼續新增處方項目' : '新增處方項目'}</h3>
                    <div className="prescription-item-form">
                      <div className="medication-search-container">
                        <label>藥品名稱</label>
                        <input
                          type="text"
                          placeholder="搜尋藥品名稱..."
                          value={medicationSearchQuery}
                          onChange={(e) => {
                            const query = e.target.value;
                            setMedicationSearchQuery(query);
                            if (query.length > 0) {
                              searchMedications(query);
                            } else {
                              setMedicationOptions([]);
                              setShowMedicationDropdown(false);
                              setSelectedMedication(null);
                              setCurrentPrescriptionItem({ ...currentPrescriptionItem, med_id: 0, med_name: '' });
                            }
                          }}
                          onFocus={() => {
                            if (medicationSearchQuery.length > 0 && medicationOptions.length > 0) {
                              setShowMedicationDropdown(true);
                            }
                          }}
                          onBlur={() => {
                            setTimeout(() => setShowMedicationDropdown(false), 200);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Escape') {
                              setShowMedicationDropdown(false);
                            }
                          }}
                        />
                        {showMedicationDropdown && (
                          <div className="medication-dropdown">
                            {medicationOptions.length > 0 ? (
                              <>
                                <div className="medication-dropdown-header">
                                  找到 {medicationOptions.length} 個結果
                                </div>
                                {medicationOptions.map((medication) => (
                                  <div
                                    key={medication.med_id}
                                    className={`medication-option ${selectedMedication?.med_id === medication.med_id ? 'selected' : ''}`}
                                    onClick={() => handleSelectMedication(medication)}
                                    onMouseEnter={() => setSelectedMedication(medication)}
                                  >
                                    <div className="medication-name">{medication.name}</div>
                                  </div>
                                ))}
                              </>
                            ) : medicationSearchQuery.length > 0 ? (
                              <div className="medication-option no-results">
                                沒有找到相關藥品
                              </div>
                            ) : null}
                          </div>
                        )}
                        {selectedMedication && (
                          <div className="selected-medication-info">
                            已選擇：<strong>{selectedMedication.name}</strong>
                          </div>
                        )}
                      </div>
                      <input
                        type="text"
                        placeholder="劑量"
                        value={currentPrescriptionItem.dosage}
                        onChange={(e) => setCurrentPrescriptionItem({ ...currentPrescriptionItem, dosage: e.target.value })}
                      />
                      <input
                        type="text"
                        placeholder="頻率"
                        value={currentPrescriptionItem.frequency}
                        onChange={(e) => setCurrentPrescriptionItem({ ...currentPrescriptionItem, frequency: e.target.value })}
                      />
                      <input
                        type="number"
                        placeholder="天數"
                        value={currentPrescriptionItem.days || ''}
                        onChange={(e) => {
                          const val = e.target.value;
                          const num = val === '' ? 0 : parseInt(val, 10);
                          setCurrentPrescriptionItem({ ...currentPrescriptionItem, days: isNaN(num) ? 0 : num });
                        }}
                      />
                      <input
                        type="number"
                        placeholder="數量"
                        value={currentPrescriptionItem.quantity || ''}
                        onChange={(e) => {
                          const val = e.target.value;
                          const num = val === '' ? 0 : parseFloat(val);
                          setCurrentPrescriptionItem({ ...currentPrescriptionItem, quantity: isNaN(num) ? 0 : num });
                        }}
                      />
                      <div className="prescription-item-actions">
                        <button
                          className="btn-small btn-danger"
                          onClick={() => {
                            setCurrentPrescriptionItem({
                              med_id: 0,
                              med_name: '',
                              dosage: '',
                              frequency: '',
                              days: 0,
                              quantity: 0,
                            });
                            setMedicationSearchQuery('');
                            setSelectedMedication(null);
                          }}
                        >
                          清除
                        </button>
                        <button
                          className="btn btn-primary"
                          onClick={handleAddPrescriptionItem}
                          disabled={!currentPrescriptionItem.med_id || !currentPrescriptionItem.med_name}
                        >
                          新增處方項目
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {prescriptionForm.items.length > 0 && (
                    <div className="prescription-items-list">
                      <h3>已新增的處方項目 ({prescriptionForm.items.length})</h3>
                      <table className="prescription-items-table">
                        <thead>
                          <tr>
                            <th>藥品名稱</th>
                            <th>劑量</th>
                            <th>頻率</th>
                            <th>天數</th>
                            <th>數量</th>
                            <th>操作</th>
                          </tr>
                        </thead>
                        <tbody>
                          {prescriptionForm.items.map((item, idx) => (
                            <tr key={idx}>
                              <td>{item.med_name || item.med_id}</td>
                              <td>{item.dosage || '-'}</td>
                              <td>{item.frequency || '-'}</td>
                              <td>{item.days}</td>
                              <td>{item.quantity}</td>
                              <td>
                                <button
                                  className="btn-small btn-danger"
                                  onClick={() => handleRemovePrescriptionItem(idx)}
                                >
                                  刪除
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <div className="prescription-finalize-actions">
                        <button className="btn btn-primary" onClick={handleFinalizePrescription}>
                          開立處方
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {activeTab === 'lab' && (
            <div className="lab-section">
              <div className="add-lab-form">
                <h3>新增檢驗結果</h3>
                <div className="form-grid">
                  <input
                    type="text"
                    placeholder="LOINC 代碼（選填）"
                    value={labForm.loinc_code}
                    onChange={(e) => setLabForm({ ...labForm, loinc_code: e.target.value })}
                  />
                  <input
                    type="text"
                    placeholder="項目名稱 *"
                    value={labForm.item_name}
                    onChange={(e) => setLabForm({ ...labForm, item_name: e.target.value })}
                    required
                  />
                  <input
                    type="text"
                    placeholder="數值"
                    value={labForm.value}
                    onChange={(e) => setLabForm({ ...labForm, value: e.target.value })}
                  />
                  <input
                    type="text"
                    placeholder="單位"
                    value={labForm.unit}
                    onChange={(e) => setLabForm({ ...labForm, unit: e.target.value })}
                  />
                  <input
                    type="text"
                    placeholder="參考範圍下限"
                    value={labForm.ref_low}
                    onChange={(e) => setLabForm({ ...labForm, ref_low: e.target.value })}
                  />
                  <input
                    type="text"
                    placeholder="參考範圍上限"
                    value={labForm.ref_high}
                    onChange={(e) => setLabForm({ ...labForm, ref_high: e.target.value })}
                  />
                  <select
                    value={labForm.abnormal_flag}
                    onChange={(e) => setLabForm({ ...labForm, abnormal_flag: e.target.value as any })}
                  >
                    <option value="N">正常</option>
                    <option value="H">高</option>
                    <option value="L">低</option>
                  </select>
                  <input
                    type="datetime-local"
                    placeholder="報告時間 *"
                    value={labForm.reported_at}
                    onChange={(e) => setLabForm({ ...labForm, reported_at: e.target.value })}
                    required
                  />
                </div>
                <button className="btn btn-primary" onClick={handleAddLabResult}>
                  新增
                </button>
              </div>
              <div className="lab-results-list">
                <h3>檢驗結果列表</h3>
                {labResults.length === 0 ? (
                  <p>目前沒有檢驗結果</p>
                ) : (
                  <table className="lab-results-table">
                    <thead>
                      <tr>
                        <th>項目名稱</th>
                        <th>數值</th>
                        <th>單位</th>
                        <th>參考範圍</th>
                        <th>異常標記</th>
                      </tr>
                    </thead>
                    <tbody>
                      {labResults.map((result) => (
                        <tr key={result.lab_id}>
                          <td>{result.item_name}</td>
                          <td>{result.value || 'N/A'}</td>
                          <td>{result.unit || 'N/A'}</td>
                          <td>
                            {result.ref_low && result.ref_high
                              ? `${result.ref_low} - ${result.ref_high}`
                              : 'N/A'}
                          </td>
                          <td>
                            {result.abnormal_flag === 'H' && <span className="flag-high">高</span>}
                            {result.abnormal_flag === 'L' && <span className="flag-low">低</span>}
                            {result.abnormal_flag === 'N' && <span className="flag-normal">正常</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {activeTab === 'payment' && (
            <div className="payment-section">
              {payment ? (
                <div className="payment-display">
                  <h3>繳費資料（僅供查看）</h3>
                  <div className="payment-info">
                    <div className="info-item">
                      <label>金額：</label>
                      <span>{payment.amount}</span>
                    </div>
                    <div className="info-item">
                      <label>付款方式：</label>
                      <span>
                        {payment.method === 'cash' ? '現金' : 
                         payment.method === 'card' ? '信用卡' : 
                         payment.method === 'insurer' ? '保險' : payment.method}
                      </span>
                    </div>
                    {payment.invoice_no && (
                      <div className="info-item">
                        <label>發票號碼：</label>
                        <span>{payment.invoice_no}</span>
                      </div>
                    )}
                    {payment.paid_at && (
                      <div className="info-item">
                        <label>繳費時間：</label>
                        <span>{new Date(payment.paid_at).toLocaleString('zh-TW')}</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="payment-form">
                  <h3>新增繳費資料</h3>
                  <div className="form-group">
                    <label>金額</label>
                    <input
                      type="number"
                      value={paymentForm.amount || ''}
                      onChange={(e) => setPaymentForm({ ...paymentForm, amount: parseFloat(e.target.value) || 0 })}
                      required
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="form-group">
                    <label>付款方式</label>
                    <select
                      value={paymentForm.method}
                      onChange={(e) => setPaymentForm({ ...paymentForm, method: e.target.value as any })}
                    >
                      <option value="cash">現金</option>
                      <option value="card">信用卡</option>
                      <option value="insurer">保險</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>發票號碼（選填）</label>
                    <input
                      type="text"
                      value={paymentForm.invoice_no}
                      onChange={(e) => setPaymentForm({ ...paymentForm, invoice_no: e.target.value })}
                    />
                  </div>
                  <button className="btn btn-primary" onClick={handleSavePayment}>
                    建立繳費記錄
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 病人過往記錄 */}
        {patientHistory && (
          <div className="patient-history-section">
            <h2>病人過往記錄</h2>
            {patientHistory.encounters.length === 0 ? (
              <p>無過往就診記錄</p>
            ) : (
              <div className="history-list">
                {patientHistory.encounters.map((enc: any) => {
                  // 找到屬於這個 encounter 的診斷
                  const encounterDiagnoses = patientHistory.diagnoses.filter(
                    (diag: any) => diag.enct_id === enc.enct_id
                  );
                  // 找到屬於這個 encounter 的檢驗結果
                  const encounterLabResults = patientHistory.lab_results.filter(
                    (lab: any) => lab.enct_id === enc.enct_id
                  );
                  
                  return (
                    <div key={enc.enct_id} className="history-card-combined">
                      <div className="history-card-main">
                        <div className="history-card-header">
                          <strong>{new Date(enc.encounter_at).toLocaleString('zh-TW')}</strong>
                          <span>{enc.department_name || '未知科別'}</span>
                          <span>{enc.provider_name}</span>
                        </div>
                        {enc.chief_complaint && (
                          <div className="history-card-content">
                            <strong>主訴：</strong>{enc.chief_complaint}
                          </div>
                        )}
                        {encounterDiagnoses.length > 0 && (
                          <div className="diagnosis-tags">
                            {encounterDiagnoses.map((diag: any, diagIdx: number) => (
                              <span key={diagIdx} className="diagnosis-tag" title={diag.description}>
                                {diag.code_icd}
                                {diag.is_primary && <span className="primary-badge">主</span>}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      {encounterLabResults.length > 0 && (
                        <button
                          className="btn-lab-report"
                          onClick={() =>
                            setLabReportModal({
                              show: true,
                              encounterDate: new Date(enc.encounter_at).toLocaleString('zh-TW'),
                              labResults: encounterLabResults,
                            })
                          }
                        >
                          📋 檢驗報告 ({encounterLabResults.length})
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* 檢驗報告 Modal */}
        {labReportModal.show && (
          <div className="lab-modal-overlay" onClick={() => setLabReportModal({ show: false, encounterDate: '', labResults: [] })}>
            <div className="lab-modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="lab-modal-header">
                <h3>檢驗報告 - {labReportModal.encounterDate}</h3>
                <button
                  className="lab-modal-close"
                  onClick={() => setLabReportModal({ show: false, encounterDate: '', labResults: [] })}
                >
                  ×
                </button>
              </div>
              <div className="lab-modal-body">
                {labReportModal.labResults.length === 0 ? (
                  <p>無檢驗結果</p>
                ) : (
                  <table className="lab-results-table">
                    <thead>
                      <tr>
                        <th>項目名稱</th>
                        <th>數值</th>
                        <th>單位</th>
                        <th>參考範圍</th>
                        <th>狀態</th>
                        <th>報告時間</th>
                      </tr>
                    </thead>
                    <tbody>
                      {labReportModal.labResults.map((lab: any) => (
                        <tr key={lab.lab_id}>
                          <td>{lab.item_name}</td>
                          <td>{lab.value || '-'}</td>
                          <td>{lab.unit || '-'}</td>
                          <td>
                            {lab.ref_low && lab.ref_high
                              ? `${lab.ref_low} - ${lab.ref_high}`
                              : lab.ref_low || lab.ref_high || '-'}
                          </td>
                          <td>
                            {lab.abnormal_flag === 'H' && <span className="flag-high">高</span>}
                            {lab.abnormal_flag === 'L' && <span className="flag-low">低</span>}
                            {lab.abnormal_flag === 'N' && <span className="flag-normal">正常</span>}
                            {!lab.abnormal_flag && '-'}
                          </td>
                          <td>
                            {lab.reported_at
                              ? new Date(lab.reported_at).toLocaleString('zh-TW')
                              : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

