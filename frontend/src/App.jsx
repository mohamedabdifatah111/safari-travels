import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';

export default function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/destinations" element={<div className="p-12 text-center text-2xl font-bold">Destinations Page (Coming Next!)</div>} />
            <Route path="/packages" element={<div className="p-12 text-center text-2xl font-bold">Packages Page (Coming Next!)</div>} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}