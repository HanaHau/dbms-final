// 病人歷史記錄頁面
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { PatientHistory } from '../../types';
import './PatientHistory.css';

export const PatientHistoryPage: React.FC = () => {
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [history, setHistory] = useState<PatientHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'encounters' | 'prescriptions' | 'lab-results' | 'payments'>('encounters');

  useEffect(() => {
    if (userType !== 'patient' || !user) {
      navigate('/patient/login');
      return;
    }
    loadHistory();
  }, [user, userType]);

  const loadHistory = async () => {
    if (!user) return;
    try {
      const data = await patientApi.getHistory(user.user_id);
      setHistory(data);
    } catch (err) {
      console.error('載入歷史記錄失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Layout><div>載入中...</div></Layout>;
  if (!history) return <Layout><div>沒有歷史記錄</div></Layout>;

  return (
    <Layout>
      <div className="patient-history">
        <h1>就診記錄</h1>
        <div className="tabs">
          <button
            className={activeTab === 'encounters' ? 'active' : ''}
            onClick={() => setActiveTab('encounters')}
          >
            就診記錄 ({history.encounters.length})
          </button>
          <button
            className={activeTab === 'prescriptions' ? 'active' : ''}
            onClick={() => setActiveTab('prescriptions')}
          >
            處方箋 ({history.prescriptions.length})
          </button>
          <button
            className={activeTab === 'lab-results' ? 'active' : ''}
            onClick={() => setActiveTab('lab-results')}
          >
            檢驗結果 ({history.lab_results.length})
          </button>
          <button
            className={activeTab === 'payments' ? 'active' : ''}
            onClick={() => setActiveTab('payments')}
          >
            繳費記錄 ({history.payments.length})
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'encounters' && (
            <div className="encounters-list">
              {history.encounters.length === 0 ? (
                <p>沒有就診記錄</p>
              ) : (
                history.encounters.map((encounter) => (
                  <div key={encounter.enct_id} className="encounter-card">
                    <div className="encounter-header">
                      <h3>就診日期: {new Date(encounter.encounter_at).toLocaleDateString()}</h3>
                      <span className={`status-badge status-${encounter.status === 1 ? 'draft' : 'final'}`}>
                        {encounter.status === 1 ? '草稿' : '定稿'}
                      </span>
                    </div>
                    {encounter.chief_complaint && (
                      <div className="encounter-field">
                        <strong>主訴:</strong> {encounter.chief_complaint}
                      </div>
                    )}
                    {encounter.subjective && (
                      <div className="encounter-field">
                        <strong>主觀描述:</strong> {encounter.subjective}
                      </div>
                    )}
                    {encounter.assessment && (
                      <div className="encounter-field">
                        <strong>評估:</strong> {encounter.assessment}
                      </div>
                    )}
                    {encounter.plan && (
                      <div className="encounter-field">
                        <strong>計畫:</strong> {encounter.plan}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'prescriptions' && (
            <div className="prescriptions-list">
              {history.prescriptions.length === 0 ? (
                <p>沒有處方記錄</p>
              ) : (
                history.prescriptions.map((prescription) => (
                  <div key={prescription.presc_id} className="prescription-card">
                    <h3>處方箋 #{prescription.presc_id}</h3>
                    <div className="prescription-items">
                      {prescription.items.map((item, idx) => (
                        <div key={idx} className="prescription-item">
                          <strong>{item.med_name}</strong>
                          <div>
                            劑量: {item.dosage || 'N/A'} | 頻率: {item.frequency || 'N/A'} | 
                            天數: {item.days} | 數量: {item.quantity}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'lab-results' && (
            <div className="lab-results-list">
              {history.lab_results.length === 0 ? (
                <p>沒有檢驗結果</p>
              ) : (
                <table className="lab-results-table">
                  <thead>
                    <tr>
                      <th>項目名稱</th>
                      <th>數值</th>
                      <th>單位</th>
                      <th>參考範圍</th>
                      <th>異常標記</th>
                      <th>報告日期</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.lab_results.map((result) => (
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
                          {!result.abnormal_flag && 'N/A'}
                        </td>
                        <td>{new Date(result.reported_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {activeTab === 'payments' && (
            <div className="payments-list">
              {history.payments.length === 0 ? (
                <p>沒有繳費記錄</p>
              ) : (
                <table className="payments-table">
                  <thead>
                    <tr>
                      <th>繳費 ID</th>
                      <th>金額</th>
                      <th>付款方式</th>
                      <th>發票號碼</th>
                      <th>繳費日期</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.payments.map((payment) => (
                      <tr key={payment.payment_id}>
                        <td>{payment.payment_id}</td>
                        <td>NT$ {payment.amount.toLocaleString()}</td>
                        <td>
                          {payment.method === 'cash' && '現金'}
                          {payment.method === 'card' && '信用卡'}
                          {payment.method === 'insurer' && '保險'}
                        </td>
                        <td>{payment.invoice_no || 'N/A'}</td>
                        <td>
                          {payment.paid_at
                            ? new Date(payment.paid_at).toLocaleDateString()
                            : '未繳費'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

