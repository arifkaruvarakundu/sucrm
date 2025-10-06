import React, { useEffect, useState } from "react";
import Chart from "react-apexcharts";
import axios from "axios";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import api from '../../../api_config';
import { useTranslation } from 'react-i18next';


const TopSellingProductsChartInbetween = () => {
  const [series, setSeries] = useState([]);
  const [categories, setCategories] = useState([]);
  const [startDate, setStartDate] = useState();
  const [endDate, setEndDate] = useState();

  const { t } = useTranslation("productAnalysis");

  const fetchData = async () => {
    try {
      const res = await api.get("/product-analysis/top-products-by-date", {
        params: {
          // Send just YYYY-MM-DD to avoid timezone mismatch issues
          start_date: startDate.toISOString().split("T")[0],
          end_date: endDate.toISOString().split("T")[0],
        },
      });
  
      // Backend returns { product_column, amount_column, rows: [...] }
      const rows = res.data.rows || [];
  
      const names = rows.map((p) => p.product);
      const sales = rows.map((p) => p.total_amount || 0); // use 0 if null
  
      setCategories(names);
      setSeries([{ name: "Sales", data: sales }]);
    } catch (err) {
      console.error("Failed to fetch top products:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [startDate, endDate]);

  const options = {
    chart: { type: "bar" },
    xaxis: { categories },
    title: { text: t("top5SellingProducts"), align: "center" },
  };

  return (
    <div className="p-4">
      <div className="flex items-center gap-4 mb-4">
        <label className="text-sm font-medium">{t("from")}:</label>
        <DatePicker selected={startDate} onChange={(date) => setStartDate(date)} />
        <label className="text-sm font-medium">{t("to")}:</label>
        <DatePicker selected={endDate} onChange={(date) => setEndDate(date)} />
      </div>
      <Chart options={options} series={series} type="bar" height={350} />
    </div>
  );
};

export default TopSellingProductsChartInbetween;
