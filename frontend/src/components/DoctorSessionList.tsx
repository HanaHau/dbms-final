// 醫師會話列表項組件
import React from 'react';
import { AppointmentButton } from './AppointmentButton';
import './DoctorSessionList.css';

export interface SessionForUI {
  sessionId: number;
  doctorName: string;
  date: string; // formatted "YYYY-MM-DD"
  weekdayLabel: string; // e.g. "星期一"
  startTime: string; // "08:00"
  endTime: string; // "12:00"
  capacity: number;
  remaining: number;
}

interface DoctorSessionListProps {
  session: SessionForUI;
  onAppointmentSuccess?: () => void;
}

export const DoctorSessionList: React.FC<DoctorSessionListProps> = ({
  session,
  onAppointmentSuccess,
}) => {
  const isAvailable = session.remaining > 0;

  return (
    <div className="doctor-session-item">
      <div className="doctor-session-content">
        <div className="doctor-session-info">
          <div className="doctor-session-name">{session.doctorName}</div>
          <div className="doctor-session-details">
            <span className="doctor-session-time">
              {session.startTime} - {session.endTime}
            </span>
            <span className="doctor-session-remaining">
              剩餘名額：{session.remaining} / {session.capacity}
            </span>
          </div>
        </div>
        <div className="doctor-session-action">
          <AppointmentButton
            sessionId={session.sessionId}
            disabled={!isAvailable}
            onSuccess={onAppointmentSuccess}
          />
        </div>
      </div>
    </div>
  );
};
