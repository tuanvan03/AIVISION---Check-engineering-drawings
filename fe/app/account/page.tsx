"use client"

import { useState, useEffect } from "react"
import { 
  User, 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  Camera,
  Zap,
  Clock,
  CheckCircle,
  Shield
} from "lucide-react"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function AccountPage() {
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [countdown, setCountdown] = useState({ hours: 5, minutes: 23, seconds: 45 })

  const [profile, setProfile] = useState({
    name: "Nguyễn Văn A",
    email: "nguyenvana@email.com",
  })

  const [passwords, setPasswords] = useState({
    current: "",
    new: "",
    confirm: "",
  })

  const quota = {
    used: 3,
    total: 10,
    resetTime: new Date(Date.now() + 1000 * 60 * 60 * 5.4), // ~5.4 hours from now
  }

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev.seconds > 0) {
          return { ...prev, seconds: prev.seconds - 1 }
        } else if (prev.minutes > 0) {
          return { ...prev, minutes: prev.minutes - 1, seconds: 59 }
        } else if (prev.hours > 0) {
          return { hours: prev.hours - 1, minutes: 59, seconds: 59 }
        }
        return prev
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const handleSaveProfile = async () => {
    setIsSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsSaving(false)
  }

  const handleChangePassword = async () => {
    setIsSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsSaving(false)
    setPasswords({ current: "", new: "", confirm: "" })
  }

  const formatCountdown = () => {
    const pad = (n: number) => n.toString().padStart(2, "0")
    return `${pad(countdown.hours)}:${pad(countdown.minutes)}:${pad(countdown.seconds)}`
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Tài khoản</h1>
          <p className="text-muted-foreground">
            Quản lý thông tin cá nhân và cài đặt bảo mật
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left Column - Profile Card */}
          <div className="lg:col-span-1 space-y-6">
            {/* Profile Overview */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex flex-col items-center text-center">
                  <div className="relative mb-4">
                    <Avatar className="h-24 w-24">
                      <AvatarImage src="" alt={profile.name} />
                      <AvatarFallback className="bg-primary/10 text-primary text-2xl font-medium">
                        {profile.name.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <button className="absolute bottom-0 right-0 h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-lg hover:bg-primary/90 transition-colors">
                      <Camera className="h-4 w-4" />
                    </button>
                  </div>
                  <h2 className="text-xl font-semibold">{profile.name}</h2>
                  <p className="text-sm text-muted-foreground">{profile.email}</p>
                  <div className="flex items-center gap-2 mt-3">
                    <div className="flex items-center gap-1 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm">
                      <CheckCircle className="h-3.5 w-3.5" />
                      <span>Tài khoản đã xác minh</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quota Card */}
            <Card className="overflow-hidden">
              <div className="bg-gradient-to-br from-primary/10 via-primary/5 to-transparent">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                      <Zap className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">Hạn mức sử dụng</CardTitle>
                      <CardDescription>Số lượt phân tích hôm nay</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-baseline justify-between mb-2">
                      <span className="text-3xl font-bold">{quota.total - quota.used}</span>
                      <span className="text-sm text-muted-foreground">/ {quota.total} lượt</span>
                    </div>
                    <Progress value={(quota.used / quota.total) * 100} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-2">
                      Đã sử dụng {quota.used} lượt hôm nay
                    </p>
                  </div>

                  <Separator />

                  {/* Countdown */}
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-accent flex items-center justify-center">
                      <Clock className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Cấp lại sau</p>
                      <p className="text-lg font-mono font-semibold tracking-wider">
                        {formatCountdown()}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </div>
            </Card>
          </div>

          {/* Right Column - Settings */}
          <div className="lg:col-span-2">
            <Card>
              <Tabs defaultValue="profile" className="w-full">
                <CardHeader className="pb-0">
                  <TabsList className="w-full justify-start h-auto p-0 bg-transparent border-b rounded-none">
                    <TabsTrigger
                      value="profile"
                      className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3 data-[state=active]:shadow-none"
                    >
                      <User className="h-4 w-4 mr-2" />
                      Thông tin cá nhân
                    </TabsTrigger>
                    <TabsTrigger
                      value="security"
                      className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3 data-[state=active]:shadow-none"
                    >
                      <Shield className="h-4 w-4 mr-2" />
                      Bảo mật
                    </TabsTrigger>
                  </TabsList>
                </CardHeader>

                <TabsContent value="profile" className="mt-0">
                  <CardContent className="pt-6 space-y-6">
                    {/* Name Field */}
                    <div className="space-y-2">
                      <Label htmlFor="name">Họ và tên</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="name"
                          value={profile.name}
                          onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                          className="pl-10 h-12"
                        />
                      </div>
                    </div>

                    {/* Email Field */}
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="email"
                          type="email"
                          value={profile.email}
                          onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                          className="pl-10 h-12"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Email này được sử dụng để đăng nhập và nhận thông báo
                      </p>
                    </div>

                    <div className="flex justify-end pt-4">
                      <Button 
                        onClick={handleSaveProfile} 
                        disabled={isSaving}
                        className="shadow-lg shadow-primary/25"
                      >
                        {isSaving ? (
                          <div className="flex items-center gap-2">
                            <div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                            Đang lưu...
                          </div>
                        ) : (
                          "Lưu thay đổi"
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </TabsContent>

                <TabsContent value="security" className="mt-0">
                  <CardContent className="pt-6 space-y-6">
                    <div className="rounded-xl bg-accent/50 p-4 border border-border/50">
                      <div className="flex items-start gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <Lock className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <h3 className="font-medium mb-1">Đổi mật khẩu</h3>
                          <p className="text-sm text-muted-foreground">
                            Để bảo mật tài khoản, hãy sử dụng mật khẩu mạnh với ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường và số.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Current Password */}
                    <div className="space-y-2">
                      <Label htmlFor="current-password">Mật khẩu hiện tại</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="current-password"
                          type={showCurrentPassword ? "text" : "password"}
                          value={passwords.current}
                          onChange={(e) => setPasswords({ ...passwords, current: e.target.value })}
                          className="pl-10 pr-10 h-12"
                          placeholder="••••••••"
                        />
                        <button
                          type="button"
                          onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {showCurrentPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* New Password */}
                    <div className="space-y-2">
                      <Label htmlFor="new-password">Mật khẩu mới</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="new-password"
                          type={showNewPassword ? "text" : "password"}
                          value={passwords.new}
                          onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
                          className="pl-10 pr-10 h-12"
                          placeholder="••••••••"
                        />
                        <button
                          type="button"
                          onClick={() => setShowNewPassword(!showNewPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {showNewPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Confirm Password */}
                    <div className="space-y-2">
                      <Label htmlFor="confirm-password">Xác nhận mật khẩu mới</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="confirm-password"
                          type="password"
                          value={passwords.confirm}
                          onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
                          className="pl-10 h-12"
                          placeholder="••••••••"
                        />
                      </div>
                      {passwords.new && passwords.confirm && passwords.new !== passwords.confirm && (
                        <p className="text-sm text-destructive">Mật khẩu xác nhận không khớp</p>
                      )}
                    </div>

                    <div className="flex justify-end pt-4">
                      <Button 
                        onClick={handleChangePassword}
                        disabled={isSaving || !passwords.current || !passwords.new || passwords.new !== passwords.confirm}
                        className="shadow-lg shadow-primary/25"
                      >
                        {isSaving ? (
                          <div className="flex items-center gap-2">
                            <div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                            Đang cập nhật...
                          </div>
                        ) : (
                          "Đổi mật khẩu"
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </TabsContent>
              </Tabs>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
