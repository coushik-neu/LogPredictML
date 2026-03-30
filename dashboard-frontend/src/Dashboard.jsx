import React, { useEffect, useState, useRef } from "react";
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell
} from "recharts";
import { AlertTriangle, Users, DollarSign, Brain, ExternalLink } from "lucide-react";

const WS_URL = "ws://localhost:8000/ws/dashboard";
const COLORS = ["#ef4444", "#f59e0b", "#22c55e"];

const Card = ({ children }) => (
    <div className="bg-zinc-800 border border-zinc-700 rounded-2xl p-4 h-full">
        {children}
    </div>
);

// -----------------------------
// Tooltip
// -----------------------------
const DarkTooltip = ({ active, payload }) => {
    if (!active || !payload) return null;

    return (
        <div className="bg-zinc-900 border border-zinc-700 p-2 rounded-lg text-xs shadow-lg">
            {payload.map((p, i) => (
                <div key={i} className="text-gray-300">
                    {p.name}: <span className="text-white font-semibold">{p.value}</span>
                </div>
            ))}
        </div>
    );
};

export default function Dashboard() {

    const [drift, setDrift] = useState({ drift_score: 0 });
    const [churn, setChurn] = useState({ high: 0, medium: 0, low: 0 });
    const [model, setModel] = useState({ model_version: "", f1: 0 });
    const [models, setModels] = useState([]);

    const [revenue, setRevenue] = useState(0);
    const [trendData, setTrendData] = useState([]);
    const [performance, setPerformance] = useState([]);

    const [customers, setCustomers] = useState([]);
    const [page, setPage] = useState(1);
    const listRef = useRef();

    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [orders, setOrders] = useState([]);

    const [ordersPage, setOrdersPage] = useState(1);
    const [hasMoreOrders, setHasMoreOrders] = useState(true);

    async function fetchMoreOrders() {
        if (!selectedCustomer || !hasMoreOrders) return;

        const nextPage = ordersPage + 1;

        const res = await fetch(
            `http://localhost:8000/api/customer-orders/${selectedCustomer.customer_id}?page=${nextPage}&limit=10&_=${Date.now()}`,
            { cache: "no-store" }
        );

        const data = await res.json();

        // if no more data, stop further calls
        if (data.length === 0) {
            setHasMoreOrders(false);
            return;
        }

        setOrders(prev => [...prev, ...data]);
        setOrdersPage(nextPage);
    }

    const ordersRequestRef = useRef(0);

    useEffect(() => {
        if (!selectedCustomer) return;

        const requestId = ++ordersRequestRef.current;


        fetch(
            `http://localhost:8000/api/customer-orders/${selectedCustomer.customer_id}?page=1&page_size=20&_=${Date.now()}`,
            { cache: "no-store" }
        )
            .then(res => res.json())
            .then(data => {
                // ✅ ONLY update if this is the latest request
                if (ordersRequestRef.current === requestId) {
                    setOrders(data?.data || data || []);
                }
            })
            .catch(() => {
                if (ordersRequestRef.current === requestId) {
                    setOrders([]);
                }
            });

    }, [selectedCustomer]);



    // -----------------------------
    // INITIAL LOAD
    // -----------------------------
    useEffect(() => {
        async function loadInitial() {
            const now = Date.now();

            const [
                modelRes,
                driftRes,
                perfRes,
                revenueTrendRes,
                modelsRes
            ] = await Promise.all([
                fetch(`http://localhost:8000/api/model-health?_=${now}`, { cache: "no-store" }),
                fetch(`http://localhost:8000/api/drift-status?_=${now}`, { cache: "no-store" }),
                fetch(`http://localhost:8000/api/performance-trend?_=${now}`, { cache: "no-store" }),
                fetch(`http://localhost:8000/api/revenue-trend?_=${now}`, { cache: "no-store" }),
                fetch(`http://localhost:8000/api/models?page=1&page_size=20&_=${now}`, { cache: "no-store" })
            ]);

            const modelData = await modelRes.json();
            const driftData = await driftRes.json();
            const perfData = await perfRes.json();
            const modelsData = await modelsRes.json();
            const revenueTrend = await revenueTrendRes.json();

            // ✅ SAFE SETTERS
            setModel({
                model_version: modelData?.model_version || "N/A",
                f1: modelData?.f1_score || 0
            });

            setDrift({
                drift_score: driftData?.drift_score || 0
            });

            setPerformance(perfData || []);
            setModels(modelsData?.data || []);

            setTrendData(
                (revenueTrend || []).slice(-30).map((r, i) => ({
                    time: i,
                    revenue: r.sales || 0
                }))
            );
        }

        loadInitial();
        loadCustomers(1);
    }, []);

    // -----------------------------
    // CUSTOMERS (PAGINATION FIXED)
    // -----------------------------
    async function loadCustomers(p) {
        const res = await fetch(
            `http://localhost:8000/api/high-risk-customers?page=${p}&page_size=20&_=${Date.now()}`,
            { cache: "no-store" }
        );

        const data = await res.json();

        if (p === 1) setCustomers(data?.data || []);
        else setCustomers(prev => [...prev, ...(data?.data || [])]);
    }

    const handleScroll = () => {
        const el = listRef.current;
        if (!el) return;

        if (el.scrollTop + el.clientHeight >= el.scrollHeight - 10) {
            const next = page + 1;
            setPage(next);
            loadCustomers(next);
        }
    };

    // -----------------------------
    // WEBSOCKET
    // -----------------------------
    useEffect(() => {
        const ws = new WebSocket(WS_URL);

        ws.onmessage = (e) => {
            const msg = JSON.parse(e.data);

            if (msg.event === "drift_update") {
                setDrift({ drift_score: msg.data?.drift_score || 0 });
            }

            if (msg.event === "churn_update") {
                setChurn(msg.data || {});
            }

            if (msg.event === "model_update") {
                setModel({
                    model_version: msg.data?.model_version || "N/A",
                    f1: msg.data?.f1 || 0
                });
            }

            if (msg.event === "business_update") {
                setRevenue(msg.data?.total_revenue || 0);

                setTrendData(prev => [
                    ...prev.slice(-49),
                    {
                        time: prev.length,
                        revenue: msg.data?.total_revenue || 0
                    }
                ]);
            }
        };

        return () => ws.close();
    }, []);

    // -----------------------------
    // CUSTOMER ORDERS (FIXED)
    // -----------------------------
    useEffect(() => {
        if (!selectedCustomer) return;

        fetch(
            `http://localhost:8000/api/customer-orders/${selectedCustomer.customer_id}?page=1&page_size=20&_=${Date.now()}`,
            { cache: "no-store" }
        )
            .then(r => r.json())
            .then(data => setOrders(data?.data || []));
    }, [selectedCustomer]);

    // -----------------------------
    // DATA FORMATTING (SAFE)
    // -----------------------------
    const churnData = [
        { name: "High", value: churn?.high || 0 },
        { name: "Medium", value: churn?.medium || 0 },
        { name: "Low", value: churn?.low || 0 },
    ];

    const perfData = (performance || []).map((p, i) => ({
        time: i,
        f1: p?.f1_score || 0
    }));

    return (
        <div className="bg-zinc-950 text-white h-screen p-4 flex flex-col gap-4 overflow-hidden">

            {/* HEADER */}
            <div className="flex justify-between items-center">
                <h1 className="text-xl font-bold">AI Monitoring</h1>
                <div className="flex items-center gap-2 text-green-400 text-sm">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
                    LIVE
                </div>
            </div>

            {/* METRICS */}
            <div className="grid grid-cols-4 gap-4">
                <Metric title="Revenue" value={`$${(revenue || 0).toLocaleString()}`} icon={<DollarSign />} />
                <Metric title="Model" value={model.model_version} sub={`F1: ${(model.f1 ?? 0).toFixed(3)}`} icon={<Brain />} />
                <Metric title="Drift" value={(drift?.drift_score ?? 0).toFixed(2)} icon={<AlertTriangle />} />
                <Metric title="High Risk" value={churn?.high || 0} icon={<Users />} />
            </div>

            {/* MAIN GRID */}
            <div className="grid grid-cols-5 gap-4 flex-1 overflow-hidden">

                {/* LEFT */}
                <div className="col-span-3 grid grid-rows-2 gap-4">

                    {/* PIE + MODELS */}
                    <Card>
                        <div className="grid grid-cols-2 gap-4 h-full">

                            <div>
                                <h2>Churn</h2>

                                <ResponsiveContainer width="100%" height={150}>
                                    <PieChart>
                                        <Pie data={churnData} dataKey="value" innerRadius={40} outerRadius={70}>
                                            {churnData.map((e, i) => (
                                                <Cell key={i} fill={COLORS[i]} />
                                            ))}
                                        </Pie>
                                    </PieChart>
                                </ResponsiveContainer>

                                {/* ✅ LEGEND */}
                                <div className="flex justify-around text-xs mt-2">
                                    {churnData.map((c, i) => (
                                        <div key={i} className="flex items-center gap-1">
                                            <div
                                                className="w-2 h-2 rounded-full"
                                                style={{ backgroundColor: COLORS[i] }}
                                            />
                                            <span className="text-gray-400">{c.name}</span>
                                            <span className="text-white">{c.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>


                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <h2>Models</h2>
                                    <button
                                        onClick={() => window.open("http://localhost:5000", "_blank")}
                                        className="text-xs flex items-center gap-1 text-blue-400"
                                    >
                                        MLflow <ExternalLink size={12} />
                                    </button>
                                </div>

                                <div className="space-y-1 text-xs max-h-40 overflow-y-auto">
                                    {models.map((m, i) => (
                                        <div key={i} className="flex justify-between">
                                            <span>{m.model_version}</span>
                                            <span>{m.f1_score}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                        </div>
                    </Card>

                    {/* GRAPHS */}
                    <div className="grid grid-cols-2 gap-4">

                        <Card>
                            <h2>Revenue</h2>
                            <ResponsiveContainer width="100%" height={180}>
                                <AreaChart data={trendData}>
                                    <XAxis hide />
                                    <YAxis hide />
                                    <Tooltip content={<DarkTooltip />} />
                                    <Area dataKey="revenue" stroke="#3b82f6" fill="#3b82f633" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </Card>

                        <Card>
                            <h2>Model F1</h2>
                            <ResponsiveContainer width="100%" height={180}>
                                <AreaChart data={perfData}>
                                    <XAxis hide />
                                    <YAxis hide />
                                    <Tooltip content={<DarkTooltip />} />
                                    <Area dataKey="f1" stroke="#22c55e" fill="#22c55e33" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </Card>

                    </div>
                </div>

                {/* RIGHT */}
                <div className="col-span-2">
                    <Card>
                        <h2>High Risk Customers</h2>

                        <div
                            ref={listRef}
                            onScroll={handleScroll}
                            className="overflow-y-auto h-[500px] space-y-2 pr-2"
                        >
                            {customers.map(c => (
                                <div
                                    key={c.customer_id}
                                    onClick={() => setSelectedCustomer(c)}
                                    className="p-3 bg-zinc-800 rounded hover:bg-zinc-700 cursor-pointer"
                                >
                                    <div className="flex justify-between">
                                        <span>{c.customer_name || c.customer}</span>
                                        <span className="text-red-400">
                                            {((c.churn_probability || 0) * 100).toFixed(1)}%
                                        </span>
                                    </div>

                                    <div className="text-xs text-gray-400">
                                        {c.company || c.industry} • Orders: {c.total_orders} • ${c.total_sales}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Card>
                </div>
            </div>

            {/* DETAILS */}
            {selectedCustomer && (
                <div className="grid grid-cols-5 gap-4 h-[200px]">

                    <div className="col-span-2">
                        <Card>
                            <h2>Customer</h2>
                            <div className="grid grid-cols-2 gap-2 mt-2">
                                <Info label="Orders" value={selectedCustomer.total_orders} />
                                <Info label="Sales" value={selectedCustomer.total_sales} />
                                <Info label="Avg Value" value={selectedCustomer.avg_order_value} />
                                <Info label="Last Order" value={selectedCustomer.last_order_days} />
                            </div>
                        </Card>
                    </div>

                    <div className="col-span-3">
                        <Card>
                            <h2 className="text-sm font-semibold mb-2">Recent Orders</h2>

                            {/* HEADER */}
                            <div className="grid grid-cols-8 text-[11px] text-gray-400 border-b border-zinc-700 pb-2 px-1">
                                <span>Order</span>
                                <span>Date</span>
                                <span>Product</span>
                                <span>Industry</span>
                                <span>Segment</span>
                                <span className="text-right">Sales</span>
                                <span className="text-right">Profit</span>
                                <span className="text-right">Disc</span>
                            </div>

                            {/* SCROLL */}
                            <div className="max-h-[150px] overflow-y-auto mt-2 space-y-1 pr-1">

                                {orders.length === 0 ? (
                                    <div className="text-center text-gray-500 text-sm py-4">
                                        No orders found
                                    </div>
                                ) : (
                                    orders.map((o, i) => {
                                        const isLoss = o.sales < 0;

                                        return (
                                            <div
                                                key={i}
                                                className="grid grid-cols-8 text-xs bg-zinc-800 px-2 py-2 rounded hover:bg-zinc-700 transition"
                                            >
                                                <span className="truncate text-gray-300">
                                                    {o.order_id}
                                                </span>

                                                <span className="text-gray-400">
                                                    {new Date(o.order_date).toLocaleDateString()}
                                                </span>

                                                <span className="truncate">{o.product}</span>

                                                <span className="truncate text-gray-400">
                                                    {o.industry}
                                                </span>

                                                <span className="truncate text-gray-500">
                                                    {o.segment}
                                                </span>

                                                <span
                                                    className={`text-right font-semibold ${isLoss ? "text-red-400" : "text-blue-400"
                                                        }`}
                                                >
                                                    ${o.sales.toFixed(2)}
                                                </span>

                                                <span className="text-right text-green-400">
                                                    ${o.profit.toFixed(2)}
                                                </span>

                                                <span className="text-right text-yellow-400">
                                                    {(o.discount * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        );
                                    })
                                )}

                            </div>
                        </Card>
                    </div>



                </div>
            )}
        </div>
    );
}

function Metric({ title, value, sub, icon }) {
    return (
        <Card>
            <div className="flex items-center gap-3">
                <div className="bg-zinc-700 p-2 rounded">{icon}</div>
                <div>
                    <p className="text-xs text-gray-400">{title}</p>
                    <p className="font-bold">{value}</p>
                    {sub && <p className="text-xs">{sub}</p>}
                </div>
            </div>
        </Card>
    );
}

function Info({ label, value }) {
    return (
        <div className="bg-zinc-800 p-2 rounded text-center">
            <p className="text-xs text-gray-400">{label}</p>
            <p>{value}</p>
        </div>
    );
}
