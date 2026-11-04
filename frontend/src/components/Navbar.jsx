import React from 'react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="bg-emerald-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold tracking-wide">
          safari<span className="text-amber-400">travels</span>
        </Link>
        <div className="space-x-6 font-medium">
          <Link to="/" className="hover:text-amber-300 transition">Home</Link>
          <Link to="/destinations" className="hover:text-amber-300 transition">Destinations</Link>
          <Link to="/packages" className="hover:text-amber-300 transition">Packages</Link>
        </div>
      </div>
    </nav>
  );
}