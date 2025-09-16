import React, { useEffect, useState } from "react";
import Chart from "react-apexcharts";
import axios from "axios";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import API_BASE_URL from '../../../api_config';
import { useTranslation } from 'react-i18next';


const TopSellingProductsChartInbetween = () => {
  const [series, setSeries] = useState([]);
  const [categories, setCategories] = useState([]);
  const [startDate, setStartDate] = useState(new Date(new Date().setDate(new Date().getDate() - 30)));
  const [endDate, setEndDate] = useState(new Date());

  const { t } = useTranslation("productAnalysis");

  const fetchData = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/top-products-inbetween`, {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
        },
      });

      const names = res.data.map((p) => p.name);
      const sales = res.data.map((p) => p.total_quantity_sold);

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
