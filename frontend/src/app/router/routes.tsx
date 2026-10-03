import type { ReactElement } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { SettingsPage } from "../../pages/SettingsPage";
import DashboardPage from "../../pages/DashboardPage";
import UploadPage from "../../pages/UploadPage";
import ProcessingPage from "../../pages/ProcessingPage";
import LibraryPage from "../../pages/LibraryPage";
import DocumentDetailPage from "../../pages/DocumentDetailPage";
import QuestionsExplorerPage from "../../pages/QuestionsExplorerPage";
import QuestionDetailPage from "../../pages/QuestionDetailPage";
import ReviewCenterPage from "../../pages/ReviewCenterPage";
import ChaptersTopicsPage from "../../pages/ChaptersTopicsPage";
import PracticePage from "../../pages/PracticePage";
import PracticeSessionPage from "../../pages/PracticeSessionPage";
import PracticeResultsPage from "../../pages/PracticeResultsPage";
import AnalyticsPage from "../../pages/AnalyticsPage";
import SearchPage from "../../pages/SearchPage";
import FirstRunPage from "../../pages/FirstRunPage";
import { LoginPage } from "../../pages/LoginPage";
import { RegisterPage } from "../../pages/RegisterPage";
import { RequireAuth } from "./RequireAuth";

export function AppRoutes():ReactElement{
 return <Routes>
   <Route path="/login" element={<LoginPage/>}/>
   <Route path="/register" element={<RegisterPage/>}/>
   <Route element={<RequireAuth/>}>
     <Route path="/" element={<Navigate to="/dashboard" replace/>}/>
     <Route path="/dashboard" element={<DashboardPage/>}/>
     <Route path="/upload" element={<UploadPage/>}/>
     <Route path="/processing" element={<ProcessingPage/>}/>
     <Route path="/library" element={<LibraryPage/>}/>
     <Route path="/document" element={<DocumentDetailPage/>}/>
     <Route path="/questions" element={<QuestionsExplorerPage/>}/>
     <Route path="/question" element={<QuestionDetailPage/>}/>
     <Route path="/review" element={<ReviewCenterPage/>}/>
     <Route path="/chapters" element={<ChaptersTopicsPage/>}/>
     <Route path="/practice" element={<PracticePage/>}/>
     <Route path="/practice/session" element={<PracticeSessionPage/>}/>
     <Route path="/practice/results" element={<PracticeResultsPage/>}/>
     <Route path="/analytics" element={<AnalyticsPage/>}/>
     <Route path="/search" element={<SearchPage/>}/>
     <Route path="/first-run" element={<FirstRunPage/>}/>
     <Route path="/settings" element={<SettingsPage/>}/>
     <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
   </Route>
   <Route path="*" element={<Navigate to="/login" replace/>}/>
 </Routes>;
}