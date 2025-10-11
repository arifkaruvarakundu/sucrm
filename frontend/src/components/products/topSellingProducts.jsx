import React, { useEffect, useState } from "react";
import Chart from "react-apexcharts";
import api from "../../../api_config"
import { useTranslation } from 'react-i18next';

const TopSellingProductsChart = () => {

  const [series, setSeries] = useState([]);
  const [categories, setCategories] = useState([]);

  const { t } = useTranslation("productAnalysis");

  useEffect(() => {
    api
      .get("/product-analysis/top-products")
      .then((res) => {
        const rows = Array.isArray(res.data?.rows) ? res.data.rows : [];
        const names = rows.map((r) => r.product);
        const values = rows.map((r) =>
          r.total_amount != null ? Number(r.total_amount) : Number(r.orders || 0)
        );
  
        setCategories(names);
        setSeries([
          {
            name: res.data?.amount_column ? "Total Amount" : "Orders",
            data: values,
          },
        ]);
      })
      .catch(() => {
        setCategories([]);
        setSeries([]);
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
      text: t("top5SellingProducts"),
      align: "center",
    },
  };

  return <Chart options={options} series={series} type="bar" height={350} />;
};

export default TopSellingProductsChart;

