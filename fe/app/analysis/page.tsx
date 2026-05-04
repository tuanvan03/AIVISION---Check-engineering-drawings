"use client"

import { useState, useCallback } from "react"
import { 
  Upload, 
  FileType, 
  Send, 
  AlertTriangle, 
  AlertCircle, 
  Info,
  CheckCircle,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Download,
  Maximize2,
  Bot,
  User as UserIcon,
  Sparkles,
  Loader2,
  Check
} from "lucide-react"
import { Navbar } from "@/components/navbar"
import { ProtectedRoute } from "@/components/auth/route-guard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import { cn } from "@/lib/utils"

interface DrawingType {
  id: string
  name: string
  description: string
  confidence: number
  selected: boolean
}

interface AnalysisError {
  id: string
  type: "critical" | "warning" | "info"
  title: string
  description: string
  isoReference?: string
}

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

const mockDrawingTypes: DrawingType[] = [
  { id: "1", name: "Bản vẽ chi tiết (Detail Drawing)", description: "Bản vẽ thể hiện chi tiết một bộ phận cơ khí", confidence: 95, selected: true },
  { id: "2", name: "Bản vẽ lắp ráp (Assembly Drawing)", description: "Bản vẽ thể hiện cách lắp ráp các chi tiết", confidence: 78, selected: false },
  { id: "3", name: "Bản vẽ mặt cắt (Section Drawing)", description: "Bản vẽ thể hiện mặt cắt của chi tiết", confidence: 65, selected: true },
  { id: "4", name: "Bản vẽ kích thước (Dimension Drawing)", description: "Bản vẽ tập trung vào kích thước và dung sai", confidence: 82, selected: true },
  { id: "5", name: "Bản vẽ GD&T", description: "Bản vẽ có ký hiệu dung sai hình học", confidence: 88, selected: true },
]

const mockErrors: AnalysisError[] = [
  {
    id: "1",
    type: "critical",
    title: "Thiếu dung sai kích thước",
    description: "Kích thước Ø25 tại vị trí lỗ chính chưa được ghi dung sai theo tiêu chuẩn.",
    isoReference: "ISO 129-1:2018, Điều 5.3.2",
  },
  {
    id: "2",
    type: "warning",
    title: "Ký hiệu GD&T không chuẩn",
    description: "Ký hiệu độ song song tại mặt A cần được điều chỉnh theo quy cách.",
    isoReference: "ASME Y14.5-2018, Điều 6.4",
  },
  {
    id: "3",
    type: "info",
    title: "Đề xuất cải thiện",
    description: "Nên bổ sung đường tâm cho các lỗ đồng trục để tăng độ rõ ràng.",
  },
]

const mockMessages: ChatMessage[] = [
  {
    id: "1",
    role: "assistant",
    content: "Xin chào! Tôi đã phân tích xong bản vẽ của bạn. Tôi phát hiện 3 vấn đề cần chú ý: 1 lỗi nghiêm trọng, 1 cảnh báo và 1 đề xuất cải thiện. Bạn muốn tôi giải thích chi tiết vấn đề nào?",
    timestamp: new Date(),
  },
]

type AnalysisStep = "upload" | "detecting" | "confirm-type" | "ready" | "analyzing" | "complete"

