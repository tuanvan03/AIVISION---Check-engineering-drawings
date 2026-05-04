"use client"

import Link from "next/link"
import { useTheme } from "next-themes"
import { 
  Eye, 
  Scan, 
  FileCheck, 
  MessageSquare, 
  Shield, 
  Zap, 
  ArrowRight,
  CheckCircle,
  Moon,
  Sun,
  Upload,
  Search,
  Bot,
  FileText
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function HomePage() {
  const { theme, setTheme } = useTheme()

  const features = [
    {
      icon: Eye,
      title: "Đôi Mắt AI Tinh Tường",
      description: "AI tự động chuyển đổi file DXF thành hình ảnh chất lượng cao, phân biệt rõ ràng đường bao, kích thước và khung tên.",
    },
    {
      icon: FileCheck,
      title: "Tri Thức Chuẩn ISO",
      description: "Được nạp sẵn 7 tài liệu chuẩn ISO quốc tế, trích dẫn chính xác điều khoản khi phát hiện lỗi.",
    },
    {
      icon: Shield,
      title: "Tự Kiểm Tra Kép",
      description: "AI tự động phóng to vùng nghi ngờ và xác minh lại trước khi báo cáo, loại bỏ tối đa cảnh báo sai.",
    },
    {
      icon: MessageSquare,
      title: "Chat Trực Tiếp với AI",
      description: "Hỏi đáp chi tiết về lỗi, tiêu chuẩn ISO và cách khắc phục ngay trong ứng dụng.",
    },
  ]

  const steps = [
    {
      number: "01",
      icon: Upload,
      title: "Tải lên",
      description: "Kéo thả file bản vẽ DXF, DWG hoặc PDF vào hệ thống",
    },
    {
      number: "02",
      icon: Search,
      title: "Xác nhận",
      description: "Chọn loại bản vẽ: Cơ khí, Kiến trúc, Điện...",
    },
    {
      number: "03",
      icon: Bot,
      title: "Phân tích",
      description: "AI quét tổng thể và đối chiếu tiêu chuẩn",
    },
    {
      number: "04",
      icon: FileText,
      title: "Báo cáo",
      description: "Nhận kết quả chi tiết và chat để đào sâu vấn đề",
    },
  ]

  const standards = ["ISO 129-1", "ISO 1101", "ASME Y14.5", "ISO 286", "ISO 2768", "ISO 5459", "ISO 1302"]

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/25">
              <Eye className="h-5 w-5" />
            </div>
            <div className="hidden sm:block">
              <span className="text-lg font-semibold tracking-tight">AI Vision</span>
              <span className="ml-1 text-sm text-muted-foreground">Drawing Checker</span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="h-9 w-9 rounded-lg"
            >
              <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            </Button>
            <Link href="/login">
              <Button variant="ghost" className="h-9">Đăng nhập</Button>
            </Link>
            <Link href="/register">
              <Button className="h-9 shadow-lg shadow-primary/25">
                Bắt đầu miễn phí
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23000%22%20fill-opacity%3D%220.02%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%221.5%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E')]" />
        
        <div className="container mx-auto px-4 py-20 md:py-32 relative">
          <div className="max-w-4xl mx-auto text-center">
            <Badge variant="secondary" className="mb-6 px-4 py-1.5 text-sm font-medium">
              <Zap className="h-3.5 w-3.5 mr-1.5 text-primary" />
              10 lượt phân tích miễn phí mỗi ngày
            </Badge>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6 text-balance">
              Thẩm định bản vẽ kỹ thuật bằng{" "}
              <span className="text-primary">Trí tuệ nhân tạo</span>
            </h1>
            
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              Tự động kiểm tra kích thước, dung sai GD&T và đối chiếu tiêu chuẩn ISO/ASME 
              trong vài giây. Tiết kiệm hàng giờ làm việc thủ công.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="h-14 px-8 text-base font-semibold shadow-xl shadow-primary/25">
                  Bắt đầu miễn phí
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/analysis">
                <Button size="lg" variant="outline" className="h-14 px-8 text-base font-semibold">
                  <Scan className="mr-2 h-5 w-5" />
                  Xem Demo
                </Button>
              </Link>
            </div>

            {/* Trust Badges */}
            <div className="mt-16 pt-8 border-t border-border/50">
              <p className="text-sm text-muted-foreground mb-4">Hỗ trợ các tiêu chuẩn quốc tế</p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                {standards.map((standard) => (
                  <span
                    key={standard}
                    className="px-4 py-2 rounded-full bg-card border border-border/50 text-sm font-medium shadow-sm"
                  >
                    {standard}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 md:py-32 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <Badge variant="outline" className="mb-4">Tính năng</Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Những Điểm Sáng Vượt Trội
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Công nghệ Vision AI tiên tiến kết hợp cơ sở tri thức chuẩn ISO, 
              mang đến trải nghiệm kiểm tra bản vẽ chưa từng có.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="group hover:shadow-xl hover:shadow-primary/5 transition-all duration-300 border-border/50">
                <CardContent className="pt-6">
                  <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-5 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <feature.icon className="h-7 w-7 text-primary group-hover:text-primary-foreground transition-colors" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <Badge variant="outline" className="mb-4">Cách hoạt động</Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Trải Nghiệm 4 Bước Dễ Dàng
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Quy trình đơn giản, kết quả chính xác trong vài giây
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-12 left-1/2 w-full h-0.5 bg-gradient-to-r from-primary/50 to-primary/10" />
                )}
                
                <div className="relative bg-card rounded-2xl p-6 border border-border/50 hover:shadow-xl hover:shadow-primary/5 transition-all">
                  {/* Step Number */}
                  <div className="absolute -top-4 left-6 bg-primary text-primary-foreground text-xs font-bold px-3 py-1 rounded-full shadow-lg">
                    {step.number}
                  </div>
                  
                  <div className="h-14 w-14 rounded-2xl bg-accent flex items-center justify-center mb-5 mt-2">
                    <step.icon className="h-7 w-7 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                  <p className="text-muted-foreground text-sm">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 md:py-32 bg-gradient-to-br from-primary/10 via-primary/5 to-background">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <div className="h-20 w-20 rounded-3xl bg-primary/10 flex items-center justify-center mx-auto mb-8">
              <Scan className="h-10 w-10 text-primary" />
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-balance">
              Sẵn sàng nâng cấp quy trình kiểm tra bản vẽ?
            </h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
              Bắt đầu miễn phí với 10 lượt phân tích mỗi ngày. 
              Không cần thẻ tín dụng.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="h-14 px-8 text-base font-semibold shadow-xl shadow-primary/25">
                  Trải nghiệm ngay
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </div>

            {/* Benefits */}
            <div className="flex flex-wrap items-center justify-center gap-6 mt-10">
              {[
                "10 lượt miễn phí/ngày",
                "Hỗ trợ DXF, DWG, PDF",
                "Báo cáo chi tiết",
                "Chat AI 24/7",
              ].map((benefit) => (
                <div key={benefit} className="flex items-center gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-primary" />
                  <span>{benefit}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Eye className="h-4 w-4" />
              </div>
              <span className="font-semibold">AI Vision Drawing Checker</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2026 AI Vision Drawing Checker. Bảo lưu mọi quyền.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
