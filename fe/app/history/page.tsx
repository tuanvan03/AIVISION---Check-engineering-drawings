"use client"

import { useState } from "react"
import Link from "next/link"
import { 
  Search, 
  Filter, 
  FileType, 
  Clock, 
  AlertCircle, 
  AlertTriangle, 
  Info,
  MoreVertical,
  Trash2,
  Eye,
  Download,
  LayoutGrid,
  List,
  ChevronLeft,
  ChevronRight
} from "lucide-react"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"

interface HistoryItem {
  id: string
  fileName: string
  fileSize: string
  drawingType: string
  analyzedAt: Date
  errors: {
    critical: number
    warning: number
    info: number
  }
}

const mockHistory: HistoryItem[] = [
  {
    id: "1",
    fileName: "bracket_assembly_v2.dxf",
    fileSize: "2.4 MB",
    drawingType: "Cơ khí",
    analyzedAt: new Date(Date.now() - 1000 * 60 * 30),
    errors: { critical: 1, warning: 2, info: 3 },
  },
  {
    id: "2",
    fileName: "housing_cover.dxf",
    fileSize: "1.8 MB",
    drawingType: "Cơ khí",
    analyzedAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
    errors: { critical: 0, warning: 1, info: 2 },
  },
  {
    id: "3",
    fileName: "floor_plan_office.dxf",
    fileSize: "5.2 MB",
    drawingType: "Kiến trúc",
    analyzedAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
    errors: { critical: 2, warning: 0, info: 1 },
  },
  {
    id: "4",
    fileName: "shaft_coupling.dxf",
    fileSize: "890 KB",
    drawingType: "Cơ khí",
    analyzedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2),
    errors: { critical: 0, warning: 0, info: 4 },
  },
  {
    id: "5",
    fileName: "electrical_panel.dxf",
    fileSize: "3.1 MB",
    drawingType: "Điện",
    analyzedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3),
    errors: { critical: 1, warning: 3, info: 0 },
  },
  {
    id: "6",
    fileName: "pipe_system_layout.dxf",
    fileSize: "4.7 MB",
    drawingType: "Đường ống",
    analyzedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5),
    errors: { critical: 0, warning: 2, info: 2 },
  },
]

function formatTimeAgo(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 60) return `${minutes} phút trước`
  if (hours < 24) return `${hours} giờ trước`
  return `${days} ngày trước`
}

