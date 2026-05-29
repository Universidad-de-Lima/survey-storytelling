import { Outlet } from 'react-router-dom';

import { Header } from '@/shared/components/header';

export function MainLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="py-4 px-6 text-center text-sm text-gray-500 border-t">
        <p>Universidad de Lima — Encuestas de Satisfacción</p>
      </footer>
    </div>
  );
}
