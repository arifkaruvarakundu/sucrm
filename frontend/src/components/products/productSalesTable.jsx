import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import Table from '../table/Table';
import api from '../../../api_config';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const ProductSalesTable = () => {
  const [products, setProducts] = useState([]);
  const [startDate, setStartDate] = useState();
  const [endDate, setEndDate] = useState();
  const [grandTotal, setGrandTotal] = useState(0);
  const [columns, setColumns] = useState({});

  const navigate = useNavigate();
  const { t } = useTranslation('productAnalysis');

  const fetchSales = async () => {
    if (!startDate || !endDate) return;

    try {
      const res = await api.get(`/product-analysis/products-sales-table`, {
        params: {
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0],
        },
      });

      const data = res.data;
      console.log('data -->', data);

      // ✅ Update columns and rows
      setColumns(data.columns || {});
      setProducts(data.rows || []);

      // ✅ Calculate grand total (price * quantity)
      const total = (data.rows || []).reduce(
        (sum, item) => sum + (item.price * item.quantity),
        0
      );
      setGrandTotal(total);
    } catch (err) {
      console.error('Error fetching product sales:', err);
    }
  };

  useEffect(() => {
    fetchSales();
  }, [startDate, endDate]);

  // ✅ Updated table header setup
  const headData = [
    'ID',
    columns.product_column || 'Product',
    columns.category_column || 'Category',
    columns.price_column || 'Price',
    columns.quantity_column || 'Quantity',
    columns.date_column || 'Date',
    'Total Amount',
  ];

  const renderHead = (item, index) => <th key={index}>{t(item)}</th>;

  // ✅ Updated table body — matches new API fields
  const renderBody = (item, index) => (
    <tr
      key={index}
      onClick={() =>
        navigate(`/product-sales/${item.id}`, {
          state: {
            startDate: startDate?.toISOString(),
            endDate: endDate?.toISOString(),
            productName: item.name,
          },
        })
      }
      className="cursor-pointer hover:bg-gray-50"
    >
      <td>{item.id}</td>
      <td>{item.name}</td>
      <td>{item.category}</td>
      <td>{item.price.toFixed(2)}</td>
      <td>{item.quantity}</td>
      <td>{item.date}</td>
      <td>{(item.price * item.quantity).toFixed(2)}</td>
    </tr>
  );

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">{t('product_sales_by_date')}</h2>

      {/* Date Pickers */}
      <div className="flex gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium mb-1">{t('start_date')}</label>
          <DatePicker
            selected={startDate}
            onChange={(date) => setStartDate(date)}
            className="border p-2 rounded"
            dateFormat="yyyy-MM-dd"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t('end_date')}</label>
          <DatePicker
            selected={endDate}
            onChange={(date) => setEndDate(date)}
            className="border p-2 rounded"
            dateFormat="yyyy-MM-dd"
          />
        </div>
      </div>

      {/* Table + Grand Total */}
      <div className="col-12">
        <div className="card">
          <div className="card__header">
            <h3>{t('sales_per_product')}</h3>
          </div>

          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">{t('product_sales_by_date')}</h2>
            <div className="text-lg font-semibold">
              {t('grand_total_kd')}: {grandTotal.toFixed(2)}
            </div>
          </div>

          <div className="card__body">
            <Table
              limit="10"
              headData={headData}
              renderHead={renderHead}
              bodyData={products}
              renderBody={renderBody}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductSalesTable;
