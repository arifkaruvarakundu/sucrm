import React, { useEffect, useState } from "react";
import Chart from "react-apexcharts";
import api from "../../../api_config";
import { useTranslation } from "react-i18next";

const TopCustomersChart = () => {
  const [series, setSeries] = useState([]);
  const [categories, setCategories] = useState([]);
  const [customerColumn, setCustomerColumn] = useState("");
  const [amountColumn, setAmountColumn] = useState("");
  const { t } = useTranslation("customerAnalysis");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get(`/dashboard/top-customers`);
        const data = res?.data || {};
        const rows = Array.isArray(data.rows) ? data.rows : [];
  
        if (!rows.length) return;
  
        const customerKey = data.customer_column || Object.keys(rows[0])[0];
        const amountKey = data.amount_column || Object.keys(rows[0])[1];
  
        setCustomerColumn(customerKey);
        setAmountColumn(amountKey);
  
        // Sort descending by amount
        const top5 = [...rows]
          .sort((a, b) => (b[amountKey] ?? 0) - (a[amountKey] ?? 0))
          .slice(0, 5);
  
        const names = top5.map(r => r[customerKey] ?? "N/A");
        const totals = top5.map(r => Number(r[amountKey]) || 0);
  
        setCategories(names);
        setSeries([{ name: amountKey, data: totals }]);
      } catch (err) {
        console.error("Error fetching top customers:", err);
        setCategories([]);
        setSeries([{ name: "Total", data: [] }]);
      }
    };
  
    fetchData();
  }, []);
  

  // detect RTL (Arabic) automatically
  const isRTL = /[\u0600-\u06FF]/.test(customerColumn + amountColumn);

  const options = {
    chart: {
      type: "bar",
      toolbar: { show: false },
    },
    plotOptions: {
      bar: {
        distributed: true,
        borderRadius: 6,
      },
    },
    xaxis: {
      categories: categories,
      title: { text: customerColumn || t("customer") },
      labels: { style: { fontSize: "14px" } },
    },
    yaxis: {
      title: { text: amountColumn || t("total_spent") },
    },
    title: {
      text: `${t("top_customers_by")} ${amountColumn || t("spending")}`,
      align: "center",
      style: { fontSize: "16px", fontWeight: 600 },
    },
    tooltip: {
      y: {
        formatter: (val) =>
          typeof val === "number" ? `$${val.toFixed(2)}` : "$0.00",
      },
    },
    dataLabels: {
      enabled: true,
      formatter: (val) => `${val}`,
    },
    noData: {
      text: t("no_data_available") || "No data available",
    },
  };

  return (
    <div dir={isRTL ? "rtl" : "ltr"}>
      <Chart options={options} series={series} type="bar" height={350} />
    </div>
  );
};

export default TopCustomersChart;
