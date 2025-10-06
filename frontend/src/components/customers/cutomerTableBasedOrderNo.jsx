import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Table from "../table/Table";
import api from "../../../api_config";
import { useTranslation } from "react-i18next";

const CustomerClassificationTables = () => {
  const [groupedCustomers, setGroupedCustomers] = useState({});
  const [allCustomers, setAllCustomers] = useState([]);
  const [ranges, setRanges] = useState({
    Loyal: { min: 16, max: null },
    Frequent: { min: 10, max: 15 },
    Occasional: { min: 5, max: 9 },
    New: { min: 1, max: 4 },
    Dead: { min: null, max: 0 },
    NoOrders: { equals: 0 }
  });
  const navigate = useNavigate();
  const { t } = useTranslation("customerAnalysis");

  const tableHead = ["customer_name", "total_orders", "Total_amount"];

  const renderHead = (item, index) => <th key={index}>{t(item)}</th>;

  const renderBody = (item, index, navigate) => (
    <tr
      key={index}
      onClick={() => navigate(`/customer-details/${item.customer_id}`)}
      style={{ cursor: "pointer" }}
    >
      <td>{item.customer_name}</td>
      <td>{item.order_count}</td>
      <td>{item.total_spending?.toFixed(2)}</td>
      {/* <td>{item.segment}</td> */}
    </tr>
  );

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const res = await api.get(`/customer-analysis/full-customer-classification`);
        const data = Array.isArray(res.data) ? res.data : [];
        setAllCustomers(data);
      } catch (error) {
        console.error("Failed to fetch classified customers:", error);
        setAllCustomers([]);
      }
    };

    fetchCustomers();
  }, []);

  useEffect(() => {
    // Classify locally using order_count and user-defined ranges
    const bucketed = allCustomers.reduce((acc, item) => {
      const count = Number(item.order_count ?? 0);
      let key = 'Unclassified';

      if (ranges.Loyal.min !== null && count >= ranges.Loyal.min) key = 'Loyal';
      else if (
        ranges.Frequent.min !== null && count >= ranges.Frequent.min &&
        ranges.Frequent.max !== null && count <= ranges.Frequent.max
      ) key = 'Frequent';
      else if (
        ranges.Occasional.min !== null && count >= ranges.Occasional.min &&
        ranges.Occasional.max !== null && count <= ranges.Occasional.max
      ) key = 'Occasional';
      else if (
        ranges.New.min !== null && count >= ranges.New.min &&
        ranges.New.max !== null && count <= ranges.New.max
      ) key = 'New';
      else if (
        (ranges.Dead.min === null || count >= ranges.Dead.min) &&
        (ranges.Dead.max === null || count <= ranges.Dead.max)
      ) key = 'Dead';
      else if (count === (ranges.NoOrders.equals ?? 0)) key = 'No Orders';

      if (!acc[key]) acc[key] = [];
      acc[key].push(item);
      return acc;
    }, {});

    if (bucketed['New']) {
      bucketed['New'].sort((a, b) => new Date(b.last_order_date) - new Date(a.last_order_date));
    }
    Object.keys(bucketed).forEach((k) => {
      if (k !== 'New') bucketed[k].sort((a, b) => b.order_count - a.order_count);
    });

    setGroupedCustomers(bucketed);
  }, [allCustomers, ranges]);

  const classificationOrder = [
    { key: "Loyal", label: t("customer_classification.Loyal.label") || 'Loyal' },
    { key: "Frequent", label: t("customer_classification.Frequent.label") || 'Frequent' },
    { key: "Occasional", label: t("customer_classification.Occasional.label") || 'Occasional' },
    { key: "New", label: t("customer_classification.New.label") || 'New' },
    { key: "Dead", label: t("customer_classification.Dead.label") || 'Dead' },
    { key: "No Orders", label: t("customer_classification.NoOrders.label") || 'No Orders' },
  ];

  const onRangeChange = (group, bound, value) => {
    setRanges((prev) => ({
      ...prev,
      [group]: {
        ...prev[group],
        [bound]: value === '' ? null : Number(value)
      }
    }));
  };

  return (
    <div className="row">
  {classificationOrder.map(({ key, label }) =>
    groupedCustomers[key]?.length > 0 ? (
      <div className="col-6" key={key}>
        <div className="card">
          <div className="bg-gradient-to-r from-indigo-100 to-indigo-200 border border-indigo-300 rounded-xl px-4 py-3 mb-4 shadow-sm text-center">
            <h3 className="text-xl font-semibold text-indigo-800 tracking-wide">
              {label} <span className="text-sm text-indigo-600">({groupedCustomers[key].length})</span>
            </h3>
            <div className="text-sm text-indigo-700 mt-2 flex items-center justify-center gap-2">
              {key === 'Loyal' && (
                <>
                  <label>Min</label>
                  <input type="number" value={ranges.Loyal.min ?? ''} onChange={(e) => onRangeChange('Loyal','min', e.target.value)} />
                </>
              )}
              {key === 'Frequent' && (
                <>
                  <label>Min</label>
                  <input type="number" value={ranges.Frequent.min ?? ''} onChange={(e) => onRangeChange('Frequent','min', e.target.value)} />
                  <label>Max</label>
                  <input type="number" value={ranges.Frequent.max ?? ''} onChange={(e) => onRangeChange('Frequent','max', e.target.value)} />
                </>
              )}
              {key === 'Occasional' && (
                <>
                  <label>Min</label>
                  <input type="number" value={ranges.Occasional.min ?? ''} onChange={(e) => onRangeChange('Occasional','min', e.target.value)} />
                  <label>Max</label>
                  <input type="number" value={ranges.Occasional.max ?? ''} onChange={(e) => onRangeChange('Occasional','max', e.target.value)} />
                </>
              )}
              {key === 'New' && (
                <>
                  <label>Min</label>
                  <input type="number" value={ranges.New.min ?? ''} onChange={(e) => onRangeChange('New','min', e.target.value)} />
                  <label>Max</label>
                  <input type="number" value={ranges.New.max ?? ''} onChange={(e) => onRangeChange('New','max', e.target.value)} />
                </>
              )}
              {key === 'Dead' && (
                <>
                  <label>Min</label>
                  <input type="number" value={ranges.Dead.min ?? ''} onChange={(e) => onRangeChange('Dead','min', e.target.value)} />
                  <label>Max</label>
                  <input type="number" value={ranges.Dead.max ?? ''} onChange={(e) => onRangeChange('Dead','max', e.target.value)} />
                </>
              )}
              {key === 'No Orders' && (
                <>
                  <label>Equals</label>
                  <input type="number" value={ranges.NoOrders.equals ?? ''} onChange={(e) => onRangeChange('NoOrders','equals', e.target.value)} />
                </>
              )}
            </div>
          </div>
          <div className="card__body">
            <Table
              limit="10"
              headData={tableHead}
              renderHead={renderHead}
              bodyData={groupedCustomers[key]}
              renderBody={(item, index) =>
                renderBody(item, index, navigate)
              }
            />
          </div>
        </div>
      </div>
    ) : null
  )}
</div>
  );
};

export default CustomerClassificationTables;
