import { useState, useEffect } from "react";
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
  Cpu,
  Clock,
  TrendingDown
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/components/ui/use-toast";
import { apiService, DashboardStats, AgentStatus, handleApiError } from "@/lib/api";

export default function Dashboard() {
  const [aiAgents, setAiAgents] = useState<AgentStatus[]>([]);
  const [systemStats, setSystemStats] = useState<DashboardStats>({
    total_checks: 0,
    fraud_alerts: 0,
    unique_advisors_verified: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // Map agent names to icons and types
  const getAgentIcon = (name: string) => {
    if (name.toLowerCase().includes('content')) return FileText;
    if (name.toLowerCase().includes('social')) return MessageSquare;
    if (name.toLowerCase().includes('pattern')) return Network;
    if (name.toLowerCase().includes('risk')) return TrendingUp;
    return Bot;
  };

  const getAgentType = (name: string) => {
    if (name.toLowerCase().includes('content')) return 'Text Analysis';
    if (name.toLowerCase().includes('social')) return 'Social Intelligence';
    if (name.toLowerCase().includes('pattern')) return 'Behavioral Analysis';
    if (name.toLowerCase().includes('risk')) return 'Risk Modeling';
    return 'AI Agent';
  };

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const [statsData, agentsData] = await Promise.all([
        apiService.getDashboardStats(),
        apiService.getAgentStatus()
      ]);
      
      setSystemStats(statsData);
      setAiAgents(agentsData);
    } catch (error) {
      const errorMessage = handleApiError(error);
      toast({
        title: "Failed to load dashboard data",
        description: errorMessage,
        variant: "destructive",
      });
      
      // Set fallback data
      setSystemStats({
        total_checks: 0,
        fraud_alerts: 0,
        unique_advisors_verified: 0
      });
      setAiAgents([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);


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
                <p className="text-3xl font-bold text-foreground">{isLoading ? "..." : systemStats.total_checks.toLocaleString()}</p>
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
                <p className="text-sm font-medium text-muted-foreground">Fraud Alerts</p>
                <p className="text-3xl font-bold text-warning">{isLoading ? "..." : systemStats.fraud_alerts}</p>
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
                <p className="text-sm font-medium text-muted-foreground">Verified Advisors</p>
                <p className="text-3xl font-bold text-success">{isLoading ? "..." : systemStats.unique_advisors_verified}</p>
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
                <p className="text-3xl font-bold text-info">{isLoading ? "..." : "98%"}</p>
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
            {isLoading ? (
              // Loading skeleton
              Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="relative group">
                  <Card className="relative border-0 shadow-lg bg-gradient-to-br from-card to-card/50">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="p-3 rounded-xl bg-muted animate-pulse">
                            <div className="h-5 w-5" />
                          </div>
                          <div>
                            <div className="h-4 w-24 bg-muted animate-pulse rounded mb-2"></div>
                            <div className="h-3 w-16 bg-muted animate-pulse rounded"></div>
                          </div>
                        </div>
                        <div className="h-6 w-16 bg-muted animate-pulse rounded"></div>
                      </div>
                      <div className="space-y-3">
                        <div className="h-2 bg-muted animate-pulse rounded"></div>
                        <div className="h-4 bg-muted animate-pulse rounded"></div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ))
            ) : aiAgents.length > 0 ? (
              aiAgents.map((agent, index) => {
                const IconComponent = getAgentIcon(agent.name);
                const agentType = getAgentType(agent.name);
                return (
                  <div key={index} className="relative group">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-primary-dark/5 rounded-xl blur-sm group-hover:blur-none transition-all duration-300"></div>
                    <Card className="relative border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 bg-gradient-to-br from-card to-card/50">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className={`p-3 rounded-xl bg-gradient-to-r ${agent.color || 'from-primary to-primary-dark'} shadow-lg`}>
                              <IconComponent className="h-5 w-5 text-white" />
                            </div>
                            <div>
                              <h3 className="font-bold text-foreground">{agent.name}</h3>
                              <p className="text-sm text-muted-foreground">{agentType}</p>
                            </div>
                          </div>
                          <Badge className={`${agent.status === 'active' ? 'bg-gradient-to-r from-success to-success/80 text-white' : 'bg-muted text-muted-foreground'}`}>
                            {agent.status}
                          </Badge>
                        </div>
                        
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-muted-foreground">Status</span>
                              <span className="font-medium capitalize">{agent.status}</span>
                            </div>
                            <Progress value={agent.status === 'active' ? 95 : 50} className="h-2" />
                          </div>
                          
                          <div className="flex justify-between items-center pt-2 border-t border-border/50">
                            <span className="text-sm text-muted-foreground">Processed</span>
                            <span className="font-bold text-primary">{agent.processed.toLocaleString()}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                );
              })
            ) : (
              // No agents found
              <div className="col-span-2 text-center py-8">
                <p className="text-muted-foreground">No agent data available</p>
              </div>
            )}
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
}