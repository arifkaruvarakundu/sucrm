import React, {useEffect, useState} from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import API_BASE_URL from '../../api_config';
import Chart from 'react-apexcharts';
import { useSelector } from 'react-redux';
import StatusCard from '../components/status-card/StatusCard';
import Table from '../components/table/Table';
import Badge from '../components/badge/Badge';
import { useTranslation} from 'react-i18next';
import api from "../../api_config"
// import ChatAI from '../components/chat_ai/chat_ai';
// import statusCards from '../assets/JsonData/status-card-data.json';

const chartOptions = {
    series: [{
        name: 'Online Customers',
        data: [40,70,20,90,36,80,30,91,60]
    }, {
        name: 'Store Customers',
        data: [40, 30, 70, 80, 40, 16, 40, 20, 51, 10]
    }],
    options: {
        color: ['#6ab04c', '#2980b9'],
        chart: {
            background: 'transparent'
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth'
        },
        xaxis: {
            categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep']
        },
        legend: {
            position: 'top'
        },
        grid: {
            show: false
        }
    }
}

// const topCustomerHead = ["user", "totalOrders", "totalSpending"];

// const renderCustomerHead = (item, index) => <th key={index}>{t(item)}</th>;

const renderCustomerBody = (item, index) => (
    <tr key={index}>
        <td>{item.user}</td>
        <td>{item.total_orders}</td>
        <td>{item.total_spending}</td>
    </tr>
);

// const renderCustomerBody = (item, index) => (
//     <tr key={index}>
//         <td>{item.username}</td>
//         <td>{item.order}</td>
//         <td>{item.price}</td>
//     </tr>
// )

const orderStatus = {
    "cancelled": "danger",
    "pending": "warning",
    "completed": "success",
    "failed": "danger",
    "processing": "primary",
}

const renderOrderBody = (item, index) => (
    <tr key={index}>
        <td>{item.id}</td>
        <td>{item.user}</td>
        <td>{item.price.replace('$', 'KD ')}</td>
        <td>{item.date}</td>
        <td>
            <Badge type={orderStatus[item.status]} content={item.status}/>
        </td>
    </tr>
)

