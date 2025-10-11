import React from 'react';
import Table from '../table/Table';
import { useTranslation } from 'react-i18next';

const CustomersTable = ({ customers = [], columns = [] }) => {
  const { t } = useTranslation("customerAnalysis");

  const hasCivilId = columns.includes("civil_id");
  const topCustomerHead = columns.length
    ? [...columns, ...(hasCivilId ? ["dob"] : [])]
    : ["customerName", "customerId", "phone", "city"]; // fallback

  const parseDobFromCivilId = (civil) => {
    if (!civil) return "";
    const digits = String(civil).replace(/\D/g, "");
    if (digits.length < 7) return "";
    const firstSeven = digits.slice(0, 7);
    const yy = firstSeven.slice(1, 3);
    const mm = firstSeven.slice(3, 5);
    const dd = firstSeven.slice(5, 7);
    return `${yy}/${mm}/${dd}`;
  };

  const renderCustomerHead = (item, index) => <th key={index}>{t(item) || item}</th>;

  const renderCustomerBody = (row, index) => (
    <tr key={index} style={{ cursor: 'default' }}>
      {topCustomerHead.map((col, i) => (
        <td key={i}>{col === 'dob' ? parseDobFromCivilId(row?.civil_id) : (row[col] ?? '')}</td>
      ))}
    </tr>
  );

  return (
    <div className="col-12">
      <div className="card">
        <div className="card__header">
          <h3>{t("customers")}</h3>
        </div>
        <div className="card__body">
          <Table
            limit="10"
            headData={topCustomerHead}
            renderHead={renderCustomerHead}
            bodyData={customers}
            renderBody={renderCustomerBody}
          />
        </div>
      </div>
    </div>
  );
};

export default CustomersTable;