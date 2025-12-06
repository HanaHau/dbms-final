// 主應用程式
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Home } from './pages/Home';
import { PatientLogin } from './pages/patient/PatientLogin';
import { PatientRegister } from './pages/patient/PatientRegister';
import { PatientHome } from './pages/patient/PatientHome';
import { PatientAppointments } from './pages/patient/PatientAppointments';
import { PatientHistoryPage } from './pages/patient/PatientHistory';
import { PatientPayments } from './pages/patient/PatientPayments';
import { ProviderLogin } from './pages/provider/ProviderLogin';
import { ProviderRegister } from './pages/provider/ProviderRegister';
import { ProviderSessions } from './pages/provider/ProviderSessions';
import { ProviderAppointments } from './pages/provider/ProviderAppointments';
import { ProviderEncounter } from './pages/provider/ProviderEncounter';
import { Departments } from './pages/departments/Departments';
import { DepartmentDetail } from './pages/departments/DepartmentDetail';
import { DepartmentClickStats } from './pages/DepartmentClickStats';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          
          {/* 部門選擇頁面 */}
          <Route path="/departments" element={<Departments />} />
          <Route path="/departments/:slug" element={<DepartmentDetail />} />
          
          {/* 科別點擊統計 */}
          <Route path="/stats/department-clicks" element={<DepartmentClickStats />} />
          
          {/* 病人端路由 */}
          <Route path="/patient/login" element={<PatientLogin />} />
          <Route path="/patient/register" element={<PatientRegister />} />
          <Route path="/patient/home" element={<PatientHome />} />
          <Route path="/patient/appointments" element={<PatientAppointments />} />
          <Route path="/patient/history" element={<PatientHistoryPage />} />
          <Route path="/patient/payments" element={<PatientPayments />} />
          
          {/* 醫師端路由 */}
          <Route path="/provider/login" element={<ProviderLogin />} />
          <Route path="/provider/register" element={<ProviderRegister />} />
          <Route path="/provider/sessions" element={<ProviderSessions />} />
          <Route path="/provider/appointments/:sessionId" element={<ProviderAppointments />} />
          <Route path="/provider/encounter/:apptId" element={<ProviderEncounter />} />
          
          {/* 預設重定向 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
