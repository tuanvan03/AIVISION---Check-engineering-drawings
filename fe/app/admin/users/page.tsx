"use client"

import { useState, useMemo } from "react"
import { 
  Search, 
  MoreHorizontal,
  Shield,
  ShieldOff,
  Lock,
  Unlock,
  History,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  UserCog
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

// Mock user data
const mockUsers = [
  { id: 1, email: "admin@aivision.com", name: "Nguyễn Văn Admin", role: "admin", joinDate: "01/01/2024", status: "active", usedToday: 15, quota: 100 },
  { id: 2, email: "nguyen.van.a@email.com", name: "Nguyễn Văn A", role: "user", joinDate: "15/02/2024", status: "active", usedToday: 8, quota: 20 },
  { id: 3, email: "tran.thi.b@email.com", name: "Trần Thị B", role: "user", joinDate: "20/02/2024", status: "active", usedToday: 12, quota: 20 },
  { id: 4, email: "le.van.c@email.com", name: "Lê Văn C", role: "user", joinDate: "01/03/2024", status: "locked", usedToday: 0, quota: 20 },
  { id: 5, email: "pham.thi.d@email.com", name: "Phạm Thị D", role: "admin", joinDate: "05/03/2024", status: "active", usedToday: 25, quota: 100 },
  { id: 6, email: "hoang.van.e@email.com", name: "Hoàng Văn E", role: "user", joinDate: "10/03/2024", status: "active", usedToday: 5, quota: 20 },
  { id: 7, email: "vo.thi.f@email.com", name: "Võ Thị F", role: "user", joinDate: "15/03/2024", status: "active", usedToday: 18, quota: 30 },
  { id: 8, email: "dang.van.g@email.com", name: "Đặng Văn G", role: "user", joinDate: "20/03/2024", status: "active", usedToday: 3, quota: 20 },
  { id: 9, email: "bui.thi.h@email.com", name: "Bùi Thị H", role: "user", joinDate: "25/03/2024", status: "locked", usedToday: 0, quota: 20 },
  { id: 10, email: "do.van.i@email.com", name: "Đỗ Văn I", role: "user", joinDate: "01/04/2024", status: "active", usedToday: 7, quota: 20 },
  { id: 11, email: "ngo.thi.k@email.com", name: "Ngô Thị K", role: "user", joinDate: "05/04/2024", status: "active", usedToday: 11, quota: 20 },
  { id: 12, email: "duong.van.l@email.com", name: "Dương Văn L", role: "user", joinDate: "10/04/2024", status: "active", usedToday: 2, quota: 20 },
]

export default function UsersManagement() {
  const [searchQuery, setSearchQuery] = useState("")
  const [roleFilter, setRoleFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [currentPage, setCurrentPage] = useState(1)
  const [quotaDialog, setQuotaDialog] = useState<{ open: boolean; user: typeof mockUsers[0] | null }>({ open: false, user: null })
  const [lockDialog, setLockDialog] = useState<{ open: boolean; user: typeof mockUsers[0] | null }>({ open: false, user: null })
  const [newQuota, setNewQuota] = useState("")

  const itemsPerPage = 8

  // Filter and search users
  const filteredUsers = useMemo(() => {
    return mockUsers.filter((user) => {
      const matchesSearch = 
        user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesRole = roleFilter === "all" || user.role === roleFilter
      const matchesStatus = statusFilter === "all" || user.status === statusFilter
      return matchesSearch && matchesRole && matchesStatus
    })
  }, [searchQuery, roleFilter, statusFilter])

  // Pagination
  const totalPages = Math.ceil(filteredUsers.length / itemsPerPage)
  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const handleQuotaChange = () => {
    // API call would go here
    setQuotaDialog({ open: false, user: null })
    setNewQuota("")
  }

  const handleLockToggle = () => {
    // API call would go here
    setLockDialog({ open: false, user: null })
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Quản lý người dùng</h1>
        <p className="text-sm text-muted-foreground">Quản lý tài khoản và phân quyền người dùng</p>
      </div>

      {/* Filters */}
      <Card className="border-border">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Tìm kiếm theo tên hoặc email..."
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
              <Select value={roleFilter} onValueChange={(v) => { setRoleFilter(v); setCurrentPage(1) }}>
                <SelectTrigger className="w-[140px]">
                  <SlidersHorizontal className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Vai trò" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả vai trò</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                </SelectContent>
              </Select>

              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setCurrentPage(1) }}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  <SelectItem value="active">Hoạt động</SelectItem>
                  <SelectItem value="locked">Đã khóa</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="border-border">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Người dùng</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Vai trò</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Ngày tham gia</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Trạng thái</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Sử dụng hôm nay</th>
                  <th className="text-right text-xs font-medium text-muted-foreground px-4 py-3">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {paginatedUsers.map((user) => (
                  <tr key={user.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">{user.name}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge 
                        variant={user.role === "admin" ? "default" : "secondary"}
                        className={user.role === "admin" ? "bg-primary" : ""}
                      >
                        {user.role === "admin" ? "Admin" : "User"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground">{user.joinDate}</span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge 
                        variant="outline"
                        className={user.status === "active" 
                          ? "border-emerald-500 text-emerald-500" 
                          : "border-red-500 text-red-500"
                        }
                      >
                        {user.status === "active" ? "Hoạt động" : "Đã khóa"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary rounded-full"
                            style={{ width: `${Math.min((user.usedToday / user.quota) * 100, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {user.usedToday}/{user.quota}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-48">
                          <DropdownMenuItem onClick={() => { setQuotaDialog({ open: true, user }); setNewQuota(user.quota.toString()) }}>
                            <UserCog className="w-4 h-4 mr-2" />
                            Thay đổi quota
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            {user.role === "admin" ? (
                              <>
                                <ShieldOff className="w-4 h-4 mr-2" />
                                Hạ cấp xuống User
                              </>
                            ) : (
                              <>
                                <Shield className="w-4 h-4 mr-2" />
                                Nâng cấp lên Admin
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => setLockDialog({ open: true, user })}>
                            {user.status === "active" ? (
                              <>
                                <Lock className="w-4 h-4 mr-2" />
                                Khóa tài khoản
                              </>
                            ) : (
                              <>
                                <Unlock className="w-4 h-4 mr-2" />
                                Mở khóa tài khoản
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <History className="w-4 h-4 mr-2" />
                            Xem lịch sử phân tích
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <p className="text-sm text-muted-foreground">
              Hiển thị {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, filteredUsers.length)} trong số {filteredUsers.length} người dùng
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
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
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

      {/* Quota Dialog */}
      <Dialog open={quotaDialog.open} onOpenChange={(open) => setQuotaDialog({ open, user: quotaDialog.user })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thay đổi giới hạn sử dụng</DialogTitle>
            <DialogDescription>
              Điều chỉnh số lượt phân tích tối đa mỗi ngày cho {quotaDialog.user?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm font-medium text-foreground">Quota mới (lượt/ngày)</label>
            <Input
              type="number"
              value={newQuota}
              onChange={(e) => setNewQuota(e.target.value)}
              className="mt-2"
              min={1}
              max={1000}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setQuotaDialog({ open: false, user: null })}>
              Hủy
            </Button>
            <Button onClick={handleQuotaChange}>Lưu thay đổi</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Lock/Unlock Dialog */}
      <Dialog open={lockDialog.open} onOpenChange={(open) => setLockDialog({ open, user: lockDialog.user })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {lockDialog.user?.status === "active" ? "Khóa tài khoản" : "Mở khóa tài khoản"}
            </DialogTitle>
            <DialogDescription>
              {lockDialog.user?.status === "active" 
                ? `Bạn có chắc chắn muốn khóa tài khoản của ${lockDialog.user?.name}? Người dùng sẽ không thể đăng nhập cho đến khi được mở khóa.`
                : `Bạn có chắc chắn muốn mở khóa tài khoản của ${lockDialog.user?.name}?`
              }
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setLockDialog({ open: false, user: null })}>
              Hủy
            </Button>
            <Button 
              variant={lockDialog.user?.status === "active" ? "destructive" : "default"}
              onClick={handleLockToggle}
            >
              {lockDialog.user?.status === "active" ? "Khóa tài khoản" : "Mở khóa"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
