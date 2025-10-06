import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Table from '../table/Table'
import api from '../../../api_config'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { useTranslation } from 'react-i18next';

const OrderTable = () => {
  const { t } = useTranslation("ordersAnalysis");

  const [orders, setOrders] = useState([])
  const [filteredOrders, setFilteredOrders] = useState([])
  const [startDate, setStartDate] = useState(null)
  const [endDate, setEndDate] = useState(null)
  const [columns, setColumns] = useState([]) // dynamic columns

  const fetchOrders = async () => {
    try {
      const params = {}
  
      if (startDate) params.start_date = startDate.toISOString().split("T")[0]
      if (endDate) params.end_date = endDate.toISOString().split("T")[0]
  
      const res = await api.get(`/order-analysis/orders-in-range`, { params })
      const data = res.data
  
      setOrders(data)
      setFilteredOrders(data)
  
      if (data.length > 0) setColumns(Object.keys(data[0]))
    } catch (err) {
      console.error('Error fetching orders:', err)
    }
  }
  

  useEffect(() => {
    if (startDate && endDate) fetchOrders()
  }, [startDate, endDate])

  const filterByDateRange = () => {
    if (startDate && endDate) {
      const filtered = orders.filter((order) => {
        const orderDate = new Date(order.date)
        return orderDate >= startDate && orderDate <= endDate
      })
      setFilteredOrders(filtered)
    } else {
      setFilteredOrders(orders)
    }
  }

  useEffect(() => {
    filterByDateRange()
  }, [startDate, endDate, orders])

  const renderHead = (item, index) => <th key={index}>{t(item)}</th>

  const renderBody = (item, index) => (
    <tr key={index}>
      {columns.map((col) => (
        <td key={col}>
          {col === "status" ? (
            <span
              className={`badge ${
                item.status === 'processing'
                  ? 'bg-yellow-500'
                  : item.status === 'failed'
                  ? 'bg-red-500'
                  : 'bg-green-500'
              } text-white px-2 py-1 rounded`}
            >
              {item.status}
            </span>
          ) : (
            item[col]
          )}
        </td>
      ))}
    </tr>
  )

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">{t("pageTitle")}</h2>

      <div className="mb-4 flex flex-wrap gap-4 items-center">
        <div>
          <label className="block text-sm font-medium mb-1">{t("startDate")}</label>
          <DatePicker
            selected={startDate}
            onChange={(date) => setStartDate(date)}
            className="border px-3 py-2 rounded"
            dateFormat="dd MMM yyyy"
            placeholderText={t("startDatePlaceholder")}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t("endDate")}</label>
          <DatePicker
            selected={endDate}
            onChange={(date) => setEndDate(date)}
            className="border px-3 py-2 rounded"
            dateFormat="dd MMM yyyy"
            placeholderText={t("endDatePlaceholder")}
          />
        </div>
      </div>

      <div className="col-12">
        <div className="card">
          <div className="card__header">
            <h3>{t("tableTitle")}</h3>
            <p className="text-sm text-gray-600 mt-2">
              {t("showing")} <span className="font-semibold">{filteredOrders.length}</span> {t("order")}
              {filteredOrders.length !== 1 ? 's' : ''} {t("inSelectedDateRange")}
            </p>
          </div>
          <div className="card__body">
            <Table
              limit="10"
              headData={columns}
              renderHead={renderHead}
              bodyData={filteredOrders}
              renderBody={renderBody}
            />
          </div>
          <div className="card__footer">{/* Optional footer */}</div>
        </div>
      </div>
    </div>
  )
}

export default OrderTable
