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
  
  // 病人歷史記錄
  const [patientHistory, setPatientHistory] = useState<{
    encounters: any[];
    diagnoses: any[];
    lab_results: any[];
  } | null>(null);
  
  // 疾病搜尋
  const [diseaseSearchQuery, setDiseaseSearchQuery] = useState('');
  const [diseaseOptions, setDiseaseOptions] = useState<Array<{ code_icd: string; description: string }>>([]);
  const [showDiseaseDropdown, setShowDiseaseDropdown] = useState(false);
  const [selectedDisease, setSelectedDisease] = useState<{ code_icd: string; description: string } | null>(null);
  
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
    items: [{ med_id: 1, dosage: '', frequency: '', days: 7, quantity: 1 }],
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
      // 先獲取 appointment 的 patient_id（無論 encounter 是否存在）
      try {
        const apptInfo = await providerApi.getAppointmentPatientId(user.user_id, parseInt(apptId));
        patientId = apptInfo.patient_id;
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
      alert(err.response?.data?.detail || '新增失敗');
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

  const handleSavePrescription = async () => {
    if (!user) return;
    if (!encounter) {
      alert('請先建立就診記錄');
      setActiveTab('encounter');
      return;
    }
    try {
      // 處方一旦開立即無法更改，所以 status 固定為 2（定稿）
      await providerApi.upsertPrescription(user.user_id, encounter.enct_id, {
        status: 2,
        items: prescriptionForm.items,
      });
      alert('開立處方成功！');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '儲存失敗');
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
    try {
      await providerApi.upsertPayment(user.user_id, encounter.enct_id, paymentForm);
      alert('儲存繳費資料成功！');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '儲存失敗');
    }
  };

  if (loading) return <Layout><div>載入中...</div></Layout>;

  return (
    <Layout>
      <div className="provider-encounter">
        <button className="btn btn-secondary" onClick={() => navigate('/provider/sessions')}>
          ← 返回門診時段
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
                      placeholder="搜尋 ICD 代碼或疾病名稱..."
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
                                <div className="disease-description">{disease.description}</div>
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
                        已選擇：<strong>{selectedDisease.code_icd}</strong> - {selectedDisease.description}
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
              {prescription && (
                <>
                  <div className="prescription-info">
                    <p className="prescription-notice">處方已開立，無法修改</p>
                  </div>
                  <div className="prescription-display">
                    <h3>處方內容</h3>
                    <table className="prescription-table">
                      <thead>
                        <tr>
                          <th>藥品 ID</th>
                          <th>劑量</th>
                          <th>頻率</th>
                          <th>天數</th>
                          <th>數量</th>
                        </tr>
                      </thead>
                      <tbody>
                        {prescription.items.map((item: any, idx: number) => (
                          <tr key={idx}>
                            <td>{item.med_id}</td>
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
              {!prescription && (
                <>
                  <div className="prescription-items">
                    <h3>處方項目</h3>
                    {prescriptionForm.items.map((item, idx) => (
                      <div key={idx} className="prescription-item-form">
                        <input
                          type="number"
                          placeholder="藥品 ID"
                          value={item.med_id || ''}
                          onChange={(e) => {
                            const items = [...prescriptionForm.items];
                            const val = e.target.value;
                            const num = val === '' ? 0 : parseInt(val, 10);
                            items[idx].med_id = isNaN(num) ? 0 : num;
                            setPrescriptionForm({ ...prescriptionForm, items });
                          }}
                        />
                        <input
                          type="text"
                          placeholder="劑量"
                          value={item.dosage}
                          onChange={(e) => {
                            const items = [...prescriptionForm.items];
                            items[idx].dosage = e.target.value;
                            setPrescriptionForm({ ...prescriptionForm, items });
                          }}
                        />
                        <input
                          type="text"
                          placeholder="頻率"
                          value={item.frequency}
                          onChange={(e) => {
                            const items = [...prescriptionForm.items];
                            items[idx].frequency = e.target.value;
                            setPrescriptionForm({ ...prescriptionForm, items });
                          }}
                        />
                        <input
                          type="number"
                          placeholder="天數"
                          value={item.days || ''}
                          onChange={(e) => {
                            const items = [...prescriptionForm.items];
                            const val = e.target.value;
                            const num = val === '' ? 0 : parseInt(val, 10);
                            items[idx].days = isNaN(num) ? 0 : num;
                            setPrescriptionForm({ ...prescriptionForm, items });
                          }}
                        />
                        <input
                          type="number"
                          placeholder="數量"
                          value={item.quantity || ''}
                          onChange={(e) => {
                            const items = [...prescriptionForm.items];
                            const val = e.target.value;
                            const num = val === '' ? 0 : parseFloat(val);
                            items[idx].quantity = isNaN(num) ? 0 : num;
                            setPrescriptionForm({ ...prescriptionForm, items });
                          }}
                        />
                        <button
                          className="btn-small btn-danger"
                          onClick={() => {
                            const items = prescriptionForm.items.filter((_, i) => i !== idx);
                            setPrescriptionForm({ ...prescriptionForm, items });
                          }}
                        >
                          刪除
                        </button>
                      </div>
                    ))}
                    <button
                      className="btn btn-secondary"
                      onClick={() => {
                        setPrescriptionForm({
                          ...prescriptionForm,
                          items: [...prescriptionForm.items, { med_id: 1, dosage: '', frequency: '', days: 7, quantity: 1 }],
                        });
                      }}
                    >
                      新增項目
                    </button>
                  </div>
                  <button className="btn btn-primary" onClick={handleSavePrescription}>
                    開立處方
                  </button>
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
            <div className="history-tabs">
              <div className="history-item">
                <h3>就診記錄 ({patientHistory.encounters.length})</h3>
                {patientHistory.encounters.length === 0 ? (
                  <p>無過往就診記錄</p>
                ) : (
                  <div className="history-list">
                    {patientHistory.encounters.map((enc: any) => (
                      <div key={enc.enct_id} className="history-card">
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
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="history-item">
                <h3>診斷記錄 ({patientHistory.diagnoses.length})</h3>
                {patientHistory.diagnoses.length === 0 ? (
                  <p>無過往診斷記錄</p>
                ) : (
                  <div className="history-list">
                    {patientHistory.diagnoses.map((diag: any, idx: number) => (
                      <div key={idx} className="history-card">
                        <div className="history-card-header">
                          <strong>{diag.code_icd}</strong>
                          {diag.is_primary && <span className="primary-badge">主要診斷</span>}
                          <span>{new Date(diag.encounter_at).toLocaleDateString('zh-TW')}</span>
                        </div>
                        <div className="history-card-content">
                          {diag.description}
                        </div>
                        <div className="history-card-footer">
                          {diag.provider_name} - {diag.department_name || '未知科別'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="history-item">
                <h3>檢驗報告 ({patientHistory.lab_results.length})</h3>
                {patientHistory.lab_results.length === 0 ? (
                  <p>無過往檢驗報告</p>
                ) : (
                  <div className="history-list">
                    {patientHistory.lab_results.map((lab: any) => (
                      <div key={lab.lab_id} className="history-card">
                        <div className="history-card-header">
                          <strong>{lab.item_name}</strong>
                          <span>{lab.value} {lab.unit}</span>
                          {lab.abnormal_flag === 'H' && <span className="flag-high">高</span>}
                          {lab.abnormal_flag === 'L' && <span className="flag-low">低</span>}
                        </div>
                        <div className="history-card-content">
                          {lab.reported_at && (
                            <span>報告時間：{new Date(lab.reported_at).toLocaleString('zh-TW')}</span>
                          )}
                        </div>
                        <div className="history-card-footer">
                          {lab.provider_name} - {lab.department_name || '未知科別'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

