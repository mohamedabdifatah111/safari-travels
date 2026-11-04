export const mockDestinations = [
  {
    id: 1,
    name: "Maasai Mara",
    description: "Experience the ultimate wildlife safari and witness the great migration.",
    image: "https://images.unsplash.com/photo-1516426122078-c23e76319801?auto=format&fit=crop&q=80&w=800"
  },
  {
    id: 2,
    name: "Diani Beach",
    description: "Relax on pristine white sandy beaches along the turquoise Indian Ocean.",
    image: "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&q=80&w=800"
  },
  {
    id: 3,
    name: "Amboseli",
    description: "Marvel at large elephant herds with the majestic backdrop of Mount Kilimanjaro.",
    image: "https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&q=80&w=800"
  }
];

export const mockPackages = [
  {
    id: 1,
    title: "5-Day Maasai Mara Wildlife Safari",
    destination: { id: 1, name: "Maasai Mara" },
    price: "850.00",
    currency: "USD",
    duration_days: 5,
    image: "https://images.unsplash.com/photo-1516426122078-c23e76319801?auto=format&fit=crop&q=80&w=800",
    description: "Join us for an unforgettable 5-day adventure across the Mara plains with expert guides, luxury tented camps, and game drives."
  },
  {
    id: 2,
    title: "4-Day Diani Beach Getaway",
    destination: { id: 2, name: "Diani Beach" },
    price: "500.00",
    currency: "USD",
    duration_days: 4,
    image: "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&q=80&w=800",
    description: "Unwind by the coast with beachside accommodation, snorkeling excursions, and sunset dhow cruises."
  },
  {
    id: 3,
    title: "3-Day Amboseli Elephant Expedition",
    destination: { id: 3, name: "Amboseli" },
    price: "450.00",
    currency: "USD",
    duration_days: 3,
    image: "https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&q=80&w=800",
    description: "Capture breathtaking views of Mount Kilimanjaro while tracking massive elephant families and diverse birdlife."
  }
];