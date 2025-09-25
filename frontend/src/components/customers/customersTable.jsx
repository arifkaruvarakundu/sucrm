import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import Table from '../table/Table'; // Update path based on your actual file structure
import API_BASE_URL from '../../../api_config';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const CustomersTable = ({customers, columns = []}) => {
    const [topCustomers, setTopCustomers] = useState([]);

    const navigate = useNavigate();
    const { t } = useTranslation("customerAnalysis");

    const hasCivilId = columns.includes("civil_id");
    const topCustomerHead = columns.length
        ? [...columns, ...(hasCivilId ? ["dob"] : [])]
        : ["name", "phone", "city", "email"]; // fallback

    const parseDobFromCivilId = (civil) => {
        if (!civil) return "";
        const digits = String(civil).replace(/\D/g, "");
        if (digits.length < 7) return "";
        const firstSeven = digits.slice(0, 7);
        const yy = firstSeven.slice(1, 3);
        const mm = firstSeven.slice(3, 5);
        const dd = firstSeven.slice(5, 7);
        if (!yy || !mm || !dd) return "";
        return `${yy}/${mm}/${dd}`;
    };

    const renderCustomerHead = (item, index) => <th key={index}>{t(item)}</th>;

    const renderCustomerBody = (item, index) => (
        <tr 
            key={index}
            style={{ cursor: 'default' }}
        >
            {topCustomerHead.map((col, i) => (
                <td key={i}>{
                    col === 'dob' ? parseDobFromCivilId(item?.civil_id) : (item?.[col] ?? '')
                }</td>
            ))}
        </tr>
    );

    // useEffect(() => {
    //     const fetchCustomers = async () => {
    //         try {
    //             const response = await axios.get(`${API_BASE_URL}/customers-table`);
    //             setTopCustomers(response.data);
    //         } catch (error) {
    //             console.error('Error fetching customer data:', error);
    //         }
    //     };

    //     fetchCustomers();
    // }, []);

    return (
        <div className="col-12">
            <div className="card">
                <div className="card__header">
                    <h3>{t("customers")}</h3>
                </div>
                <div className="card__body">
                    <Table
                        limit = "10"
                        headData={topCustomerHead}
                        renderHead={renderCustomerHead}
                        bodyData={customers}
                        renderBody={renderCustomerBody}
                    />
                </div>
                {/* <div className="card__footer">
                    <Link to="/">View All</Link>
                </div> */}
            </div>
        </div>
    );
};

export default CustomersTable;
