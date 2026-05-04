"use client"

import { useState } from "react"
import { 
  Users, 
  UserCheck, 
  FileSearch, 
  BarChart3,
  TrendingUp,
  TrendingDown,
  Calendar
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

// Mock data for chart
const chartData = [
  { date: "01/04", analyses: 45 },
  { date: "02/04", analyses: 52 },
  { date: "03/04", analyses: 38 },
  { date: "04/04", analyses: 65 },
  { date: "05/04", analyses: 48 },
  { date: "06/04", analyses: 72 },
  { date: "07/04", analyses: 58 },
  { date: "08/04", analyses: 43 },
  { date: "09/04", analyses: 67 },
  { date: "10/04", analyses: 82 },
  { date: "11/04", analyses: 75 },
  { date: "12/04", analyses: 91 },
  { date: "13/04", analyses: 68 },
  { date: "14/04", analyses: 54 },
  { date: "15/04", analyses: 79 },
  { date: "16/04", analyses: 86 },
  { date: "17/04", analyses: 62 },
  { date: "18/04", analyses: 95 },
  { date: "19/04", analyses: 88 },
  { date: "20/04", analyses: 73 },
  { date: "21/04", analyses: 102 },
  { date: "22/04", analyses: 97 },
  { date: "23/04", analyses: 84 },
  { date: "24/04", analyses: 110 },
  { date: "25/04", analyses: 98 },
  { date: "26/04", analyses: 89 },
  { date: "27/04", analyses: 115 },
  { date: "28/04", analyses: 108 },
  { date: "29/04", analyses: 92 },
  { date: "30/04", analyses: 125 },
]

const stats = [
  {
    title: "Tổng người dùng",
    value: "2,847",
    change: "+12.5%",
    trend: "up",
    icon: Users,
    description: "so với tháng trước",
  },
  {
    title: "Hoạt động 7 ngày",
    value: "1,234",
    change: "+8.2%",
    trend: "up",
    icon: UserCheck,
    description: "người dùng active",
  },
  {
    title: "Phân tích hôm nay",
    value: "342",
    change: "-3.1%",
    trend: "down",
    icon: FileSearch,
    description: "bản vẽ đã xử lý",
  },
  {
    title: "Phân tích tháng này",
    value: "8,492",
    change: "+24.7%",
    trend: "up",
    icon: BarChart3,
    description: "tổng lượt phân tích",
  },
]

// Recent activity mock data
const recentActivity = [
  { user: "nguyen.van.a@email.com", action: "Phân tích bản vẽ", time: "2 phút trước", type: "analysis" },
  { user: "tran.thi.b@email.com", action: "Đăng ký tài khoản", time: "5 phút trước", type: "register" },
  { user: "le.van.c@email.com", action: "Đăng nhập", time: "8 phút trước", type: "login" },
  { user: "pham.thi.d@email.com", action: "Phân tích bản vẽ", time: "12 phút trước", type: "analysis" },
  { user: "hoang.van.e@email.com", action: "Cập nhật hồ sơ", time: "15 phút trước", type: "update" },
]

export default function AdminDashboard() {
  const [timeRange] = useState("30days")

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Bảng điều khiển</h1>
          <p className="text-sm text-muted-foreground">Tổng quan hoạt động hệ thống</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg text-sm text-muted-foreground">
          <Calendar className="w-4 h-4" />
          <span>30 ngày gần nhất</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.title} className="border-border">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">{stat.title}</p>
                  <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                  <div className="flex items-center gap-1.5">
                    {stat.trend === "up" ? (
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                    ) : (
                      <TrendingDown className="w-3.5 h-3.5 text-red-500" />
                    )}
                    <span className={stat.trend === "up" ? "text-xs text-emerald-500" : "text-xs text-red-500"}>
                      {stat.change}
                    </span>
                    <span className="text-xs text-muted-foreground">{stat.description}</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <stat.icon className="w-5 h-5 text-primary" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Chart and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <Card className="lg:col-span-2 border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Xu hướng phân tích bản vẽ</CardTitle>
            <p className="text-xs text-muted-foreground">Số lượng bản vẽ được phân tích trong 30 ngày qua</p>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis 
                    tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    labelStyle={{ color: "hsl(var(--foreground))" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="analyses"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: "hsl(var(--primary))" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Hoạt động gần đây</CardTitle>
            <p className="text-xs text-muted-foreground">Các thao tác mới nhất trên hệ thống</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className={`w-2 h-2 rounded-full mt-1.5 ${
                    activity.type === "analysis" ? "bg-primary" :
                    activity.type === "register" ? "bg-emerald-500" :
                    activity.type === "login" ? "bg-blue-500" :
                    "bg-amber-500"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground truncate">{activity.user}</p>
                    <p className="text-xs text-muted-foreground">{activity.action}</p>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">{activity.time}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
