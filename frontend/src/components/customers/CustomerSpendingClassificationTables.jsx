import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Table from "../table/Table";
import axios from "axios";
import api from "../../../api_config";
import { useTranslation } from "react-i18next";

const CustomerSpendingClassificationTables = () => {
  const [groupedCustomers, setGroupedCustomers] = useState({});
  const [allCustomers, setAllCustomers] = useState([]);
  const [ranges, setRanges] = useState({
    VIP: { min: 1000, max: null },
    'High Spender': { min: 500, max: 999.99 },
    'Medium Spender': { min: 200, max: 499.99 },
    'Low Spender': { min: 0, max: 199.99 }
  });

  const { t } = useTranslation("customerAnalysis");
  const navigate = useNavigate();

  const tableHead = ["customer_name", "total_orders", "total_spending", "churn_risk"];

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
    {/* <td>{item.churn_risk}</td> */}

  </tr>
  );

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const res = await api.get(`/customer-analysis/full-customer-classification`);
        const data = Array.isArray(res.data) ? res.data : [];
        setAllCustomers(data);
      } catch (error) {
        console.error("Failed to fetch spending classified customers:", error);
        setAllCustomers([]);
      }
    };

    fetchCustomers();
  }, []);

  useEffect(() => {
    const bucketed = allCustomers.reduce((acc, item) => {
      const spend = Number(item.total_spending ?? 0);
      let key = 'Unclassified';

      if (ranges.VIP.min !== null && spend >= ranges.VIP.min) key = 'VIP';
      else if (
        ranges['High Spender'].min !== null && spend >= ranges['High Spender'].min &&
        ranges['High Spender'].max !== null && spend <= ranges['High Spender'].max
      ) key = 'High Spender';
      else if (
        ranges['Medium Spender'].min !== null && spend >= ranges['Medium Spender'].min &&
        ranges['Medium Spender'].max !== null && spend <= ranges['Medium Spender'].max
      ) key = 'Medium Spender';
      else if (
        ranges['Low Spender'].min !== null && spend >= ranges['Low Spender'].min &&
        ranges['Low Spender'].max !== null && spend <= ranges['Low Spender'].max
      ) key = 'Low Spender';

      if (!acc[key]) acc[key] = [];
      acc[key].push(item);
      return acc;
    }, {});

    Object.keys(bucketed).forEach((k) => {
      bucketed[k].sort((a, b) => (b.total_spending ?? 0) - (a.total_spending ?? 0));
    });

    setGroupedCustomers(bucketed);
  }, [allCustomers, ranges]);

  const classificationOrder = [
    { key: "VIP", label: t("customer_spending_classification.VIP.label") || 'VIP' },
    { key: "High Spender", label: t("customer_spending_classification.HighSpender.label") || 'High Spender' },
    { key: "Medium Spender", label: t("customer_spending_classification.MediumSpender.label") || 'Medium Spender' },
    { key: "Low Spender", label: t("customer_spending_classification.LowSpender.label") || 'Low Spender' }
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
              <div className="bg-gradient-to-r from-green-100 to-green-200 border border-green-300 rounded-xl px-4 py-3 mb-4 shadow-sm text-center">
                <h3 className="text-xl font-semibold text-green-800 tracking-wide">
                  {label} <span className="text-sm text-green-700">({groupedCustomers[key].length})</span>
                </h3>
                <div className="text-sm text-green-700 mt-2 flex items-center justify-center gap-2">
                  {key === 'VIP' && (
                    <>
                      <label>Min</label>
                      <input type="number" step="0.01" value={ranges['VIP'].min ?? ''} onChange={(e) => onRangeChange('VIP','min', e.target.value)} />
                    </>
                  )}
                  {key === 'High Spender' && (
                    <>
                      <label>Min</label>
                      <input type="number" step="0.01" value={ranges['High Spender'].min ?? ''} onChange={(e) => onRangeChange('High Spender','min', e.target.value)} />
                      <label>Max</label>
                      <input type="number" step="0.01" value={ranges['High Spender'].max ?? ''} onChange={(e) => onRangeChange('High Spender','max', e.target.value)} />
                    </>
                  )}
                  {key === 'Medium Spender' && (
                    <>
                      <label>Min</label>
                      <input type="number" step="0.01" value={ranges['Medium Spender'].min ?? ''} onChange={(e) => onRangeChange('Medium Spender','min', e.target.value)} />
                      <label>Max</label>
                      <input type="number" step="0.01" value={ranges['Medium Spender'].max ?? ''} onChange={(e) => onRangeChange('Medium Spender','max', e.target.value)} />
                    </>
                  )}
                  {key === 'Low Spender' && (
                    <>
                      <label>Min</label>
                      <input type="number" step="0.01" value={ranges['Low Spender'].min ?? ''} onChange={(e) => onRangeChange('Low Spender','min', e.target.value)} />
                      <label>Max</label>
                      <input type="number" step="0.01" value={ranges['Low Spender'].max ?? ''} onChange={(e) => onRangeChange('Low Spender','max', e.target.value)} />
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
                  renderBody={(item, index) => renderBody(item, index, navigate)}
                />
              </div>
            </div>
          </div>
        ) : null
      )}
    </div>
  );
};

export default CustomerSpendingClassificationTables;
