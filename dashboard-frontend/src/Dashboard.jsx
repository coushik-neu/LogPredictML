import React, { useEffect, useState, useRef } from "react";
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell
} from "recharts";
import { AlertTriangle, Users, DollarSign, Brain, ExternalLink } from "lucide-react";

const WS_URL = "ws://localhost:8000/ws/dashboard";
const COLORS = ["#ef4444", "#f59e0b", "#22c55e"];

const Card = ({ children, className = "" }) => (
    <div className={`bg-zinc-800 border border-zinc-700 rounded-2xl p-4 h-full min-h-0 ${className}`}>
        {children}
    </div>
);


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
    const [customerType, setCustomerType] = useState("active");

    const [loading, setLoading] = useState(false);   // ✅ FIX
    const [hasMore, setHasMore] = useState(true);    // ✅ FIX

    const listRef = useRef();

    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [orders, setOrders] = useState([]);

    const ordersRequestRef = useRef(0);

    // -----------------------------
    // ORDERS
    // -----------------------------
    useEffect(() => {
        if (!selectedCustomer) return;

        const requestId = ++ordersRequestRef.current;

        fetch(
            `http://localhost:8000/api/customer-orders/${selectedCustomer.customer_id}?page=1&page_size=20&_=${Date.now()}`,
            { cache: "no-store" }
        )
            .then(res => res.json())
            .then(data => {
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

            setModel({
                model_version: modelData?.model_version || "N/A",
                f1: modelData?.f1_score || 0
            });

            setDrift({
                drift_score: driftData?.drift_score || 0
            });

            setPerformance(perfData || []);
            setModels(modelsData?.data || []);

            const data = (revenueTrend || []).slice(-30);

setTrendData(
    data.map((r, i) => ({
        time: i,
        revenue: i === 0 ? 0 : (r.sales || 0) - (data[i - 1]?.sales || 0),
        raw: r.sales || 0
    }))
);


        }

        loadInitial();
        loadCustomers(1, "active");
    }, []);

    // -----------------------------
    // LOAD CUSTOMERS (FIXED)
    // -----------------------------
    async function loadCustomers(p, type = customerType) {

        if (loading || !hasMore) return;   // ✅ FIX

        setLoading(true);

        const res = await fetch(
            `http://localhost:8000/api/high-risk-customers?type=${type}&page=${p}&page_size=20&_=${Date.now()}`,
            { cache: "no-store" }
        );

        const data = await res.json();

        const newData = data?.data || [];

        if (p === 1) {
            setCustomers(newData);
        } else {
            setCustomers(prev => [...prev, ...newData]);
        }

        setHasMore(data?.has_more ?? newData.length > 0);  // ✅ FIX
        setLoading(false);
    }

    // -----------------------------
    // TYPE CHANGE
    // -----------------------------
    const handleTypeChange = (type) => {
        setCustomerType(type);
        setPage(1);
        setCustomers([]);   // ✅ FIX reset list
        setHasMore(true);   // ✅ FIX reset pagination
        setSelectedCustomer(null);
        loadCustomers(1, type);
    };

    // -----------------------------
    // SCROLL FIX
    // -----------------------------
    const handleScroll = () => {
        const el = listRef.current;
        if (!el || loading || !hasMore) return;  // ✅ FIX

        if (el.scrollTop + el.clientHeight >= el.scrollHeight - 10) {
            const next = page + 1;
            setPage(next);
            loadCustomers(next);
        }
    };

    // -----------------------------
    // WEBSOCKET (UNCHANGED)
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
    const current = msg.data?.total_revenue || 0;

    setRevenue(current);

    setTrendData(prev => {
        const lastRaw = prev.length > 0 ? prev[prev.length - 1].raw || 0 : 0;

        return [
            ...prev.slice(-49),
            {
                time: prev.length,
                revenue: current - lastRaw, // ✅ incremental change
                raw: current               // ✅ keep absolute
            }
        ];
    });
}
        };

        return () => ws.close();
    }, []);

    const churnData = [
        { name: "High", value: churn?.high || 0 },
        { name: "Medium", value: churn?.medium || 0 },
        { name: "Low", value: churn?.low || 0 },
    ];

    const perfData = (performance || []).map((p, i) => ({
    time: i,
    f1: (p?.f1_score || 0) - 0.99  // normalize
}));


    return (
        <div className="bg-zinc-950 text-white h-screen p-4 flex flex-col gap-4 overflow-hidden">

            {/* HEADER */}
            <div className="flex justify-between items-center">
                <h1 className="text-xl font-bold">Customer Churn Monitoring</h1>
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
             <div className="grid grid-cols-5 gap-4 flex-1 overflow-hidden min-h-0">

                {/* LEFT (UNCHANGED FULLY) */}
                <div className="col-span-3 grid grid-rows-2 gap-4 min-h-0">

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

                                <div className="flex justify-around text-xs mt-2">
                                    {churnData.map((c, i) => (
                                        <div key={i} className="flex items-center gap-1">
                                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                                            <span className="text-gray-400">{c.name}</span>
                                            <span>{c.value}</span>
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
                                    {models.map((m, i) => {

                                        const f1 = (m.f1_score ?? 0).toFixed(3);
                                        const auc = (m.roc_auc ?? 0).toFixed(3);

                                        const date = m.created_at
                                            ? new Date(m.created_at).toLocaleDateString("en-US", {
                                                month: "short",
                                                day: "numeric",
                                                year: "numeric"
                                            })
                                            : "N/A";

                                        return (
                                            <div key={i} className="flex justify-between gap-2 text-gray-300">
                                                <span className="truncate max-w-[40%]">
                                                    {m.model_version}
                                                </span>

                                                <span className="text-gray-400">
                                                    F1: <span className="text-white">{f1}</span>
                                                </span>

                                                <span className="text-gray-400">
                                                    AUC: <span className="text-white">{auc}</span>
                                                </span>

                                                <span className="text-gray-500">
                                                    {date}
                                                </span>
                                            </div>
                                        );
                                    })}
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
                                    <Area  type="monotone" dataKey="revenue" stroke="#3b82f6" fill="#3b82f633" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </Card>

                        <Card>
                            <h2>Model F1</h2>
                            <ResponsiveContainer width="100%" height={180}>
                                <AreaChart data={perfData}>
                                    <XAxis hide />
                                    <YAxis domain={[0.98, 1]} hide />
                                    <Tooltip content={<DarkTooltip />} />
                                    <Area dataKey="f1" stroke="#22c55e" fill="#22c55e33" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </Card>
                    </div>
                </div>

                {/* RIGHT WITH DROPDOWN */}
                <div className="col-span-2 flex flex-col overflow-hidden min-h-0">

                    <Card className="flex flex-col flex-1 overflow-hidden min-h-0">

                        <div className="flex justify-between items-center mb-2">
                            <h2>
                                {customerType === "risk" ? "High Risk Customers" : "Highly Active Customers"}
                            </h2>

                            <select
                                value={customerType}
                                onChange={(e) => handleTypeChange(e.target.value)}
                                className="bg-zinc-700 text-xs p-1 rounded"
                            >
                                <option value="active">Active</option>
                                <option value="risk">High Risk</option>
                            </select>
                        </div>

                        <div
                            ref={listRef}
                            onScroll={handleScroll}
                            className="overflow-y-auto flex-1 space-y-2 pr-2 min-h-0"
                        >

                            {customers.map(c => (
                                <div
                                    key={c.customer_id}
                                    onClick={() => setSelectedCustomer(c)}
                                    className="p-3 bg-zinc-800 rounded hover:bg-zinc-700 cursor-pointer"
                                >
                                    <div className="flex justify-between">
                                        <span>{c.customer || c.contact_name}</span>

                                        <span className={
                                            customerType === "risk"
                                                ? "text-red-400"
                                                : "text-green-400"
                                        }>
                                            {customerType === "risk"
                                                ? `${((c.churn_probability || 0) * 100).toFixed(1)}%`
                                                : `${c.total_orders} orders`}
                                        </span>
                                    </div>

                                    <div className="text-xs text-gray-400">
                                        {c.industry} • ${c.total_sales}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Card>
                </div>
            </div>

            {/* DETAILS */}
            {selectedCustomer && (
                <div className="grid grid-cols-5 gap-4 h-[200px] min-h-0">

                    <div className="col-span-2">
                        <Card>
                            <h2>Customer</h2>
                            <div className="grid grid-cols-3 gap-2 mt-2">
                                <Info label="Orders" value={selectedCustomer.total_orders} />
                                <Info label="Sales" value={selectedCustomer.total_sales.toFixed(3)} />
                                <Info label="Avg Value" value={selectedCustomer.avg_order_value.toFixed(3)} />
                                <Info label="Customer" value={selectedCustomer.customer} />
                                <Info label="Industry" value={selectedCustomer.industry} />
                                <Info label="Segment" value={selectedCustomer.segment} />
                            </div>
                        </Card>
                    </div>

                    {/* ORDERS SAME AS BEFORE */}
                    <div className="col-span-3 flex flex-col overflow-hidden min-h-0">

                    <Card className="flex flex-col h-full">
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
                            <div className="flex-1 overflow-y-auto mt-2 space-y-1 pr-1 min-h-0">

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
            <div className="flex items-center justify-between">

                {/* LEFT TEXT */}
                <div>
                    <p className="text-xs text-gray-400 mb-1">{title}</p>

                    {/* 🔥 BIG VALUE */}
                    <p className="text-2xl font-semibold text-white leading-tight">
                        {value}
                    </p>

                    {/* SUBTEXT */}
                    {sub && (
                        <p className="text-xs text-gray-500 mt-1">
                            {sub}
                        </p>
                    )}
                </div>

                {/* ICON (NO BACKGROUND) */}
                <div className="text-gray-400 opacity-80">
                    {React.cloneElement(icon, { size: 22 })}
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
