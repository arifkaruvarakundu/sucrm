import React,{useState, useEffect} from 'react'
import TopCustomersChart from "../components/customers/topCustomers"
import CustomersTable from "../components/customers/customersTable"
import CustomerClassificationTables from "../components/customers/cutomerTableBasedOrderNo"
import CustomerSpendingClassificationTables from "../components/customers/CustomerSpendingClassificationTables";
import LowChurnCustomers from "../components/customers/CustomersWithLowChurnRisk";
import api from "../../api_config";
import axios from "axios";
import { useTranslation } from 'react-i18next'; 

function CustomerAnalysis() {
  const [customers, setCustomers] = useState([]);
  const [filteredCustomers, setFilteredCustomers] = useState([]);
  const [columns, setColumns] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  // Filters use `null` for "not set"
  const [orderFilter, setOrderFilter] = useState({ min: null, max: null });
  const [spendingFilter, setSpendingFilter] = useState({ min: null, max: null });

  const { t } = useTranslation("customerAnalysis");

  // 🔄 Fetch customers
  useEffect(() => {
    async function fetchCustomers() {
      try {
        const res = await api.get(`/customer-analysis/customers-table`);
        const list = Array.isArray(res.data?.customers) ? res.data.customers : [];
        const cols = Array.isArray(res.data?.columns) ? res.data.columns : (list[0] ? Object.keys(list[0]) : []);
        console.log("response of customers table:", list)
        setCustomers(list);
        setFilteredCustomers(list);
        setColumns(cols);

      } catch (err) {
        console.error("Error fetching customers", err);
      }
    }
    fetchCustomers();
  }, []);

  // 🔍 Filter when searchTerm changes
  useEffect(() => {
  const rawSearch = searchTerm.trim().toLowerCase();
  const digitSearch = rawSearch.replace(/\D/g, '');

  const filtered = (Array.isArray(customers) ? customers : [])
    // Ensure basic shape (name/phone optional-safe, but keep rows even if one missing)
    .filter((c) => typeof c === 'object' && c !== null)
    .filter((customer) => {
    // Generic text search across all string-like fields
    const textMatch = Object.values(customer || {})
      .filter((v) => typeof v === 'string')
      .some((v) => v.toLowerCase().includes(rawSearch));

    // Phone digit-only match on any field that looks like phone
    const phoneLike = (customer?.phone || customer?.mobile || customer?.contact || '').toString();
    const phoneDigits = phoneLike.replace(/\D/g, '');

    const isPhoneMatch = digitSearch && phoneDigits.includes(digitSearch);
    const passesSearch = !rawSearch || textMatch || isPhoneMatch;

    // Optional numeric filters if present
    const ordersRaw = customer.total_orders ?? customer.orders;
    const spendingRaw = customer.total_spending ?? customer.spent;
    const orders = ordersRaw === undefined || ordersRaw === null ? null : Number(ordersRaw);
    const spending = spendingRaw === undefined || spendingRaw === null ? null : Number(spendingRaw);

    // removed duplicate isPhoneMatch/passesSearch definitions that caused redeclare errors

    // ✅ Orders filter
    const passesOrderMin =
      orderFilter.min === null || (Number.isFinite(orders) && orders >= orderFilter.min);
    const passesOrderMax =
      orderFilter.max === null || (Number.isFinite(orders) && orders <= orderFilter.max);

    // ✅ Spending filter
    const passesSpendingMin =
      spendingFilter.min === null || (Number.isFinite(spending) && spending >= spendingFilter.min);
    const passesSpendingMax =
      spendingFilter.max === null || (Number.isFinite(spending) && spending <= spendingFilter.max);

    return (
      passesSearch &&
      passesOrderMin &&
      passesOrderMax &&
      passesSpendingMin &&
      passesSpendingMax
    );
  });

    setFilteredCustomers(filtered);
      }, [searchTerm, customers, orderFilter, spendingFilter]);

    const clearFilters = () => {
      setSearchTerm("");
      setOrderFilter({ min: null, max: null });
      setSpendingFilter({ min: null, max: null });
    };

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">{t("customer_analysis")}</h2>
      <TopCustomersChart/>

      {/* 🔍 Search Bar */}
      <div className="mb-6 max-w-xl">
        <input
          type="text"
          placeholder={t("search_by_name_or_phone")}
          className="w-full px-4 py-2 border rounded shadow-sm"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Filters */}
      {/* <div className="mb-6 max-w-3xl">
        <div className="bg-gradient-to-r from-green-100 to-green-200 border border-green-300 shadow-md rounded-2xl px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-green-800">{t("filter_customers")}</h3>
            <button
              onClick={clearFilters}
              className="text-sm bg-white px-3 py-1 rounded shadow-sm border hover:bg-gray-50"
            >
              {t("clear_filters")}
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4"> */}
            {/* Orders Min */}
            {/* <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t("orders")} ≥</label>
              <input
                type="number"
                min="0"
                className="w-full px-3 py-2 border rounded-lg shadow-sm"
                value={orderFilter.min ?? ""}
                placeholder={t("any")}
                onChange={(e) =>
                  setOrderFilter((prev) => ({
                    ...prev,
                    min: e.target.value === "" ? null : Number(e.target.value),
                  }))
                }
              />
            </div> */}

            {/* Orders Max */}
            {/* <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t("orders")} ≤</label>
              <input
                type="number"
                min="0"
                className="w-full px-3 py-2 border rounded-lg shadow-sm"
                value={orderFilter.max ?? ""}
                placeholder={t("any")}
                onChange={(e) =>
                  setOrderFilter((prev) => ({
                    ...prev,
                    max: e.target.value === "" ? null : Number(e.target.value),
                  }))
                }
              />
            </div> */}

            {/* Spending Min */}
            {/* <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t("spent")} ≥</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full px-3 py-2 border rounded-lg shadow-sm"
                value={spendingFilter.min ?? ""}
                placeholder={t("any")}
                onChange={(e) =>
                  setSpendingFilter((prev) => ({
                    ...prev,
                    min: e.target.value === "" ? null : Number(e.target.value),
                  }))
                }
              />
            </div> */}

            {/* Spending Max */}
            {/* <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t("spent")} ≤</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full px-3 py-2 border rounded-lg shadow-sm"
                value={spendingFilter.max ?? ""}
                placeholder={t("any")}
                onChange={(e) =>
                  setSpendingFilter((prev) => ({
                    ...prev,
                    max: e.target.value === "" ? null : Number(e.target.value),
                  }))
                }
              />
            </div> */}
          {/* </div>
        </div>
      </div> */}

      <CustomersTable customers={filteredCustomers} columns={columns}/>
      <div className="flex justify-center my-8">
        <div className="bg-gradient-to-r from-blue-100 to-blue-200 border border-blue-300 shadow-md rounded-2xl px-6 py-4 text-center w-full max-w-3xl">
          <h3 className="text-2xl font-bold text-blue-800 tracking-wide">
            {t("classification_by_orders")}
          </h3>
        </div>
      </div>

      <CustomerClassificationTables/>
      <div className="flex justify-center my-8">
        <div className="bg-gradient-to-r from-blue-100 to-blue-200 border border-blue-300 shadow-md rounded-2xl px-6 py-4 text-center w-full max-w-3xl">
          <h3 className="text-2xl font-bold text-blue-800 tracking-wide">
            {t("classification_by_spending")}
          </h3>
        </div>
      </div>
      
      <CustomerSpendingClassificationTables/>
      {/* <div className="flex justify-center my-8">
        <div className="bg-gradient-to-r from-blue-100 to-blue-200 border border-blue-300 shadow-md rounded-2xl px-6 py-4 text-center w-full max-w-3xl">
          <h3 className="text-2xl font-bold text-blue-800 tracking-wide">
            {t("low_churn_table")}
          </h3>
        </div>
      </div>
      <LowChurnCustomers/> */}
    </div>
  )
}

export default CustomerAnalysis