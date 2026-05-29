import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import { MainLayout } from '@/app/layouts/main-layout';
import { SurveyListPage } from '@/features/surveys/pages/survey-list-page';
import { DashboardPage } from '@/features/dashboard/pages/dashboard-page';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <SurveyListPage />,
      },
      {
        path: ':level/:period',
        element: <DashboardPage />,
      },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
