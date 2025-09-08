import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { Articles } from '@/pages/Articles';
import { HotArticles } from '@/pages/HotArticles';
import { Tasks } from '@/pages/Tasks';
import { Sources } from '@/pages/Sources';
import { Monitor } from '@/pages/Monitor';
import { Stats } from '@/pages/Stats';
import { Admin } from '@/pages/Admin';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="articles" element={<Articles />} />
            <Route path="hot" element={<HotArticles />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="sources" element={<Sources />} />
            <Route path="monitor" element={<Monitor />} />
            <Route path="stats" element={<Stats />} />
            <Route path="admin" element={<Admin />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App