const Dashboard = () => {

    const [orders, setOrders] = useState([])
    // const [rows, setRows] = useState([])
    // const [columns, setColumns] = useState([]);
    const [orderHeaders, setOrderHeaders] = useState([]);
    const [statusCards, setStatusCards] = useState([])
    const [topCustomers, setTopCustomers] = useState([])
    const [salesComparison, setSalesComparison] = useState(null)
    const [topCustHeaders, setTopCustHeaders] = useState([]);
    const [topCustRows, setTopCustRows] = useState([]);

    const { t, i18n } = useTranslation("landing");

    const topCustomerHead = ["user", "totalOrders", "totalSpending"];
    const renderCustomerHead = (item, index) => <th key={index}>{t(item)}</th>;

    useEffect(() => {
        (async () => {
            try {
            const { data } = await api.get("/dashboard/latest-rows", {
                params: { limit: 5 },
            });

            // Ensure data is an array
            if (!Array.isArray(data) || data.length === 0) {
                setOrderHeaders([]);
                setOrders([]);
                console.log("No latest rows:", data);
                return;
            }

            // Extract column headers
            const keys = Object.keys(data[0].data || {});
            setOrderHeaders(keys.map((k) => k.replaceAll("_", " ").toUpperCase()));

            // Map rows into array of arrays for table
            const formattedRows = data.map((item) =>
                keys.map((k) => item.data?.[k] ?? "")
            );
            setOrders(formattedRows);

            console.log("Latest rows:", formattedRows);
            } catch (err) {
            console.error("Error fetching latest rows:", err);
            }
        })();
        }, []);

      useEffect(() => {
        (async () => {
            try {
            const { data } = await api.get("/dashboard/top-customers", {
                params: { limit: 5 },
            });

            // Ensure rows exist
            const rows = Array.isArray(data.rows) ? data.rows : [];
            if (rows.length === 0) {
                setTopCustHeaders([]);
                setTopCustRows([]);
                console.log("No top customers:", data);
                return;
            }

            // Extract headers dynamically
            const headers = Object.keys(rows[0]); // e.g. ["user", "total_orders", "total_spending"]
            setTopCustHeaders(headers.map((h) => h.replaceAll("_", " ").toUpperCase()));

            // Map rows into array-of-arrays for Table
            const formattedRows = rows.map((row) => headers.map((h) => row[h] ?? ""));
            setTopCustRows(formattedRows);

            console.log("Top customers formatted:", formattedRows);
            } catch (err) {
            console.error("Error fetching top customers:", err);
            }
        })();
        }, []);

      useEffect(() => {
        const fetchStatusCards = async () => {
          try {
            const { data: { count } } = await api.get("/dashboard/total-orders-count");
            const { data: { total_sales } } = await api.get("/dashboard/total-sales");
            const { data: { total_products } } = await api.get("/dashboard/total-products");
            const { data: { total_customers } } = await api.get("/dashboard/total-customers");
            console.log("total customers",total_customers )
    
            const cards = [
              {
                title: t("totalSales"),
                count: total_sales,
                icon: "bx bx-shopping-bag",
              },
              {
                title: "Total Products",
                count: total_products,
                icon: "bx bx-cart",
              },
              {
                title: t("totalCustomers"),
                count: total_customers,
                icon: "bx bx-dollar-circle",
              },
              {
                title: t("totalOrders"),
                count,
                icon: "bx bx-receipt",
              },
            ];
    
            setStatusCards(cards);
          } catch (error) {
            console.error("Failed to fetch status card data", error);
          }
        };
    
        fetchStatusCards();
      }, [i18n.language]);

    useEffect(() => {
        api.get(`/sales-comparison`)
            .then((res) => {
                setSalesComparison(res.data);
            })
            .catch((err) => console.error("Failed to fetch sales comparison data:", err));
    }, []);

    const getSalesChartData = (data) => {
    const maxDay = Math.max(
        ...data.previousMonth.map(item => item.day),
        ...data.currentMonth.map(item => item.day)
    );

    const labels = Array.from({ length: maxDay }, (_, i) => `${i + 1}`);

    const prevSeries = Array(maxDay).fill(0);
    const currSeries = Array(maxDay).fill(0);

    data.previousMonth.forEach(({ day, total }) => {
        prevSeries[day - 1] = total;
    });

    data.currentMonth.forEach(({ day, total }) => {
        currSeries[day - 1] = total;
    });

    return {
        series: [
            {
                name: t("previousMonth"),
                data: prevSeries
            },
            {
                name: t("thisMonth"),
                data: currSeries
            }
        ],
        options: {
            chart: {
                background: 'transparent'
            },
            stroke: {
                curve: 'smooth'
            },
            dataLabels: {
                enabled: false
            },
            xaxis: {
                categories: labels,
                title: {
                    text: t("dayOfMonth")
                }
            },
            yaxis: {
                title: {
                    text: t("salesKD")
                },
                labels: {
                    formatter: val => Number(val).toFixed(3)
                }
            },

            legend: {
                position: 'top'
            },
            theme: {
                mode: themeReducer === 'theme-mode-dark' ? 'dark' : 'light'
            },
            tooltip: {
                y: {
                    formatter: val => `KD ${val.toFixed(2)}`
                }
            },
            grid: {
                show: false
            }
        }
    };
};

    const latestRowsHeaders = ["orderId", "user", "totalPrice", "date", "status"];
    const renderOrderHead = (item, index) => <th key={index}>{t(item)}</th>;
    const theme = useSelector(state => state.theme)

    return (
        <div>
            <h2 className="page-header">{t("dashboard")}</h2>
            {/* <ChatAI /> */}
            <div className="row">
                <div className="col-6">
                  <div className="row">
                    {statusCards.length > 0 ? (
                        statusCards.map((item, index) => (
                        <div className="col-6" key={index}>
                            <StatusCard
                            icon={item.icon}
                            count={item.count ?? t("noData")}
                            title={item.title}
                            />
                        </div>
                        ))
                    ) : (
                        <p className="text-center w-full">{t("noData")}</p>
                    )}
                    </div>

                </div>
                <div className="col-6">
                    <div className="card full-height">
                        {
                            salesComparison ? (
                                <Chart
                                    options={getSalesChartData(salesComparison).options}
                                    series={getSalesChartData(salesComparison).series}
                                    type='line'
                                    height='100%'
                                />
                            ) : (
                                <p>{t("loadingChart")}</p>
                            )
                        }
                    </div>
                </div>

                <div className="col-4">
                    <div className="card">
                        <div className="card__header">
                        <h3>{t("topCustomers")}</h3>
                        </div>
                        <div className="card__body">
                            {topCustRows.length > 0 ? (
                                <Table
                                    headData={topCustHeaders}
                                    renderHead={(h, i) => <th key={i}>{h}</th>}
                                    bodyData={topCustRows}
                                    renderBody={(row, rIdx) => (
                                        <tr key={rIdx}>
                                        {row.map((cell, cIdx) => (
                                            <td key={cIdx}>
                                            {cIdx === row.length - 1 ? `KD ${Number(cell).toFixed(2)}` : cell}
                                            </td>
                                        ))}
                                        </tr>
                                    )}
                                    />
                            ) : (
                                <p className="text-center">{t("noData")}</p>
                            )}
                            </div>
                        <div className="card__footer">
                        <Link to='/CustomerAnalysis'>{t("viewAll")}</Link>
                        </div>
                    </div>
                    </div>

                <div className="col-8">
                    <div className="card">
                        <div className="card__header">
                            <h3>{t("latestData")}</h3>
                        </div>
                        <div className="card__body">
                            {orders.length > 0 ? (
                                <Table
                                headData={orderHeaders}
                                renderHead={(h, i) => <th key={i}>{h}</th>}
                                bodyData={orders}
                                renderBody={(row, rIdx) => (
                                    <tr key={rIdx}>
                                    {row.map((cell, cIdx) => (
                                        <td key={cIdx}>{cell == null ? "" : String(cell)}</td>
                                    ))}
                                    </tr>
                                )}
                                />
                            ) : (
                                <p className="text-center">{t("noData")}</p>
                            )}
                            </div>
                        <div className="card__footer">
                            <Link to='/orderAnalysis'>{t("viewAll")}</Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
