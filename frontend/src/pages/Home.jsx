import React from 'react';
import { Link } from 'react-router-dom';
import { mockDestinations, mockPackages } from '../mocks/mockData';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      {/* Hero Section */}
      <div className="relative bg-emerald-900 text-white py-24 px-4 text-center">
        <div className="absolute inset-0 overflow-hidden opacity-30">
          <img 
            src="https://images.unsplash.com/photo-1516426122078-c23e76319801?auto=format&fit=crop&q=80&w=1600" 
            alt="Safari background" 
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative max-w-3xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
            Explore East Africa's Finest Adventures
          </h1>
          <p className="text-lg md:text-xl text-stone-200 mb-8">
            Discover breathtaking wildlife, pristine beaches, and custom-tailored travel packages.
          </p>
          <Link 
            to="/packages" 
            className="bg-amber-500 hover:bg-amber-600 text-stone-950 font-bold px-8 py-3 rounded-lg shadow-lg transition"
          >
            Explore Packages
          </Link>
        </div>
      </div>

      {/* Featured Destinations */}
      <section className="max-w-7xl mx-auto px-4 py-16 w-full">
        <h2 className="text-2xl font-bold text-stone-800 mb-8">Popular Destinations</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {mockDestinations.map((dest) => (
            <div key={dest.id} className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition">
              <img src={dest.image} alt={dest.name} className="w-full h-48 object-cover" />
              <div className="p-6">
                <h3 className="text-xl font-semibold text-stone-800 mb-2">{dest.name}</h3>
                <p className="text-stone-600 text-sm">{dest.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Featured Packages */}
      <section className="bg-stone-100 py-16 w-full">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-stone-800 mb-8">Featured Travel Packages</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {mockPackages.map((pkg) => (
              <div key={pkg.id} className="bg-white rounded-xl shadow-md overflow-hidden flex flex-col justify-between">
                <div>
                  <img src={pkg.image} alt={pkg.title} className="w-full h-48 object-cover" />
                  <div className="p-6">
                    <span className="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full">
                      {pkg.duration_days} Days
                    </span>
                    <h3 className="text-xl font-semibold text-stone-800 mt-3 mb-2">{pkg.title}</h3>
                    <p className="text-stone-600 text-sm line-clamp-2">{pkg.description}</p>
                  </div>
                </div>
                <div className="p-6 pt-0 flex items-center justify-between border-t border-stone-100 mt-4">
                  <span className="text-lg font-bold text-emerald-800">
                    {pkg.currency} {pkg.price}
                  </span>
                  <Link 
                    to={`/packages`} 
                    className="bg-emerald-800 hover:bg-emerald-900 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
                  >
                    View Details
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}