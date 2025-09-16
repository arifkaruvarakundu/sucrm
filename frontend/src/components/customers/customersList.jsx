import { useState, useEffect } from "react";
import axios from "axios";
import API_BASE_URL from "../../../api_config";

const CustomerList = ({ onSelectCustomers }) => {
  const [customers, setCustomers] = useState([]);
  const [selected, setSelected] = useState([]);
  const [filter, setFilter] = useState("");

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 20;

  useEffect(() => {
    axios.get(`${API_BASE_URL}/customers-table`)
      .then(res => setCustomers(res.data))
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    onSelectCustomers(selected);  // whenever selection changes, update parent
  }, [selected]);

  // Filtering
  const filteredCustomers = customers.filter(c =>
    c.user.toLowerCase().includes(filter.toLowerCase()) ||
    c.phone.includes(filter)
  );

  // Pagination calculations
  const totalPages = Math.ceil(filteredCustomers.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const currentCustomers = filteredCustomers.slice(startIndex, startIndex + rowsPerPage);

  // Selection logic
  const toggleSelect = (id) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    const allIds = filteredCustomers.map(c => c.id);
    setSelected(allIds);
  };

  const unselectAll = () => {
    setSelected([]);
  };

  const goToPrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const goToNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4 text-gray-800">Customers List</h2>

      {/* Search Bar */}
      <input
        type="text"
        placeholder="Search by name or phone..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="mb-4 p-2 border rounded w-full shadow-sm focus:ring-2 focus:ring-blue-400"
      />

      {/* Select / Unselect All Buttons */}
      <div className="mb-4 space-x-2">
        <button
          onClick={selectAll}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Select All
        </button>
        <button
          onClick={unselectAll}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Unselect All
        </button>
        {selected.length > 0 && (
          <span className="ml-4 text-gray-700">{selected.length} selected</span>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg shadow">
        <table className="w-full border-collapse">
          <thead className="bg-gray-100 text-gray-700">
            <tr>
              <th className="p-2 border"></th>
              <th className="p-2 border text-left">Name</th>
              <th className="p-2 border text-left">Phone</th>
            </tr>
          </thead>
          <tbody>
            {currentCustomers.map(c => (
              <tr
                key={c.id}
                className={`hover:bg-gray-800 ${selected.includes(c.id) ? "bg-blue-50" : ""}`}
              >
                <td className="p-2 border text-center">
                  <input
                    type="checkbox"
                    checked={selected.includes(c.id)}
                    onChange={() => toggleSelect(c.id)}
                  />
                </td>
                <td className="p-2 border">{c.user}</td>
                <td className="p-2 border">{c.phone}</td>
              </tr>
            ))}
            {currentCustomers.length === 0 && (
              <tr>
                <td colSpan="3" className="p-4 text-center text-gray-500">
                  No customers found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4 text-gray-700">
        <button
          onClick={goToPrevPage}
          disabled={currentPage === 1}
          className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300"
        >
          Previous
        </button>
        <span className="text-sm">
          Page {currentPage} of {totalPages}
        </span>
        <button
          onClick={goToNextPage}
          disabled={currentPage === totalPages}
          className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default CustomerList;
