"use client"

import { useState, useMemo } from "react"
import { 
  Search, 
  Download,
  Filter,
  ChevronLeft,
  ChevronRight,
  Calendar,
  Info,
  AlertTriangle,
  XCircle,
  RefreshCw
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

// Mock log data
const mockLogs = [
  { id: 1, timestamp: "04/05/2026 14:32:15", user: "nguyen.van.a@email.com", ip: "192.168.1.105", event: "Đăng nhập thành công", level: "info" },
  { id: 2, timestamp: "04/05/2026 14:30:42", user: "tran.thi.b@email.com", ip: "192.168.1.108", event: "Phân tích bản vẽ: floor_plan_v2.dwg", level: "info" },
  { id: 3, timestamp: "04/05/2026 14:28:19", user: "System", ip: "-", event: "Không thể kết nối đến AI Service - timeout sau 30s", level: "error" },
  { id: 4, timestamp: "04/05/2026 14:25:33", user: "le.van.c@email.com", ip: "192.168.1.112", event: "Đăng nhập thất bại - sai mật khẩu (lần 3)", level: "warning" },
  { id: 5, timestamp: "04/05/2026 14:22:48", user: "pham.thi.d@email.com", ip: "192.168.1.115", event: "Tải lên bản vẽ: electrical_diagram.pdf", level: "info" },
  { id: 6, timestamp: "04/05/2026 14:20:11", user: "hoang.van.e@email.com", ip: "192.168.1.118", event: "Cập nhật thông tin hồ sơ", level: "info" },
  { id: 7, timestamp: "04/05/2026 14:18:55", user: "System", ip: "-", event: "Dung lượng lưu trữ đạt 85% - cần dọn dẹp", level: "warning" },
  { id: 8, timestamp: "04/05/2026 14:15:32", user: "admin@aivision.com", ip: "192.168.1.100", event: "Thay đổi quota cho user: vo.thi.f@email.com (20 -> 30)", level: "info" },
  { id: 9, timestamp: "04/05/2026 14:12:18", user: "vo.thi.f@email.com", ip: "192.168.1.120", event: "Phân tích bản vẽ: hvac_system.dwg", level: "info" },
  { id: 10, timestamp: "04/05/2026 14:10:45", user: "System", ip: "-", event: "Lỗi xử lý file: Định dạng không hỗ trợ (.psd)", level: "error" },
  { id: 11, timestamp: "04/05/2026 14:08:22", user: "dang.van.g@email.com", ip: "192.168.1.125", event: "Đăng ký tài khoản mới", level: "info" },
  { id: 12, timestamp: "04/05/2026 14:05:19", user: "bui.thi.h@email.com", ip: "192.168.1.128", event: "Yêu cầu đặt lại mật khẩu", level: "info" },
  { id: 13, timestamp: "04/05/2026 14:02:55", user: "System", ip: "-", event: "Tự động backup database hoàn tất", level: "info" },
  { id: 14, timestamp: "04/05/2026 14:00:11", user: "do.van.i@email.com", ip: "192.168.1.130", event: "Đăng xuất", level: "info" },
  { id: 15, timestamp: "04/05/2026 13:58:48", user: "admin@aivision.com", ip: "192.168.1.100", event: "Khóa tài khoản: le.van.c@email.com", level: "warning" },
  { id: 16, timestamp: "04/05/2026 13:55:32", user: "ngo.thi.k@email.com", ip: "192.168.1.135", event: "Phân tích bản vẽ: structural_design.pdf", level: "info" },
  { id: 17, timestamp: "04/05/2026 13:52:19", user: "System", ip: "-", event: "Rate limit exceeded cho IP 192.168.1.140", level: "warning" },
  { id: 18, timestamp: "04/05/2026 13:50:45", user: "duong.van.l@email.com", ip: "192.168.1.140", event: "Phân tích bản vẽ: plumbing_layout.dwg", level: "info" },
]

export default function SystemLogs() {
  const [searchQuery, setSearchQuery] = useState("")
  const [levelFilter, setLevelFilter] = useState("all")
  const [dateFilter, setDateFilter] = useState("today")
  const [currentPage, setCurrentPage] = useState(1)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const itemsPerPage = 10

  // Filter logs
  const filteredLogs = useMemo(() => {
    return mockLogs.filter((log) => {
      const matchesSearch = 
        log.user.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.event.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.ip.includes(searchQuery)
      const matchesLevel = levelFilter === "all" || log.level === levelFilter
      return matchesSearch && matchesLevel
    })
  }, [searchQuery, levelFilter])

  // Pagination
  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage)
  const paginatedLogs = filteredLogs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  // Stats
  const stats = {
    total: mockLogs.length,
    info: mockLogs.filter(l => l.level === "info").length,
    warning: mockLogs.filter(l => l.level === "warning").length,
    error: mockLogs.filter(l => l.level === "error").length,
  }

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  const handleExport = () => {
    // Export logic would go here
    alert("Đang xuất file CSV...")
  }

  const getLevelIcon = (level: string) => {
    switch (level) {
      case "info":
        return <Info className="w-4 h-4 text-blue-500" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-amber-500" />
      case "error":
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <Info className="w-4 h-4" />
    }
  }

  const getLevelBadge = (level: string) => {
    switch (level) {
      case "info":
        return <Badge variant="outline" className="border-blue-500 text-blue-500 text-xs">Info</Badge>
      case "warning":
        return <Badge variant="outline" className="border-amber-500 text-amber-500 text-xs">Warning</Badge>
      case "error":
        return <Badge variant="outline" className="border-red-500 text-red-500 text-xs">Error</Badge>
      default:
        return <Badge variant="outline" className="text-xs">Unknown</Badge>
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Nhật ký hệ thống</h1>
          <p className="text-sm text-muted-foreground">Theo dõi và giám sát hoạt động hệ thống</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
            Làm mới
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Xuất CSV
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-border">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
              <Info className="w-5 h-5 text-muted-foreground" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{stats.total}</p>
              <p className="text-xs text-muted-foreground">Tổng số log</p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Info className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{stats.info}</p>
              <p className="text-xs text-muted-foreground">Bình thường</p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{stats.warning}</p>
              <p className="text-xs text-muted-foreground">Cảnh báo</p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
              <XCircle className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{stats.error}</p>
              <p className="text-xs text-muted-foreground">Lỗi</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="border-border">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Tìm kiếm theo người dùng, sự kiện, IP..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value)
                  setCurrentPage(1)
                }}
                className="pl-9"
              />
            </div>

            {/* Filters */}
            <div className="flex gap-3">
              <Select value={dateFilter} onValueChange={setDateFilter}>
                <SelectTrigger className="w-[150px]">
                  <Calendar className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Thời gian" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="today">Hôm nay</SelectItem>
                  <SelectItem value="yesterday">Hôm qua</SelectItem>
                  <SelectItem value="7days">7 ngày qua</SelectItem>
                  <SelectItem value="30days">30 ngày qua</SelectItem>
                  <SelectItem value="all">Tất cả</SelectItem>
                </SelectContent>
              </Select>

              <Select value={levelFilter} onValueChange={(v) => { setLevelFilter(v); setCurrentPage(1) }}>
                <SelectTrigger className="w-[140px]">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Mức độ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  <SelectItem value="info">Bình thường</SelectItem>
                  <SelectItem value="warning">Cảnh báo</SelectItem>
                  <SelectItem value="error">Lỗi</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card className="border-border">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3 w-10"></th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Thời gian</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Người dùng</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">IP</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Sự kiện</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Mức độ</th>
                </tr>
              </thead>
              <tbody>
                {paginatedLogs.map((log) => (
                  <tr 
                    key={log.id} 
                    className={`border-b border-border hover:bg-muted/30 transition-colors ${
                      log.level === "error" ? "bg-red-500/5" : 
                      log.level === "warning" ? "bg-amber-500/5" : ""
                    }`}
                  >
                    <td className="px-4 py-3">
                      {getLevelIcon(log.level)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground font-mono">{log.timestamp}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-sm ${log.user === "System" ? "text-primary font-medium" : "text-foreground"}`}>
                        {log.user}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground font-mono">{log.ip}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-foreground">{log.event}</span>
                    </td>
                    <td className="px-4 py-3">
                      {getLevelBadge(log.level)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <p className="text-sm text-muted-foreground">
              Hiển thị {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, filteredLogs.length)} trong số {filteredLogs.length} bản ghi
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
                <Button
                  key={page}
                  variant={currentPage === page ? "default" : "outline"}
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setCurrentPage(page)}
                >
                  {page}
                </Button>
              ))}
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
