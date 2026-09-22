import { Navigate, Route, Routes } from "react-router-dom";
import ConverterPage from "./pages/ConverterPage.jsx";
import HomePage from "./pages/HomePage.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/convert" element={<ConverterPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
