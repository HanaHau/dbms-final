// 預約按鈕組件（客戶端組件）
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { patientApi } from '../services/api';
import './AppointmentButton.css';

interface AppointmentButtonProps {
  sessionId: number;
  disabled?: boolean;
  onSuccess?: () => void;
}

export const AppointmentButton: React.FC<AppointmentButtonProps> = ({
  sessionId,
  disabled = false,
  onSuccess,
}) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleClick = async () => {
    if (disabled || !user) return;

    try {
      await patientApi.createAppointment(user.user_id, sessionId);
      alert('掛號成功！');
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/patient/appointments');
      }
    } catch (err: any) {
      console.error('掛號錯誤:', err);
      const errorDetail = err.response?.data?.detail;
      alert(errorDetail || '掛號失敗，請稍後再試');
      // 若因名額已滿或其他併發錯誤導致掛號失敗，關閉錯誤提示後自動刷新頁面
      window.location.reload();
    }
  };

  return (
    <button
      className={`appointment-button ${disabled ? 'disabled' : ''}`}
      onClick={handleClick}
      disabled={disabled}
    >
      掛號
    </button>
  );
};
