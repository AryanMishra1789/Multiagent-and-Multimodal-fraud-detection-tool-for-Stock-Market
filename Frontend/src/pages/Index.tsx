import { useState } from "react";
import {
  Shield,
  Brain,
  Eye,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Activity,
  Users,
  FileText,
  MessageSquare,
  Zap,
  Bot,
  Network,
  Cpu
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const Index = () => {
  const [aiAgents] = useState([
    {
      id: "content-analyzer",
      name: "Content Analyzer",
      status: "active",
      type: "Text Analysis",
      accuracy: 94,
      processed: 1247,
      icon: FileText,
      color: "from-primary to-primary-dark"
    },
    {
      id: "social-monitor",
      name: "Social Media Monitor",
      status: "active", 
      type: "Social Intelligence",
      accuracy: 89,
      processed: 856,
      icon: MessageSquare,
      color: "from-info to-info/80"
    },
    {
      id: "pattern-detector",
      name: "Pattern Detector",
      status: "active",
      type: "Behavioral Analysis",
      accuracy: 92,
      processed: 634,
      icon: Network,
      color: "from-success to-success/80"
    },
    {
      id: "risk-assessor",
      name: "Risk Assessor",
      status: "active",
      type: "Risk Modeling",
      accuracy: 96,
      processed: 423,
      icon: TrendingUp,
      color: "from-warning to-warning/80"
    }
  ]);

  const [systemStats] = useState({
    totalCases: 3160,
    activeCases: 127,
    resolvedToday: 89,
    riskLevel: "medium",
    systemHealth: 98
  });

  return (
    <div className="space-y-6 fade-in">
      {/* Hero Section */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-primary-dark/10 rounded-2xl blur-3xl"></div>
        <div className="relative bg-gradient-to-r from-primary to-primary-dark bg-clip-text text-transparent">
          <h1 className="text-4xl font-bold mb-2">SEBI Fraud Detection Dashboard</h1>
        </div>
        <p className="text-foreground/80 text-lg font-medium mb-4">
          Multiagent & Multimodal AI-Powered Stock Market Fraud Detection System
        </p>
        <div className="flex items-center gap-4">
          <Badge className="bg-gradient-to-r from-primary to-primary-dark text-white shadow-lg">
            <Bot className="h-3 w-3 mr-1" />
            {aiAgents.length} AI Agents Active
          </Badge>
          <Badge className="bg-gradient-to-r from-success to-success/80 text-white shadow-lg">
            <Cpu className="h-3 w-3 mr-1" />
            Multimodal Analysis
          </Badge>
        </div>
      </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="relative overflow-hidden group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-primary/5"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Cases</p>
                <p className="text-3xl font-bold text-foreground">{systemStats.totalCases.toLocaleString()}</p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-primary to-primary/80 shadow-lg">
                <Shield className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-warning/10 to-warning/5"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Cases</p>
                <p className="text-3xl font-bold text-warning">{systemStats.activeCases}</p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-warning to-warning/80 shadow-lg">
                <Activity className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-success/10 to-success/5"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Resolved Today</p>
                <p className="text-3xl font-bold text-success">{systemStats.resolvedToday}</p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-success to-success/80 shadow-lg">
                <CheckCircle className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-info/10 to-info/5"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">System Health</p>
                <p className="text-3xl font-bold text-info">{systemStats.systemHealth}%</p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-info to-info/80 shadow-lg">
                <Zap className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Agents Section */}
      <Card className="relative overflow-hidden border-0 shadow-2xl bg-gradient-to-br from-card via-card to-primary/5">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-primary-dark"></div>
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-foreground flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-r from-primary to-primary-dark">
              <Brain className="h-6 w-6 text-white" />
            </div>
            AI Agent Network
            <Badge className="bg-gradient-to-r from-primary to-primary-dark text-white">
              Multiagent System
            </Badge>
          </CardTitle>
          <p className="text-muted-foreground">
            Advanced AI agents working collaboratively for comprehensive fraud detection
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {aiAgents.map((agent) => {
              const IconComponent = agent.icon;
              return (
                <div key={agent.id} className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-primary-dark/5 rounded-xl blur-sm group-hover:blur-none transition-all duration-300"></div>
                  <Card className="relative border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 bg-gradient-to-br from-card to-card/50">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className={`p-3 rounded-xl bg-gradient-to-r ${agent.color} shadow-lg`}>
                            <IconComponent className="h-5 w-5 text-white" />
                          </div>
                          <div>
                            <h3 className="font-bold text-foreground">{agent.name}</h3>
                            <p className="text-sm text-muted-foreground">{agent.type}</p>
                          </div>
                        </div>
                        <Badge className="bg-gradient-to-r from-success to-success/80 text-white">
                          {agent.status}
                        </Badge>
                      </div>
                      
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-muted-foreground">Accuracy</span>
                            <span className="font-medium">{agent.accuracy}%</span>
                          </div>
                          <Progress value={agent.accuracy} className="h-2" />
                        </div>
                        
                        <div className="flex justify-between items-center pt-2 border-t border-border/50">
                          <span className="text-sm text-muted-foreground">Processed Today</span>
                          <span className="font-bold text-primary">{agent.processed.toLocaleString()}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card className="relative overflow-hidden border-0 shadow-xl bg-gradient-to-br from-card via-card to-warning/5">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-warning to-error"></div>
        <CardHeader>
          <CardTitle className="text-xl font-bold text-foreground flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-warning" />
            Recent Fraud Alerts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { type: "High Risk", content: "Suspicious trading pattern detected in RELIANCE", time: "2 min ago", severity: "high" },
              { type: "Medium Risk", content: "Unverified investment advice on social media", time: "15 min ago", severity: "medium" },
              { type: "Low Risk", content: "Missing disclaimer in promotional content", time: "1 hour ago", severity: "low" }
            ].map((alert, index) => (
              <div key={index} className="flex items-center gap-4 p-4 rounded-lg bg-gradient-to-r from-background to-muted/20 hover:shadow-md transition-all duration-200">
                <div className={`p-2 rounded-full ${
                  alert.severity === 'high' ? 'bg-error/20' : 
                  alert.severity === 'medium' ? 'bg-warning/20' : 'bg-success/20'
                }`}>
                  <AlertTriangle className={`h-4 w-4 ${
                    alert.severity === 'high' ? 'text-error' : 
                    alert.severity === 'medium' ? 'text-warning' : 'text-success'
                  }`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className={`${
                      alert.severity === 'high' ? 'bg-error/10 text-error' : 
                      alert.severity === 'medium' ? 'bg-warning/10 text-warning' : 'bg-success/10 text-success'
                    }`}>
                      {alert.type}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{alert.time}</span>
                  </div>
                  <p className="text-sm text-foreground">{alert.content}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Index;
