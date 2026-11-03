const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

export const getDestinations = () => request("/destinations/");
export const getPackages = () => request("/packages/");
export const getPackage = (id) => request(`/packages/${id}/`);
export const createBooking = (data) =>
  request("/bookings/", { method: "POST", body: JSON.stringify(data) });