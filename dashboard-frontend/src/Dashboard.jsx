import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { Activity, AlertTriangle, Users, DollarSign, Brain } from "lucide-react";

// -----------------------------
// WebSocket URL (Docker compatible)
// -----------------------------
const WS_URL = "ws://localhost:8000/ws/dashboard";

const Card = ({ children, className }) => (
  <div
    className={`bg-zinc-800 border border-zinc-700 rounded-2xl shadow-md ${className}`}
  >
    {children}
  </div>
);

const CardContent = ({ children, className }) => (
  <div className={`p-4 ${className}`}>{children}</div>
);

const Badge = ({ children }) => (
  <div className="bg-green-600 px-4 py-1 rounded-full text-sm font-semibold">
    {children}
  </div>
);

// -----------------------------
// Main Component
// -----------------------------
export default function Dashboard() {
  const [drift, setDrift] = useState({ drift_detected: false, drift_score: 0 });
  const [churn, setChurn] = useState({ high: 0, medium: 0, low: 0 });
  const [model, setModel] = useState({ model_version: "v1", f1: 0 });
  const [revenue, setRevenue] = useState(0);
  const [trendData, setTrendData] = useState([]);

  // -----------------------------
  // WebSocket Connection
  // -----------------------------
  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log("WebSocket connected!");
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.event === "drift_update") setDrift(msg.data);
      if (msg.event === "churn_update") setChurn(msg.data);
      if (msg.event === "model_update") setModel(msg.data);
      if (msg.event === "business_update") {
        setRevenue(msg.data.total_revenue);
        setTrendData((prev) => [
          ...prev.slice(-9),
          { time: new Date().toLocaleTimeString(), revenue: msg.data.total_revenue },
        ]);
      }
    };

    ws.onclose = () => console.log("WebSocket disconnected");
    return () => ws.close();
  }, []);

  const churnData = [
    { name: "High", value: churn.high },
    { name: "Medium", value: churn.medium },
    { name: "Low", value: churn.low },
  ];
  const COLORS = ["#ef4444", "#f59e0b", "#22c55e"];

  return (
    <div className="bg-zinc-950 text-white min-h-screen p-6 grid grid-rows-[auto_auto_1fr] gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI Monitoring Dashboard</h1>
          <p className="text-gray-400 text-sm">
            Real-time churn, drift & business analytics
          </p>
        </div>
        <Badge>Live</Badge>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-4 gap-6">
        <MetricCard
          icon={<DollarSign />}
          title="Total Revenue"
          value={`$${revenue.toLocaleString()}`}
        />
        <MetricCard
          icon={<Brain />}
          title="Model Version"
          value={model.model_version}
          subtitle={`F1 Score: ${model.f1}`}
        />
        <MetricCard
          icon={<AlertTriangle />}
          title="Drift Score"
          value={drift.drift_score.toFixed(2)}
          subtitle={drift.drift_detected ? "Drift Detected" : "Stable"}
        />
        <MetricCard
          icon={<Users />}
          title="High Risk Customers"
          value={churn.high}
          subtitle="Churn > 0.7"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-3 gap-6 h-full">
        {/* Revenue Trend */}
        <Card className="col-span-2 h-full">
          <CardContent className="h-full">
            <h2 className="text-lg font-semibold mb-4">Revenue Trend (Live)</h2>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <XAxis dataKey="time" stroke="#888" />
                <YAxis stroke="#888" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1f2937", borderRadius: 8 }}
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Churn Distribution */}
        <Card className="h-full">
          <CardContent className="h-full">
            <h2 className="text-lg font-semibold mb-4">Churn Distribution</h2>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={churnData}
                  dataKey="value"
                  outerRadius={80}
                  innerRadius={30}
                  paddingAngle={4}
                  label
                >
                  {churnData.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Activity Feed */}
        <Card className="col-span-3 h-full">
          <CardContent>
            <h2 className="text-lg font-semibold mb-4">Live System Activity</h2>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <ActivityItem title="Model" value={model.model_version} />
              <ActivityItem title="Drift" value={drift.drift_score.toFixed(2)} />
              <ActivityItem title="Revenue" value={`$${revenue.toLocaleString()}`} />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// -----------------------------
// Metric Card
// -----------------------------
function MetricCard({ icon, title, value, subtitle }) {
  return (
    <Card>
      <CardContent className="p-4 flex items-center gap-4">
        <div className="bg-zinc-700 p-3 rounded-2xl">{icon}</div>
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <h2 className="text-2xl font-bold">{value}</h2>
          {subtitle && <p className="text-gray-500 text-xs">{subtitle}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

// -----------------------------
// Activity Item
// -----------------------------
function ActivityItem({ title, value }) {
  return (
    <div className="bg-zinc-700 p-4 rounded-xl">
      <p className="text-gray-400">{title}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}