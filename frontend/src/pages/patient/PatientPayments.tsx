// 病人繳費頁面
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { Payment } from '../../types';
import './PatientPayments.css';

export const PatientPayments: React.FC = () => {
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [payingId, setPayingId] = useState<number | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'card' | 'insurer'>('card');
  const [invoiceNo, setInvoiceNo] = useState('');

  useEffect(() => {
    if (userType !== 'patient' || !user) {
      navigate('/patient/login');
      return;
    }
    loadPayments();
  }, [user, userType]);

  const loadPayments = async () => {
    if (!user) return;
    try {
      const data = await patientApi.listPayments(user.user_id);
      setPayments(data);
    } catch (err) {
      console.error('載入繳費記錄失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePay = async (paymentId: number) => {
    if (!user) return;
    try {
      await patientApi.payOnline(paymentId, user.user_id, {
        method: paymentMethod,
        invoice_no: invoiceNo || undefined,
      });
      alert('繳費成功！');
      setPayingId(null);
      setInvoiceNo('');
      loadPayments();
    } catch (err: any) {
      alert(err.response?.data?.detail || '繳費失敗');
    }
  };

  if (loading) return <Layout><div>載入中...</div></Layout>;

  return (
    <Layout>
      <div className="patient-payments">
        <h1>繳費記錄</h1>
        {payments.length === 0 ? (
          <p>目前沒有繳費記錄</p>
        ) : (
          <table className="payments-table">
            <thead>
              <tr>
                <th>繳費 ID</th>
                <th>金額</th>
                <th>付款方式</th>
                <th>發票號碼</th>
                <th>狀態</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
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
                    {payment.paid_at ? (
                      <span className="status-paid">已繳費</span>
                    ) : (
                      <span className="status-unpaid">未繳費</span>
                    )}
                  </td>
                  <td>
                    {!payment.paid_at && (
                      <>
                        {payingId === payment.payment_id ? (
                          <div className="pay-form">
                            <select
                              value={paymentMethod}
                              onChange={(e) => setPaymentMethod(e.target.value as any)}
                            >
                              <option value="cash">現金</option>
                              <option value="card">信用卡</option>
                              <option value="insurer">保險</option>
                            </select>
                            <input
                              type="text"
                              placeholder="發票號碼（選填）"
                              value={invoiceNo}
                              onChange={(e) => setInvoiceNo(e.target.value)}
                            />
                            <button
                              className="btn btn-primary btn-small"
                              onClick={() => handlePay(payment.payment_id)}
                            >
                              確認繳費
                            </button>
                            <button
                              className="btn btn-secondary btn-small"
                              onClick={() => {
                                setPayingId(null);
                                setInvoiceNo('');
                              }}
                            >
                              取消
                            </button>
                          </div>
                        ) : (
                          <button
                            className="btn btn-primary btn-small"
                            onClick={() => setPayingId(payment.payment_id)}
                          >
                            線上繳費
                          </button>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
};

