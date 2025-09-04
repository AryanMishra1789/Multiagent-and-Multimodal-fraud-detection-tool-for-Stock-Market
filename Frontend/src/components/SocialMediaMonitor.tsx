import React, { useState, useEffect } from "react";
import {
  Calendar,
  TrendingUp,
  MessageSquare,
  Users,
  ExternalLink,
  MoreHorizontal,
  Plus,
  ChevronDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  X,
  Loader2,
  Search,
  Eye,
  Flag,
  FileText,
  Info
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { 
  apiService, 
  MultiPlatformStats, 
  SocialMediaMessage, 
  MonitoredGroup, 
  FraudAlert,
  SupportedPlatform,
  handleApiError 
} from "@/lib/api";

interface SocialMediaPost {
  id: string;
  platform: "telegram" | "reddit" | "discord" | "twitter" | "facebook" | "instagram" | "linkedin" | "youtube";
  user: string;
  content: string;
  riskScore: number;
  date: string;
  engagement: number;
  status: "flagged" | "reviewed" | "approved" | "blocked" | "Legitimate" | "Suspicious" | "Fraud";
  url: string;
  groupName?: string;
  alertLevel?: string;
  source?: string;
  analysis_summary?: string;
}

// Convert SocialMediaMessage to SocialMediaPost format
const convertSocialMediaMessage = (message: SocialMediaMessage): SocialMediaPost => ({
  id: message.message_id,
  platform: message.platform as any,
  user: message.author,
  content: message.content,
  riskScore: message.risk_score,
  date: message.timestamp,
  engagement: message.engagement.score || message.engagement.comments || 0,
  status: (message as any).status || (message.is_fraud ? "flagged" : "approved"),
  url: message.url,
  source: message.source,
  alertLevel: message.alert_level,
  analysis_summary: message.analysis_summary
});

const platformIcons = {
  telegram: "📱",
  reddit: "🔴",
  discord: "🎮",
  twitter: "🐦",
  facebook: "📘",
  instagram: "📷",
  linkedin: "💼",
  youtube: "📺"
};

const getRiskColor = (score: number) => {
  if (score >= 80) return "bg-gradient-to-r from-error to-error/80 text-white shadow-lg";
  if (score >= 50) return "bg-gradient-to-r from-warning to-warning/80 text-white shadow-lg";
  return "bg-gradient-to-r from-success to-success/80 text-white shadow-lg";
};

const getStatusColor = (status: string) => {
  switch (status) {
    case "Fraud":
    case "flagged": return "bg-gradient-to-r from-error to-error/80 text-white shadow-lg";
    case "Suspicious":
    case "reviewed": return "bg-gradient-to-r from-warning to-warning/80 text-white shadow-lg";
    case "Legitimate":
    case "approved": return "bg-gradient-to-r from-success to-success/80 text-white shadow-lg";
    case "blocked": return "bg-gradient-to-r from-destructive to-destructive/80 text-white shadow-lg";
    default: return "bg-gradient-to-r from-muted to-muted/80 text-muted-foreground shadow-lg";
  }
};

export default function SocialMediaMonitor() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("all");
  const [selectedRisk, setSelectedRisk] = useState("all");
  const [posts, setPosts] = useState<SocialMediaPost[]>([]);
  const [newGroupHandle, setNewGroupHandle] = useState("");
  const [selectedNewPlatform, setSelectedNewPlatform] = useState<string>("");
  const [monitoredGroups, setMonitoredGroups] = useState<MonitoredGroup[]>([]);
  const [multiPlatformStats, setMultiPlatformStats] = useState<MultiPlatformStats | null>(null);
  const [supportedPlatforms, setSupportedPlatforms] = useState<SupportedPlatform[]>([]);
  const [platformStatus, setPlatformStatus] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPostForAnalysis, setSelectedPostForAnalysis] = useState<SocialMediaPost | null>(null);
  const { toast } = useToast();

  // Load data on component mount
  useEffect(() => {
    loadMultiPlatformData();
  }, []);

  const loadMultiPlatformData = async () => {
    setIsLoading(true);
    try {
      // Load multi-platform data with better error handling
      const [status, stats, groups, messages, platforms] = await Promise.all([
        apiService.getMultiPlatformStatus().catch((err) => {
          console.log("Multi-platform status error:", err);
          return { platforms: {}, total_active_platforms: 0 };
        }),
        apiService.getMultiPlatformStats().catch((err) => {
          console.log("Multi-platform stats error:", err);
          return null;
        }),
        apiService.getAllMonitoredGroups().catch((err) => {
          console.log("Monitored groups error:", err);
          return { groups: [], total_count: 0 };
        }),
        apiService.getSocialMediaMessages(100).catch((err) => {
          console.log("Social media messages error:", err);
          return { messages: [], total_count: 0 };
        }),
        apiService.getSupportedPlatforms().catch((err) => {
          console.log("Supported platforms error:", err);
          // Return hardcoded platforms as fallback
          return {
            platforms: [
              { name: "telegram", display_name: "Telegram", description: "Monitor Telegram groups", free: true, requires_setup: true, setup_requirements: [] },
              { name: "reddit", display_name: "Reddit", description: "Monitor Reddit subreddits", free: true, requires_setup: true, setup_requirements: [] },
              { name: "discord", display_name: "Discord", description: "Monitor Discord servers", free: true, requires_setup: true, setup_requirements: [] }
            ]
          };
        })
      ]);

      console.log("Loaded platforms:", platforms);
      setPlatformStatus(status.platforms);
      setMultiPlatformStats(stats);
      setMonitoredGroups(groups.groups);
      setSupportedPlatforms(platforms.platforms);
      
      // Convert social media messages to posts
      const convertedPosts = messages.messages.map(convertSocialMediaMessage);
      setPosts(convertedPosts);

    } catch (error) {
      console.error("Error in loadMultiPlatformData:", error);
      const errorMessage = handleApiError(error);
      toast({
        title: "Error Loading Data",
        description: errorMessage,
        variant: "destructive",
      });
      
      // Set fallback platforms even on error
      setSupportedPlatforms([
        { name: "telegram", display_name: "Telegram", description: "Monitor Telegram groups", free: true, requires_setup: true, setup_requirements: [] },
        { name: "reddit", display_name: "Reddit", description: "Monitor Reddit subreddits", free: true, requires_setup: true, setup_requirements: [] },
        { name: "discord", display_name: "Discord", description: "Monitor Discord servers", free: true, requires_setup: true, setup_requirements: [] }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveGroup = async (platform: string, groupId: string) => {
    try {
      await apiService.removeSocialMediaGroup(platform, groupId);
      loadMultiPlatformData(); // Refresh data
      toast({
        title: "Success",
        description: `Removed ${platform} group successfully`,
      });
    } catch (error) {
      const errorMessage = handleApiError(error);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const filteredPosts = posts.filter(post => {
    const matchesSearch = searchQuery === '' || 
      post.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.user.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (post.groupName && post.groupName.toLowerCase().includes(searchQuery.toLowerCase()));
      
    const matchesPlatform = selectedPlatform === 'all' || post.platform === selectedPlatform;
    
    let matchesRisk = true;
    if (selectedRisk === 'high') {
      matchesRisk = post.riskScore >= 80;
    } else if (selectedRisk === 'medium') {
      matchesRisk = post.riskScore >= 50 && post.riskScore < 80;
    } else if (selectedRisk === 'low') {
      matchesRisk = post.riskScore < 50;
    }
    
    return matchesSearch && matchesPlatform && matchesRisk;
  });

  const updatePostStatus = (postId: string, newStatus: SocialMediaPost["status"]) => {
    setPosts(prev => prev.map(post => 
      post.id === postId ? { ...post, status: newStatus } : post
    ));
  };

  const addSocialMediaGroup = async () => {
    if (!selectedNewPlatform || !newGroupHandle.trim()) {
      toast({
        title: "Error",
        description: "Please select a platform and enter a group handle",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      await apiService.addSocialMediaGroup(selectedNewPlatform, newGroupHandle.trim());
      await loadMultiPlatformData();
      setNewGroupHandle("");
      setSelectedNewPlatform("");
      toast({
        title: "Success",
        description: `Added ${selectedNewPlatform} group successfully`,
      });
    } catch (error) {
      const errorMessage = handleApiError(error);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Stats Cards */}
        <Card className="relative overflow-hidden group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-primary/5"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Platforms</p>
                <p className="text-3xl font-bold text-primary">
                  {isLoading ? (
                    <Clock className="h-8 w-8 animate-spin" />
                  ) : (
                    (multiPlatformStats as any)?.total_active_platforms || Object.keys(platformStatus).filter(p => platformStatus[p].is_active).length
                  )}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-primary to-primary/80 shadow-lg">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-info/10 to-info/5"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Messages</p>
                <p className="text-3xl font-bold text-foreground">
                  {isLoading ? (
                    <Clock className="h-8 w-8 animate-spin" />
                  ) : (
                    multiPlatformStats?.combined.weekly_messages || posts.length
                  )}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-info to-info/80 shadow-lg">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-error/10 to-error/5"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Fraud Detected</p>
                <p className="text-3xl font-bold text-error">
                  {isLoading ? (
                    <Clock className="h-8 w-8 animate-spin" />
                  ) : (
                    multiPlatformStats?.combined.weekly_fraud_detected || posts.filter(p => p.status === "flagged").length
                  )}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-error to-error/80 shadow-lg">
                <Flag className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-warning/10 to-warning/5"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">High Risk</p>
                <p className="text-3xl font-bold text-warning">
                  {isLoading ? (
                    <Clock className="h-8 w-8 animate-spin" />
                  ) : (
                    multiPlatformStats?.combined.weekly_high_risk || posts.filter(p => p.riskScore >= 80).length
                  )}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-warning to-warning/80 shadow-lg">
                <AlertTriangle className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add New Group Card */}
      <Card className="relative overflow-hidden border-0 shadow-xl bg-gradient-to-br from-card via-card to-accent/5">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent to-primary"></div>
        <CardHeader>
          <CardTitle className="text-xl font-bold text-foreground">
            Add Social Media Group
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Select value={selectedNewPlatform} onValueChange={setSelectedNewPlatform}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Platform" />
                </SelectTrigger>
                <SelectContent>
                  {supportedPlatforms.map(platform => (
                    <SelectItem key={platform.name} value={platform.name}>
                      {platform.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                placeholder="Group ID or URL"
                value={newGroupHandle}
                onChange={(e) => setNewGroupHandle(e.target.value)}
                className="md:col-span-2"
              />
            </div>
            <div className="flex justify-end">
              <Button 
                onClick={addSocialMediaGroup}
                disabled={!selectedNewPlatform || !newGroupHandle.trim() || isLoading}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Adding...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Group
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Currently Monitored Groups Section */}
          <div className="mt-8">
            <h4 className="text-sm font-medium mb-3 text-muted-foreground">
              Currently Monitored Groups ({monitoredGroups.length})
            </h4>
            {monitoredGroups.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Users className="mx-auto h-12 w-12 mb-2 opacity-50" />
                <p>No groups being monitored yet</p>
                <p className="text-sm">Add a group above to start monitoring</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {monitoredGroups.map((group) => (
                  <div 
                    key={`${group.platform}-${group.group_id}`} 
                    className="flex items-center justify-between p-3 border rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span className="text-lg">
                        {platformIcons[group.platform as keyof typeof platformIcons] || '📱'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{group.group_name || group.group_id}</p>
                        <div className="flex items-center gap-2">
                          <span className="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">
                            {group.platform}
                          </span>
                          {group.status && (
                            <span className="text-xs text-muted-foreground">
                              {group.status}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveGroup(group.platform, group.group_id)}
                      className="h-8 w-8 p-0 hover:bg-destructive/10 hover:text-destructive"
                      title="Remove from monitoring"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card className="relative overflow-hidden border-0 shadow-xl bg-gradient-to-br from-card via-card to-accent/5">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent to-primary"></div>
        <CardHeader>
          <CardTitle className="text-xl font-bold text-foreground">
            Filters & Search
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search posts, users, or content..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-full"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Platforms" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Platforms</SelectItem>
                  <SelectItem value="telegram">📱 Telegram</SelectItem>
                  <SelectItem value="reddit">🔴 Reddit</SelectItem>
                  <SelectItem value="discord">🎮 Discord</SelectItem>
                  <SelectItem value="twitter">🐦 Twitter</SelectItem>
                  <SelectItem value="facebook">📘 Facebook</SelectItem>
                  <SelectItem value="instagram">📷 Instagram</SelectItem>
                  <SelectItem value="linkedin">💼 LinkedIn</SelectItem>
                  <SelectItem value="youtube">📺 YouTube</SelectItem>
                </SelectContent>
              </Select>
              <Select value={selectedRisk} onValueChange={setSelectedRisk}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Risk Levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Risk Levels</SelectItem>
                  <SelectItem value="high">High Risk (80+)</SelectItem>
                  <SelectItem value="medium">Medium Risk (50-79)</SelectItem>
                  <SelectItem value="low">Low Risk (below 50)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Posts Table */}
      <Card className="relative overflow-hidden border-0 shadow-2xl bg-gradient-to-br from-card via-card to-error/5">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-error to-warning"></div>
        <CardHeader>
          <CardTitle className="text-xl font-bold bg-gradient-to-r from-error to-warning bg-clip-text text-transparent">
            Flagged Social Media Posts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Platform</TableHead>
                <TableHead>Content</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    <div className="flex flex-col items-center justify-center">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-2" />
                      <p>Loading posts...</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredPosts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                    No posts found matching your filters
                  </TableCell>
                </TableRow>
              ) : (
                filteredPosts.map((post) => (
                  <TableRow key={post.id} className="hover:bg-muted/50">
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-lg">
                          {platformIcons[post.platform] || '📱'}
                        </span>
                        <span className="capitalize">{post.platform}</span>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[300px] truncate">
                      <p className="truncate">{post.content}</p>
                    </TableCell>
                    <TableCell>
                      <p className="font-medium">{post.user}</p>
                    </TableCell>
                    <TableCell>
                      {post.groupName && (
                        <span className="text-sm text-muted-foreground">
                          {post.groupName}
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-muted-foreground">
                        {new Date(post.date).toLocaleDateString()}
                      </p>
                    </TableCell>
                    <TableCell>
                      <Badge className={getRiskColor(post.riskScore)}>
                        {post.riskScore}%
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(post.status)}>
                        {post.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => window.open(post.url, '_blank')}
                          >
                            <ExternalLink className="mr-2 h-4 w-4" />
                            View Post
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setSelectedPostForAnalysis(post)}
                          >
                            <FileText className="mr-2 h-4 w-4" />
                            View Detailed Analysis
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => updatePostStatus(post.id, "reviewed")}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            Mark as Reviewed
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => updatePostStatus(post.id, "approved")}
                            className="text-success"
                          >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            Approve
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => updatePostStatus(post.id, "blocked")}
                            className="text-destructive"
                          >
                            <X className="mr-2 h-4 w-4" />
                            Block Content
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Detailed Analysis Dialog */}
      <Dialog open={!!selectedPostForAnalysis} onOpenChange={() => setSelectedPostForAnalysis(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Detailed Fraud Analysis
            </DialogTitle>
          </DialogHeader>
          
          {selectedPostForAnalysis && (
            <div className="space-y-6">
              {/* Post Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Post Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start gap-2">
                    <span className="font-medium text-sm">Platform:</span>
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {platformIcons[selectedPostForAnalysis.platform]}
                      </span>
                      <span className="capitalize">{selectedPostForAnalysis.platform}</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="font-medium text-sm">Author:</span>
                    <span className="text-sm">{selectedPostForAnalysis.user}</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="font-medium text-sm">Source:</span>
                    <span className="text-sm">{selectedPostForAnalysis.source || 'Unknown'}</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="font-medium text-sm">Date:</span>
                    <span className="text-sm">{new Date(selectedPostForAnalysis.date).toLocaleString()}</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="font-medium text-sm">Content:</span>
                    <span className="text-sm">{selectedPostForAnalysis.content}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Risk Assessment */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Risk Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="space-y-3">
                      <div className="flex items-start gap-2">
                        <span className="font-medium text-sm">Overall Status:</span>
                        <Badge className={getStatusColor(selectedPostForAnalysis.status)}>
                          {selectedPostForAnalysis.status}
                        </Badge>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="font-medium text-sm">Risk Score:</span>
                        <div className="flex items-center gap-2">
                          <Badge className={getRiskColor(selectedPostForAnalysis.riskScore)}>
                            {selectedPostForAnalysis.riskScore}/100
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            ({selectedPostForAnalysis.riskScore >= 80 ? 'High Risk' : 
                              selectedPostForAnalysis.riskScore >= 40 ? 'Medium Risk' : 'Low Risk'})
                          </span>
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="font-medium text-sm">Alert Level:</span>
                        <span className="text-sm capitalize">{selectedPostForAnalysis.alertLevel || 'low'}</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="font-medium text-sm">Recommendation:</span>
                        <span className="text-sm">
                          {selectedPostForAnalysis.status === 'Fraud' ? 
                            'Immediate investigation required. Content shows signs of fraudulent activity.' :
                            selectedPostForAnalysis.status === 'Suspicious' ?
                            'Enhanced monitoring recommended. Content contains potential risk indicators.' :
                            'Content appears legitimate. Continue routine monitoring.'}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Analysis Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Analysis Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="space-y-3">
                      <div className="flex items-start gap-2">
                        <span className="font-medium text-sm">Fraud Indicators:</span>
                        <span className="text-sm">
                          {selectedPostForAnalysis.analysis_summary || 'No specific fraud indicators detected'}
                        </span>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="font-medium text-sm">Processing Time:</span>
                        <span className="text-sm">
                          {new Date().toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Regulatory Disclaimer */}
              <div className="p-4 bg-gray-100 rounded-lg border">
                <h4 className="font-medium text-gray-800 mb-2 flex items-center gap-2">
                  <Info className="h-4 w-4" />
                  Regulatory Notice
                </h4>
                <p className="text-sm text-muted-foreground">
                  This analysis was conducted using AI-powered fraud detection algorithms in compliance with SEBI guidelines. 
                  The reasoning provided is based on pattern recognition, sentiment analysis, and regulatory database cross-referencing. 
                  For critical decisions, manual verification by authorized personnel is recommended.
                </p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
