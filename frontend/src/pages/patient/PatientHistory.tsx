// 病人歷史記錄頁面 - 以就診為中心的整合式介面
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { PatientHistory, Visit, Encounter, Prescription, LabResult, Payment, Diagnosis } from '../../types';
import { getPeriodDisplayName } from '../../lib/periodUtils';
import './PatientHistory.css';

export const PatientHistoryPage: React.FC = () => {
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [history, setHistory] = useState<PatientHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedVisits, setExpandedVisits] = useState<Set<number>>(new Set());

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

  // 格式化日期顯示：2025/2/26（四）
  const formatDateDisplay = (dateStr: string): string => {
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    const weekday = weekdays[date.getDay()];
    return `${year}/${month}/${day}（${weekday}）`;
  };

  // 將數據整合為以就診為中心的結構
  const visits: Visit[] = useMemo(() => {
    if (!history) return [];

    const visitMap = new Map<number, Visit>();

    // 處理就診記錄
    history.encounters.forEach((encounter: Encounter) => {
      visitMap.set(encounter.enct_id, {
        enct_id: encounter.enct_id,
        encounter_at: encounter.encounter_at,
        session_date: encounter.session_date,
        session_period: encounter.session_period,
        provider_name: encounter.provider_name || '未知醫師',
        department_name: encounter.department_name || '未知科別',
        chief_complaint: encounter.chief_complaint,
        subjective: encounter.subjective,
        assessment: encounter.assessment,
        plan: encounter.plan,
        diagnoses: [],
        prescription: undefined,
        lab_results: [],
        payment: undefined,
      });
    });

    // 處理診斷
    if (history.diagnoses) {
      history.diagnoses.forEach((diagnosis: Diagnosis) => {
        const visit = visitMap.get(diagnosis.enct_id);
        if (visit) {
          visit.diagnoses.push(diagnosis);
        }
      });
    }

    // 處理處方
    history.prescriptions.forEach((prescription: Prescription) => {
      const visit = visitMap.get(prescription.enct_id);
      if (visit) {
        visit.prescription = prescription;
      }
    });

    // 處理檢驗結果
    history.lab_results.forEach((labResult: LabResult) => {
      const visit = visitMap.get(labResult.enct_id);
      if (visit) {
        visit.lab_results.push(labResult);
      }
    });

    // 處理繳費記錄
    history.payments.forEach((payment: Payment) => {
      const visit = visitMap.get(payment.enct_id);
      if (visit) {
        visit.payment = payment;
      }
    });

    return Array.from(visitMap.values());
  }, [history]);

  // 排序就診記錄：今日 → 未來 → 過去（由近到遠）
  const sortedVisits = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const todayVisits: Visit[] = [];
    const futureVisits: Visit[] = [];
    const pastVisits: Visit[] = [];

    visits.forEach((visit) => {
      const visitDate = new Date(visit.encounter_at);
      visitDate.setHours(0, 0, 0, 0);

      if (visitDate.getTime() === today.getTime()) {
        todayVisits.push(visit);
      } else if (visitDate > today) {
        futureVisits.push(visit);
      } else {
        pastVisits.push(visit);
      }
    });

    // 排序：未來由近到遠，過去由近到遠
    futureVisits.sort((a, b) => 
      new Date(a.encounter_at).getTime() - new Date(b.encounter_at).getTime()
    );
    pastVisits.sort((a, b) => 
      new Date(b.encounter_at).getTime() - new Date(a.encounter_at).getTime()
    );

    return [...todayVisits, ...futureVisits, ...pastVisits];
  }, [visits]);

  // 切換展開/收合
  const toggleVisit = (enctId: number) => {
    const newExpanded = new Set(expandedVisits);
    if (newExpanded.has(enctId)) {
      newExpanded.delete(enctId);
    } else {
      newExpanded.add(enctId);
    }
    setExpandedVisits(newExpanded);
  };

  // 獲取診斷摘要（主要診斷）
  const getDiagnosisSummary = (visit: Visit): string => {
    const primaryDiagnosis = visit.diagnoses.find(d => d.is_primary);
    if (primaryDiagnosis) {
      // 確保 description 不是空字串，優先使用 description
      const desc = primaryDiagnosis.description?.trim();
      if (desc && desc.length > 0) {
        return desc;
      }
      const name = primaryDiagnosis.disease_name?.trim();
      if (name && name.length > 0) {
        return name;
      }
      return '無';
    }
    if (visit.diagnoses.length > 0) {
      const desc = visit.diagnoses[0].description?.trim();
      if (desc && desc.length > 0) {
        return desc;
      }
      const name = visit.diagnoses[0].disease_name?.trim();
      if (name && name.length > 0) {
        return name;
      }
      return '無';
    }
    return visit.assessment || '無';
  };

  // 計算異常檢驗數量
  const getAbnormalLabCount = (visit: Visit): number => {
    return visit.lab_results.filter(lab => lab.abnormal_flag === 'H' || lab.abnormal_flag === 'L').length;
  };

  if (loading) return <Layout><div>載入中...</div></Layout>;
  if (!history) return <Layout><div>沒有歷史記錄</div></Layout>;

  return (
    <Layout>
      <div className="patient-history">
        <h1>就診記錄</h1>

        {sortedVisits.length === 0 ? (
          <div className="no-visits">
            <p>目前沒有就診記錄</p>
          </div>
        ) : (
          <div className="visits-timeline">
            {sortedVisits.map((visit) => {
              const isExpanded = expandedVisits.has(visit.enct_id);
              const periodDisplay = visit.session_period ? getPeriodDisplayName(visit.session_period) : '';
              const dateDisplay = formatDateDisplay(visit.encounter_at);
              const prescriptionCount = visit.prescription?.items.length || 0;
              const labCount = visit.lab_results.length;
              const abnormalLabCount = getAbnormalLabCount(visit);
              const diagnosisSummary = getDiagnosisSummary(visit);

              return (
                <div key={visit.enct_id} className={`visit-card ${isExpanded ? 'expanded' : ''}`}>
                  {/* 就診卡片摘要 */}
                  <div className="visit-card-header" onClick={() => toggleVisit(visit.enct_id)}>
                    <div className="visit-card-main">
                      <h3 className="visit-date">
                        {dateDisplay} {periodDisplay && `· ${periodDisplay}`}
                      </h3>
                      <div className="visit-meta">
                        <span className="visit-dept">{visit.department_name}</span>
                        <span className="visit-separator">·</span>
                        <span className="visit-provider">{visit.provider_name}</span>
                      </div>
                    </div>
                    <div className="visit-card-summary">
                      <div className="summary-item">
                        <span className="summary-label">症狀摘要：</span>
                        <span className="summary-value">{visit.chief_complaint || '無'}</span>
                      </div>
                      <div className="summary-item">
                        <span className="summary-label">診斷摘要：</span>
                        <span className="summary-value">{diagnosisSummary}</span>
                      </div>
                      <div className="summary-stats">
                        {prescriptionCount > 0 && (
                          <span className="stat-badge">處方：{prescriptionCount} 項</span>
                        )}
                        {labCount > 0 && (
                          <span className={`stat-badge ${abnormalLabCount > 0 ? 'has-abnormal' : ''}`}>
                            檢驗：{labCount} 項{abnormalLabCount > 0 ? `（${abnormalLabCount} 項異常）` : ''}
                          </span>
                        )}
                        {visit.payment && (
                          <span className="stat-badge">繳費：NT$ {visit.payment.amount.toLocaleString()}</span>
                        )}
                      </div>
                    </div>
                    <div className="visit-card-toggle">
                      <span className="toggle-icon">{isExpanded ? '▼' : '▶'}</span>
                      <span className="toggle-text">{isExpanded ? '收起' : '查看詳情'}</span>
                    </div>
                  </div>

                  {/* 展開的詳情 */}
                  {isExpanded && (
                    <div className="visit-card-details">
                      {/* 就診紀錄（SOAP） */}
                      <div className="visit-section">
                        <h4 className="section-title">🩺 就診紀錄</h4>
                        {visit.chief_complaint && (
                          <div className="soap-field">
                            <strong>主訴：</strong>
                            <p>{visit.chief_complaint}</p>
                          </div>
                        )}
                        {visit.subjective && (
                          <div className="soap-field">
                            <strong>現病史：</strong>
                            <p>{visit.subjective}</p>
                          </div>
                        )}
                        {visit.assessment && (
                          <div className="soap-field">
                            <strong>檢查及評估：</strong>
                            <p>{visit.assessment}</p>
                          </div>
                        )}
                        {visit.plan && (
                          <div className="soap-field plan-field">
                            <strong>醫師計畫：</strong>
                            <p>{visit.plan}</p>
                          </div>
                        )}
                      </div>

                      {/* 診斷 */}
                      {visit.diagnoses.length > 0 && (
                        <div className="visit-section">
                          <h4 className="section-title">📋 診斷</h4>
                          <div className="diagnoses-list">
                            {visit.diagnoses.map((diagnosis, idx) => {
                              // 確保 description 不是空字串，優先使用 description
                              const desc = diagnosis.description?.trim();
                              const name = diagnosis.disease_name?.trim();
                              const displayText = (desc && desc.length > 0) 
                                ? desc 
                                : (name && name.length > 0) 
                                  ? name 
                                  : '無診斷描述';
                              
                              return (
                                <div key={idx} className={`diagnosis-item ${diagnosis.is_primary ? 'primary' : ''}`}>
                                  <span className="diagnosis-name">
                                    {displayText}
                                  </span>
                                  {diagnosis.is_primary && <span className="primary-badge">主要診斷</span>}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* 處方資訊 */}
                      {visit.prescription && visit.prescription.items.length > 0 && (
                        <div className="visit-section">
                          <h4 className="section-title">💊 處方資訊</h4>
                          <div className="prescription-items">
                            {visit.prescription.items.map((item, idx) => (
                              <div key={idx} className="prescription-item">
                                <div className="med-name">{item.med_name}</div>
                                <div className="med-details">
                                  劑量：{item.dosage || 'N/A'} | 
                                  頻率：{item.frequency || 'N/A'} | 
                                  天數：{item.days} | 
                                  數量：{item.quantity}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 檢驗結果 */}
                      {visit.lab_results.length > 0 && (
                        <div className="visit-section">
                          <h4 className="section-title">🧪 檢驗結果</h4>
                          <table className="lab-results-table">
                            <thead>
                              <tr>
                                <th>檢驗項目</th>
                                <th>數值</th>
                                <th>單位</th>
                                <th>參考範圍</th>
                                <th>異常標記</th>
                              </tr>
                            </thead>
                            <tbody>
                              {visit.lab_results.map((result) => (
                                <tr 
                                  key={result.lab_id}
                                  className={result.abnormal_flag === 'H' || result.abnormal_flag === 'L' ? 'abnormal' : ''}
                                >
                                  <td>{result.item_name}</td>
                                  <td>{result.value || 'N/A'}</td>
                                  <td>{result.unit || 'N/A'}</td>
                                  <td>
                                    {result.ref_low && result.ref_high
                                      ? `${result.ref_low} - ${result.ref_high}`
                                      : 'N/A'}
                                  </td>
                                  <td>
                                    {result.abnormal_flag === 'H' && <span className="flag-high">↑ 高</span>}
                                    {result.abnormal_flag === 'L' && <span className="flag-low">↓ 低</span>}
                                    {result.abnormal_flag === 'N' && <span className="flag-normal">正常</span>}
                                    {!result.abnormal_flag && 'N/A'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {/* 繳費明細 */}
                      {visit.payment && (
                        <div className="visit-section">
                          <h4 className="section-title">💳 繳費明細</h4>
                          <div className="payment-details">
                            <div className="payment-row">
                              <span className="payment-label">金額：</span>
                              <span className="payment-value">NT$ {visit.payment.amount.toLocaleString()}</span>
                            </div>
                            <div className="payment-row">
                              <span className="payment-label">付款方式：</span>
                              <span className="payment-value">
                                {visit.payment.method === 'cash' && '現金'}
                                {visit.payment.method === 'card' && '信用卡'}
                                {visit.payment.method === 'insurer' && '保險'}
                              </span>
                            </div>
                            {visit.payment.invoice_no && (
                              <div className="payment-row">
                                <span className="payment-label">發票號碼：</span>
                                <span className="payment-value">{visit.payment.invoice_no}</span>
                              </div>
                            )}
                            {visit.payment.paid_at && (
                              <div className="payment-row">
                                <span className="payment-label">繳費日期：</span>
                                <span className="payment-value">
                                  {formatDateDisplay(visit.payment.paid_at)}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Layout>
  );
};