export default function HistoryPage() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [searchQuery, setSearchQuery] = useState("")
  const [filterType, setFilterType] = useState<string>("all")
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 6

  const filteredHistory = mockHistory.filter((item) => {
    const matchesSearch = item.fileName.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === "all" || item.drawingType === filterType
    return matchesSearch && matchesType
  })

  const totalPages = Math.ceil(filteredHistory.length / itemsPerPage)
  const paginatedHistory = filteredHistory.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const getDrawingTypeColor = (type: string) => {
    switch (type) {
      case "Cơ khí":
        return "bg-blue-500/10 text-blue-600 dark:text-blue-400"
      case "Kiến trúc":
        return "bg-green-500/10 text-green-600 dark:text-green-400"
      case "Điện":
        return "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400"
      case "Đường ống":
        return "bg-purple-500/10 text-purple-600 dark:text-purple-400"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Lịch sử phân tích</h1>
          <p className="text-muted-foreground">
            Xem lại các bản vẽ đã được kiểm tra và báo cáo lỗi chi tiết
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Tìm kiếm bản vẽ..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-11"
            />
          </div>
          <div className="flex gap-2">
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[160px] h-11">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Loại bản vẽ" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tất cả</SelectItem>
                <SelectItem value="Cơ khí">Cơ khí</SelectItem>
                <SelectItem value="Kiến trúc">Kiến trúc</SelectItem>
                <SelectItem value="Điện">Điện</SelectItem>
                <SelectItem value="Đường ống">Đường ống</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex border rounded-lg overflow-hidden">
              <Button
                variant={viewMode === "grid" ? "secondary" : "ghost"}
                size="icon"
                className="h-11 w-11 rounded-none"
                onClick={() => setViewMode("grid")}
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "secondary" : "ghost"}
                size="icon"
                className="h-11 w-11 rounded-none"
                onClick={() => setViewMode("list")}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Results Count */}
        <p className="text-sm text-muted-foreground mb-4">
          Hiển thị {paginatedHistory.length} trong tổng số {filteredHistory.length} bản vẽ
        </p>

        {/* History Items */}
        {paginatedHistory.length === 0 ? (
          <Card className="py-16">
            <CardContent className="flex flex-col items-center justify-center text-center">
              <div className="h-16 w-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
                <FileType className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="font-medium mb-1">Không tìm thấy bản vẽ</h3>
              <p className="text-sm text-muted-foreground max-w-[300px]">
                Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm
              </p>
            </CardContent>
          </Card>
        ) : viewMode === "grid" ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {paginatedHistory.map((item) => (
              <Card key={item.id} className="group hover:shadow-lg hover:shadow-primary/5 transition-all duration-200">
                <CardContent className="p-5">
                  {/* File Info */}
                  <div className="flex items-start gap-3 mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
                      <FileType className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium truncate mb-1" title={item.fileName}>
                        {item.fileName}
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{item.fileSize}</span>
                        <span>•</span>
                        <Badge variant="secondary" className={cn("text-xs", getDrawingTypeColor(item.drawingType))}>
                          {item.drawingType}
                        </Badge>
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Eye className="h-4 w-4 mr-2" />
                          Xem chi tiết
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="h-4 w-4 mr-2" />
                          Tải báo cáo
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive focus:text-destructive">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Xóa
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  {/* Time */}
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-4">
                    <Clock className="h-3.5 w-3.5" />
                    <span>{formatTimeAgo(item.analyzedAt)}</span>
                  </div>

                  {/* Error Summary */}
                  <div className="flex items-center gap-3 pt-3 border-t">
                    <div className="flex items-center gap-1.5">
                      <AlertCircle className="h-4 w-4 text-destructive" />
                      <span className="text-sm font-medium">{item.errors.critical}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <AlertTriangle className="h-4 w-4 text-warning" />
                      <span className="text-sm font-medium">{item.errors.warning}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Info className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">{item.errors.info}</span>
                    </div>
                    <div className="flex-1" />
                    <Link href={`/analysis?id=${item.id}`}>
                      <Button variant="ghost" size="sm" className="h-8 text-primary hover:text-primary">
                        Xem lại
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {paginatedHistory.map((item) => (
              <Card key={item.id} className="group hover:shadow-lg hover:shadow-primary/5 transition-all duration-200">
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    {/* File Icon */}
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
                      <FileType className="h-6 w-6 text-primary" />
                    </div>

                    {/* File Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium truncate" title={item.fileName}>
                        {item.fileName}
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{item.fileSize}</span>
                        <span>•</span>
                        <Badge variant="secondary" className={cn("text-xs", getDrawingTypeColor(item.drawingType))}>
                          {item.drawingType}
                        </Badge>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          {formatTimeAgo(item.analyzedAt)}
                        </span>
                      </div>
                    </div>

                    {/* Error Summary */}
                    <div className="hidden sm:flex items-center gap-4">
                      <div className="flex items-center gap-1.5">
                        <AlertCircle className="h-4 w-4 text-destructive" />
                        <span className="text-sm font-medium">{item.errors.critical}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <AlertTriangle className="h-4 w-4 text-warning" />
                        <span className="text-sm font-medium">{item.errors.warning}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Info className="h-4 w-4 text-primary" />
                        <span className="text-sm font-medium">{item.errors.info}</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <Link href={`/analysis?id=${item.id}`}>
                        <Button variant="outline" size="sm" className="h-9">
                          Xem lại
                        </Button>
                      </Link>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-9 w-9">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Download className="h-4 w-4 mr-2" />
                            Tải báo cáo
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive focus:text-destructive">
                            <Trash2 className="h-4 w-4 mr-2" />
                            Xóa
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <Button
                key={page}
                variant={currentPage === page ? "default" : "outline"}
                size="icon"
                className="h-9 w-9"
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </Button>
            ))}
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </main>
    </div>
  )
}