export default function AnalysisPage() {
  const [file, setFile] = useState<File | null>(null)
  const [step, setStep] = useState<AnalysisStep>("upload")
  const [drawingTypes, setDrawingTypes] = useState<DrawingType[]>([])
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [errors, setErrors] = useState<AnalysisError[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isDragging, setIsDragging] = useState(false)
  const [zoom, setZoom] = useState(100)
  const [confirmationMessage, setConfirmationMessage] = useState("")

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      setFile(droppedFile)
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const detectDrawingType = async () => {
    setStep("detecting")
    
    // Simulate API call for rule-based detection
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    setDrawingTypes(mockDrawingTypes)
    setStep("confirm-type")
  }

  const toggleDrawingType = (id: string) => {
    setDrawingTypes(prev => 
      prev.map(type => 
        type.id === id ? { ...type, selected: !type.selected } : type
      )
    )
  }

  const confirmDrawingTypes = () => {
    const selectedTypes = drawingTypes.filter(t => t.selected)
    setConfirmationMessage(`Đã xác nhận ${selectedTypes.length} loại bản vẽ: ${selectedTypes.map(t => t.name.split(" (")[0]).join(", ")}`)
    setStep("ready")
  }

  const startAnalysis = async () => {
    setStep("analyzing")
    setAnalysisProgress(0)
    
    for (let i = 0; i <= 100; i += 2) {
      await new Promise(resolve => setTimeout(resolve, 50))
      setAnalysisProgress(i)
    }
    
    setStep("complete")
    setErrors(mockErrors)
    setMessages(mockMessages)
  }

  const sendMessage = () => {
    if (!inputMessage.trim()) return
    
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: inputMessage,
      timestamp: new Date(),
    }
    
    setMessages(prev => [...prev, newMessage])
    setInputMessage("")
    
    setTimeout(() => {
      const response: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Theo tiêu chuẩn ISO 129-1:2018, mọi kích thước chức năng đều phải có dung sai rõ ràng. Đối với lỗ Ø25 trong bản vẽ của bạn, tôi khuyến nghị áp dụng dung sai H7 (+0.021/0) nếu đây là lỗ lắp ghép trượt, hoặc H8 nếu yêu cầu độ chính xác thấp hơn.",
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, response])
    }, 1000)
  }

  const getErrorIcon = (type: AnalysisError["type"]) => {
    switch (type) {
      case "critical":
        return <AlertCircle className="h-4 w-4 text-destructive" />
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-warning" />
      case "info":
        return <Info className="h-4 w-4 text-primary" />
    }
  }

  const getErrorBadgeVariant = (type: AnalysisError["type"]) => {
    switch (type) {
      case "critical":
        return "destructive"
      case "warning":
        return "secondary"
      case "info":
        return "outline"
    }
  }

  const resetAnalysis = () => {
    setFile(null)
    setStep("upload")
    setDrawingTypes([])
    setAnalysisProgress(0)
    setErrors([])
    setMessages([])
    setConfirmationMessage("")
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Navbar />
      
      <main className="container mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-4 h-[calc(100vh-8rem)]">
          {/* Left Panel - Drawing Viewer */}
          <div className="flex-1 flex flex-col min-h-[350px] lg:min-h-0">
            <Card className="flex-1 flex flex-col overflow-hidden">
              <CardHeader className="flex-shrink-0 flex flex-row items-center justify-between py-2.5 px-4 border-b">
                <CardTitle className="text-sm font-medium">Bản vẽ</CardTitle>
                {(step === "confirm-type" || step === "ready" || step === "complete") && (
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setZoom(z => Math.max(25, z - 25))}>
                      <ZoomOut className="h-3.5 w-3.5" />
                    </Button>
                    <span className="text-xs text-muted-foreground w-10 text-center">{zoom}%</span>
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setZoom(z => Math.min(200, z + 25))}>
                      <ZoomIn className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7">
                      <RotateCw className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7">
                      <Maximize2 className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7">
                      <Download className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                )}
              </CardHeader>
              <CardContent className="flex-1 p-4 flex items-center justify-center overflow-auto">
                {step === "upload" && !file && (
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                      "w-full h-full min-h-[280px] border-2 border-dashed rounded-xl flex flex-col items-center justify-center gap-3 transition-all cursor-pointer relative",
                      isDragging
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50 hover:bg-accent/50"
                    )}
                  >
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
                      <Upload className="h-7 w-7 text-primary" />
                    </div>
                    <div className="text-center">
                      <p className="text-base font-medium">Kéo thả file bản vẽ vào đây</p>
                      <p className="text-sm text-muted-foreground mt-1">hoặc click để chọn file</p>
                    </div>
                    <p className="text-xs text-muted-foreground">Hỗ trợ: DXF, DWG, PDF (tối đa 50MB)</p>
                    <input
                      type="file"
                      accept=".dxf,.dwg,.pdf"
                      onChange={handleFileChange}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                  </div>
                )}

                {step === "upload" && file && (
                  <div className="w-full max-w-sm space-y-4">
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-accent/50 border border-border">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                        <FileType className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{file.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={resetAnalysis}
                        className="text-muted-foreground hover:text-destructive text-xs h-8"
                      >
                        Xóa
                      </Button>
                    </div>

                    <Button
                      onClick={detectDrawingType}
                      className="w-full h-10 text-sm font-semibold shadow-lg shadow-primary/25"
                    >
                      <Sparkles className="mr-2 h-4 w-4" />
                      Xác định loại bản vẽ
                    </Button>
                  </div>
                )}

                {step === "detecting" && (
                  <div className="text-center space-y-4">
                    <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto" />
                    <div>
                      <p className="font-medium">Đang xác định loại bản vẽ...</p>
                      <p className="text-sm text-muted-foreground mt-1">Sử dụng rule-based AI để phân loại</p>
                    </div>
                  </div>
                )}

                {(step === "confirm-type" || step === "ready" || step === "analyzing" || step === "complete") && (
                  <div 
                    className="w-full h-full bg-accent/30 rounded-lg flex items-center justify-center"
                    style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'center' }}
                  >
                    <div className="w-full max-w-2xl aspect-[4/3] bg-background rounded-lg border-2 border-border flex items-center justify-center">
                      <div className="text-muted-foreground space-y-2 text-center">
                        <FileType className="h-14 w-14 mx-auto opacity-50" />
                        <p className="text-sm">Bản vẽ: {file?.name}</p>
                        <p className="text-xs opacity-75">(Preview bản vẽ thực tế)</p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Panel - Results & Chat */}
          <div className="w-full lg:w-[360px] flex flex-col min-h-[400px] lg:min-h-0">
            <Card className="flex-1 flex flex-col overflow-hidden">
              <Tabs defaultValue="results" className="flex-1 flex flex-col">
                <TabsList className="w-full justify-start rounded-none border-b bg-transparent px-3 py-0 h-10">
                  <TabsTrigger
                    value="results"
                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-3 py-2 text-sm"
                  >
                    Kết quả
                    {errors.length > 0 && (
                      <Badge variant="secondary" className="ml-1.5 h-4 px-1 text-[10px]">
                        {errors.length}
                      </Badge>
                    )}
                  </TabsTrigger>
                  <TabsTrigger
                    value="chat"
                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-3 py-2 text-sm"
                  >
                    Chat AI
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="results" className="flex-1 m-0 overflow-hidden">
                  <ScrollArea className="h-full">
                    <div className="p-3 space-y-2.5">
                      {step === "upload" && (
                        <div className="flex flex-col items-center justify-center py-10 text-center">
                          <div className="h-12 w-12 rounded-xl bg-muted flex items-center justify-center mb-3">
                            <FileType className="h-6 w-6 text-muted-foreground" />
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Tải lên bản vẽ để bắt đầu
                          </p>
                        </div>
                      )}

                      {step === "detecting" && (
                        <div className="flex flex-col items-center justify-center py-10 text-center">
                          <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
                          <p className="text-sm text-muted-foreground">
                            Đang phân tích loại bản vẽ...
                          </p>
                        </div>
                      )}

                      {step === "confirm-type" && (
                        <>
                          <div className="p-2.5 rounded-lg bg-primary/5 border border-primary/20 mb-3">
                            <p className="text-xs font-medium text-primary">
                              Vui lòng xác nhận loại bản vẽ được phát hiện:
                            </p>
                          </div>
                          
                          <div className="space-y-2">
                            {drawingTypes.map((type) => (
                              <div
                                key={type.id}
                                onClick={() => toggleDrawingType(type.id)}
                                className={cn(
                                  "p-2.5 rounded-lg border cursor-pointer transition-all",
                                  type.selected 
                                    ? "bg-primary/5 border-primary/30" 
                                    : "bg-card border-border hover:border-primary/20"
                                )}
                              >
                                <div className="flex items-start gap-2.5">
                                  <Checkbox 
                                    checked={type.selected} 
                                    className="mt-0.5 h-4 w-4"
                                    onCheckedChange={() => toggleDrawingType(type.id)}
                                  />
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between gap-2">
                                      <h4 className="font-medium text-xs">{type.name}</h4>
                                      <Badge variant="outline" className="text-[10px] h-4 px-1">
                                        {type.confidence}%
                                      </Badge>
                                    </div>
                                    <p className="text-[11px] text-muted-foreground mt-0.5">
                                      {type.description}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>

                          <Button
                            onClick={confirmDrawingTypes}
                            disabled={!drawingTypes.some(t => t.selected)}
                            className="w-full h-9 text-sm mt-3"
                          >
                            <Check className="mr-1.5 h-3.5 w-3.5" />
                            Xác nhận loại bản vẽ
                          </Button>
                        </>
                      )}

                      {step === "ready" && (
                        <>
                          <div className="p-2.5 rounded-lg bg-green-500/10 border border-green-500/20 mb-3">
                            <div className="flex items-start gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                              <p className="text-xs text-green-700 dark:text-green-400">
                                {confirmationMessage}
                              </p>
                            </div>
                          </div>

                          <Button
                            onClick={startAnalysis}
                            className="w-full h-9 text-sm shadow-lg shadow-primary/25"
                          >
                            <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                            Bắt đầu phân tích
                          </Button>
                        </>
                      )}

                      {step === "analyzing" && (
                        <div className="space-y-3 py-6">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground">Đang phân tích...</span>
                            <span className="font-medium">{analysisProgress}%</span>
                          </div>
                          <Progress value={analysisProgress} className="h-1.5" />
                          <p className="text-xs text-muted-foreground text-center">
                            {analysisProgress < 20 && "Đang đọc file bản vẽ..."}
                            {analysisProgress >= 20 && analysisProgress < 40 && "Đang xử lý hình ảnh..."}
                            {analysisProgress >= 40 && analysisProgress < 60 && "Đang phân tích kích thước..."}
                            {analysisProgress >= 60 && analysisProgress < 80 && "Đang kiểm tra GD&T..."}
                            {analysisProgress >= 80 && analysisProgress < 95 && "Đang đối chiếu ISO..."}
                            {analysisProgress >= 95 && "Đang tạo báo cáo..."}
                          </p>
                        </div>
                      )}

                      {step === "complete" && (
                        <>
                          {/* Summary */}
                          <div className="grid grid-cols-3 gap-1.5 mb-3">
                            <div className="flex items-center gap-1.5 p-2 rounded-lg bg-destructive/10 border border-destructive/20">
                              <AlertCircle className="h-3.5 w-3.5 text-destructive" />
                              <div>
                                <p className="text-[10px] text-muted-foreground">Nghiêm trọng</p>
                                <p className="text-sm font-semibold text-destructive">
                                  {errors.filter(e => e.type === "critical").length}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 p-2 rounded-lg bg-warning/10 border border-warning/20">
                              <AlertTriangle className="h-3.5 w-3.5 text-warning" />
                              <div>
                                <p className="text-[10px] text-muted-foreground">Cảnh báo</p>
                                <p className="text-sm font-semibold text-warning-foreground">
                                  {errors.filter(e => e.type === "warning").length}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 p-2 rounded-lg bg-primary/10 border border-primary/20">
                              <Info className="h-3.5 w-3.5 text-primary" />
                              <div>
                                <p className="text-[10px] text-muted-foreground">Đề xuất</p>
                                <p className="text-sm font-semibold text-primary">
                                  {errors.filter(e => e.type === "info").length}
                                </p>
                              </div>
                            </div>
                          </div>

                          {/* Error List */}
                          {errors.map((error) => (
                            <div
                              key={error.id}
                              className="p-2.5 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer"
                            >
                              <div className="flex items-start gap-2">
                                <div className="mt-0.5">{getErrorIcon(error.type)}</div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5 mb-0.5">
                                    <h4 className="font-medium text-xs">{error.title}</h4>
                                    <Badge variant={getErrorBadgeVariant(error.type)} className="text-[10px] h-4 px-1">
                                      {error.type === "critical" && "Nghiêm trọng"}
                                      {error.type === "warning" && "Cảnh báo"}
                                      {error.type === "info" && "Đề xuất"}
                                    </Badge>
                                  </div>
                                  <p className="text-[11px] text-muted-foreground mb-1.5">
                                    {error.description}
                                  </p>
                                  {error.isoReference && (
                                    <p className="text-[10px] text-primary font-mono bg-primary/5 px-1.5 py-0.5 rounded inline-block">
                                      {error.isoReference}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent value="chat" className="flex-1 m-0 flex flex-col overflow-hidden">
                  <ScrollArea className="flex-1">
                    <div className="p-3 space-y-3">
                      {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-10 text-center">
                          <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mb-3">
                            <Bot className="h-6 w-6 text-primary" />
                          </div>
                          <p className="font-medium text-sm mb-0.5">AI Chuyên gia</p>
                          <p className="text-xs text-muted-foreground max-w-[220px]">
                            Hỏi tôi về bản vẽ, tiêu chuẩn ISO, hoặc cách khắc phục lỗi
                          </p>
                        </div>
                      ) : (
                        messages.map((message) => (
                          <div
                            key={message.id}
                            className={cn(
                              "flex gap-2",
                              message.role === "user" && "flex-row-reverse"
                            )}
                          >
                            <div
                              className={cn(
                                "h-6 w-6 rounded-md flex items-center justify-center flex-shrink-0",
                                message.role === "user"
                                  ? "bg-primary text-primary-foreground"
                                  : "bg-accent"
                              )}
                            >
                              {message.role === "user" ? (
                                <UserIcon className="h-3 w-3" />
                              ) : (
                                <Bot className="h-3 w-3" />
                              )}
                            </div>
                            <div
                              className={cn(
                                "flex-1 rounded-lg px-3 py-2 text-xs",
                                message.role === "user"
                                  ? "bg-primary text-primary-foreground"
                                  : "bg-accent"
                              )}
                            >
                              {message.content}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </ScrollArea>

                  {/* Chat Input */}
                  <div className="p-3 border-t">
                    <div className="flex gap-2">
                      <Input
                        placeholder="Hỏi về bản vẽ hoặc tiêu chuẩn..."
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                        className="h-8 text-xs"
                        disabled={step !== "complete"}
                      />
                      <Button
                        onClick={sendMessage}
                        disabled={!inputMessage.trim() || step !== "complete"}
                        className="h-8 px-3"
                        size="sm"
                      >
                        <Send className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </Card>
          </div>
        </div>
      </main>
    </div>
    </ProtectedRoute>
  )
}
