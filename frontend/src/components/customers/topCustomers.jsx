import React, { useEffect, useState } from "react";
import Chart from "react-apexcharts";
import api from "../../../api_config";
import { useTranslation } from "react-i18next";

const TopCustomersChart = () => {
  const [series, setSeries] = useState([]);
  const [categories, setCategories] = useState([]);
  const { t } = useTranslation("customerAnalysis");

  useEffect(() => {
    api.get(`/dashboard/top-customers`).then((res) => {
      const rows = Array.isArray(res.data.rows) ? res.data.rows : [];
      
      //sort by total_amount descending and take top 5
      const top5 = rows
        .sort((a,b) => (b.total_amount ?? 0) - (a.total_amount ?? 0))
        .slice(0, 5);

      const names = top5.map((c) => c.customer);
      const totalSpent = top5.map((c) => c.total_amount);

      setCategories(names);
      setSeries([
        {
          name: "Total Spent",
          data: totalSpent,
        },
      ]);
    });
  }, []);

  const options = {
    chart: {
      type: "bar",
    },
    xaxis: {
      categories: categories,
    },
    title: {
      text: t("top_5_customers_by_spending"),
      align: "center",
    },
    tooltip: {
      y: {
        formatter: (val) => `$${val.toFixed(2)}`
      }
    }
  };

  return <Chart options={options} series={series} type="bar" height={350} />;
};

export default TopCustomersChart;
