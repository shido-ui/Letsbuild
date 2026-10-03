import type { ReactElement } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { LoginPage } from "../../pages/LoginPage";
import { RegisterPage } from "../../pages/RegisterPage";
import { SettingsPage } from "../../pages/SettingsPage";
import { DashboardPage } from "../../pages/DashboardPage";
import { UploadPage } from "../../pages/UploadPage";
import { ProcessingPage } from "../../pages/ProcessingPage";
import { LibraryPage } from "../../pages/LibraryPage";
import { ChaptersPage } from "../../pages/ChaptersPage";
import { ReviewPage } from "../../pages/ReviewPage";
import { SearchPage } from "../../pages/SearchPage";
import { AnalyticsPage } from "../../pages/AnalyticsPage";
import { PracticePage } from "../../pages/PracticePage";
import { PracticeSessionPage } from "../../pages/PracticeSessionPage";
import { PracticeResultsPage } from "../../pages/PracticeResultsPage";
import { SourceDetailPage } from "../../pages/SourceDetailPage";
import { FirstRunPage } from "../../pages/FirstRunPage";
import { useAppStore } from "../store/useAppStore";

function Protected({ children }: { children: ReactElement }) {
  const token = useAppStore((s) => s.token);
  return token ? children : <Navigate to="/login" replace />;
}

export function AppRoutes(): ReactElement {
 return <Routes>
  <Route path="/login" element={<LoginPage/>}/><Route path="/register" element={<RegisterPage/>}/>
  <Route path="/" element={<Navigate to="/dashboard" replace/>}/>
  <Route path="/dashboard" element={<Protected><DashboardPage/></Protected>}/>
  <Route path="/upload" element={<Protected><UploadPage/></Protected>}/>
  <Route path="/processing/:id" element={<Protected><ProcessingPage/></Protected>}/>
  <Route path="/processing" element={<Protected><ProcessingPage/></Protected>}/>
  <Route path="/library" element={<Protected><LibraryPage/></Protected>}/>
  <Route path="/document/:id" element={<Protected><SourceDetailPage kind="document"/></Protected>}/>
  <Route path="/document" element={<Protected><LibraryPage/></Protected>}/>
  <Route path="/questions" element={<Protected><SearchPage/></Protected>}/>
  <Route path="/question/:id" element={<Protected><SourceDetailPage kind="question"/></Protected>}/>
  <Route path="/question" element={<Protected><SearchPage/></Protected>}/>
  <Route path="/review" element={<Protected><ReviewPage/></Protected>}/>
  <Route path="/chapters" element={<Protected><ChaptersPage/></Protected>}/>
  <Route path="/practice" element={<Protected><PracticePage/></Protected>}/>
  <Route path="/practice/session/:id" element={<Protected><PracticeSessionPage/></Protected>}/>
  <Route path="/practice/results/:id" element={<Protected><PracticeResultsPage/></Protected>}/>
  <Route path="/practice/session" element={<Protected><PracticePage/></Protected>}/>
  <Route path="/practice/results" element={<Protected><PracticePage/></Protected>}/>
  <Route path="/analytics" element={<Protected><AnalyticsPage/></Protected>}/>
  <Route path="/search" element={<Protected><SearchPage/></Protected>}/>
  <Route path="/first-run" element={<Protected><FirstRunPage/></Protected>}/>
  <Route path="/settings" element={<SettingsPage/>}/>
  <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
 </Routes>;
}
