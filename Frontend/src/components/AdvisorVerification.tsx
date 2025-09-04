import { useState } from "react";
import {
  Search,
  User,
  Building,
  Phone,
  Mail,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Calendar,
  FileText,
  Shield
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/components/ui/use-toast";
import { apiService, handleApiError } from "@/lib/api";

interface Advisor {
  id: string;
  name: string;
  registrationNumber: string;
  firm: string;
  status: "active" | "suspended" | "revoked";
  registrationDate: string;
  expiryDate: string;
  email: string;
  phone: string;
  address: string;
  specializations: string[];
  aum: string; // Assets Under Management
  clientCount: number;
  qualifications: string[];
}

const mockAdvisors: Advisor[] = [
  {
    id: "1",
    name: "Rajesh Kumar Sharma",
    registrationNumber: "INA000001234",
    firm: "ABC Wealth Management Pvt. Ltd.",
    status: "active",
    registrationDate: "2020-03-15",
    expiryDate: "2025-03-14",
    email: "rajesh.sharma@abcwealth.com",
    phone: "+91-9876543210",
    address: "1st Floor, Business Tower, Connaught Place, New Delhi - 110001",
    specializations: ["Equity Research", "Portfolio Management", "Retirement Planning"],
    aum: "₹125 Crores",
    clientCount: 450,
    qualifications: ["CFA", "MBA Finance", "NISM Certified"]
  },
  {
    id: "2",
    name: "Priya Mehta",
    registrationNumber: "INA000005678",
    firm: "Smart Investment Solutions",
    status: "active",
    registrationDate: "2019-08-22",
    expiryDate: "2024-08-21",
    email: "priya.mehta@smartinvest.com",
    phone: "+91-9123456789",
    address: "3rd Floor, Tech Park, Bandra Kurla Complex, Mumbai - 400051",
    specializations: ["Mutual Funds", "Tax Planning", "Insurance"],
    aum: "₹85 Crores",
    clientCount: 320,
    qualifications: ["CFP", "CA", "NISM Series XV"]
  }
];

const getStatusColor = (status: string) => {
  switch (status) {
    case "active": return "bg-success/10 text-success";
    case "suspended": return "bg-warning/10 text-warning";
    case "revoked": return "bg-error/10 text-error";
    default: return "bg-muted/10 text-muted-foreground";
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case "active": return CheckCircle;
    case "suspended": return AlertTriangle;
    case "revoked": return XCircle;
    default: return AlertTriangle;
  }
};

export default function AdvisorVerification() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Advisor[]>([]);
  const [selectedAdvisor, setSelectedAdvisor] = useState<Advisor | null>(null);
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const { toast } = useToast();

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      // Use the advisor verification API
      const result = await apiService.verifyAdvisor(searchQuery);
      
      // Check if advisor was found in the result
      if (result.source === "SEBI Advisor List" && result.is_valid && result.context) {
        // Convert API result to our Advisor format
        const advisors = Array.isArray(result.context) ? result.context : [result.context];
        const convertedAdvisors: Advisor[] = advisors.map((advisor: any, index: number) => ({
          id: index.toString(),
          name: advisor.Name || advisor.name || "Unknown",
          registrationNumber: advisor["Registration No."] || advisor.registrationNumber || "N/A",
          firm: advisor.Firm || advisor.firm || "N/A",
          status: "active" as const,
          registrationDate: "2020-01-01", // Default date
          expiryDate: "2025-01-01", // Default date
          email: advisor.Email || advisor.email || "N/A",
          phone: advisor.Phone || advisor.phone || "N/A",
          address: advisor.Address || advisor.address || "N/A",
          specializations: ["Investment Advisory"],
          aum: "N/A",
          clientCount: 0,
          qualifications: ["SEBI Registered"]
        }));
        
        setSearchResults(convertedAdvisors);
        setVerificationResult(result);
        
      } else {
        // No advisors found or not valid - still show the verification result
        setSearchResults([]);
        setVerificationResult(result);
        
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      
      // Fallback to mock data for demo purposes
      const results = mockAdvisors.filter(advisor =>
        advisor.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        advisor.registrationNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        advisor.firm.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setSearchResults(results);
    } finally {
      setIsSearching(false);
    }
  };

  const handleVerifyAdvisor = async (advisor: Advisor) => {
    setSelectedAdvisor(advisor);
    
    // If we already have verification result, use it
    if (verificationResult) {
      return;
    }
    
    // Otherwise, verify this specific advisor
    try {
      const result = await apiService.verifyAdvisor(advisor.registrationNumber);
      setVerificationResult(result);
    } catch (error) {
      console.error('Failed to verify advisor:', error);
    }
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Advisor Verification</h1>
        <p className="text-muted-foreground">
          Search and verify SEBI registered investment advisors
        </p>
      </div>

      {/* Search Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search Investment Advisors
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Enter advisor name, registration number, or firm name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <Button 
              onClick={handleSearch}
              disabled={!searchQuery.trim() || isSearching}
            >
              {isSearching ? "Searching..." : "Search"}
            </Button>
          </div>
          
          <div className="text-sm text-muted-foreground">
            <p>You can search by:</p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Advisor name (e.g., "Rajesh Kumar")</li>
              <li>SEBI registration number (e.g., "INA000001234")</li>
              <li>Investment firm name (e.g., "ABC Wealth Management")</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Search Results ({searchResults.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {searchResults.map((advisor) => {
                const StatusIcon = getStatusIcon(advisor.status);
                return (
                  <div
                    key={advisor.id}
                    className="p-4 border border-border rounded-lg hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold text-foreground">
                            {advisor.name}
                          </h3>
                          <Badge className={getStatusColor(advisor.status)}>
                            <StatusIcon className="mr-1 h-3 w-3" />
                            {advisor.status.toUpperCase()}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <FileText className="h-4 w-4" />
                            <span>Reg. No: {advisor.registrationNumber}</span>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Building className="h-4 w-4" />
                            <span>{advisor.firm}</span>
                          </div>
                        </div>
                        
                        <div className="flex flex-wrap gap-2">
                          {advisor.specializations.slice(0, 3).map((spec) => (
                            <Badge key={spec} variant="outline" className="text-xs">
                              {spec}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      <Button
                        onClick={() => handleVerifyAdvisor(advisor)}
                        variant="outline"
                        size="sm"
                      >
                        <Shield className="mr-2 h-4 w-4" />
                        Verify Details
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Verification Result - Show when search is performed but no advisors found */}
      {verificationResult && !selectedAdvisor && searchResults.length === 0 && (
        <Card className="slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {verificationResult.is_valid ? (
                <CheckCircle className="h-5 w-5 text-success" />
              ) : (
                <XCircle className="h-5 w-5 text-error" />
              )}
              Advisor Verification Result
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className={`${verificationResult.is_valid ? 'bg-success/5' : 'bg-error/5'} rounded-lg p-4`}>
              <div className="flex items-center gap-3">
                {verificationResult.is_valid ? (
                  <CheckCircle className="h-6 w-6 text-success" />
                ) : (
                  <XCircle className="h-6 w-6 text-error" />
                )}
                <div>
                  <h4 className={`font-semibold ${verificationResult.is_valid ? 'text-success' : 'text-error'}`}>
                    {verificationResult.is_valid ? 'Advisor Found' : 'Advisor Not Found'}
                  </h4>
                  <p className="text-sm text-muted-foreground">
                    {verificationResult.message || (
                      verificationResult.is_valid 
                        ? 'The searched advisor is registered with SEBI.'
                        : 'The searched advisor registration number or name was not found in the SEBI database. Please verify the registration number or contact SEBI directly.'
                    )}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="text-sm text-muted-foreground">
              <p><strong>Search Query:</strong> {searchQuery}</p>
              <p><strong>Source:</strong> {verificationResult.source || 'SEBI Advisor Database'}</p>
            </div>
            
            {!verificationResult.is_valid && (
              <div className="bg-warning/10 border border-warning/20 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-warning mt-0.5" />
                  <div>
                    <h4 className="font-medium text-warning">Important Notice</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      If someone claims to be a SEBI registered advisor but is not found in this database, 
                      they may be operating without proper authorization. Always verify advisor credentials 
                      before making any investment decisions.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Advisor Details */}
      {selectedAdvisor && (
        <Card className="slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-success" />
              Advisor Verification Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <User className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Full Name</p>
                      <p className="font-medium">{selectedAdvisor.name}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Registration Number</p>
                      <p className="font-medium font-mono">{selectedAdvisor.registrationNumber}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <Building className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Investment Firm</p>
                      <p className="font-medium">{selectedAdvisor.firm}</p>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Email</p>
                      <p className="font-medium">{selectedAdvisor.email}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <Phone className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Phone</p>
                      <p className="font-medium">{selectedAdvisor.phone}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <Building className="h-5 w-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-sm text-muted-foreground">Address</p>
                      <p className="font-medium text-sm leading-relaxed">
                        {selectedAdvisor.address}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <Separator />

            {/* Registration Details */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Registration Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Registration Date</p>
                    <p className="font-medium">
                      {new Date(selectedAdvisor.registrationDate).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Expiry Date</p>
                    <p className="font-medium">
                      {new Date(selectedAdvisor.expiryDate).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Status</p>
                    <Badge className={getStatusColor(selectedAdvisor.status)}>
                      {selectedAdvisor.status.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>

            <Separator />

            {/* Professional Details */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Professional Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Specializations</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedAdvisor.specializations.map((spec) => (
                      <Badge key={spec} variant="outline">
                        {spec}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Qualifications</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedAdvisor.qualifications.map((qual) => (
                      <Badge key={qual} className="bg-primary/10 text-primary">
                        {qual}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                <div>
                  <p className="text-sm text-muted-foreground">Assets Under Management</p>
                  <p className="text-2xl font-bold text-foreground">{selectedAdvisor.aum}</p>
                </div>
                
                <div>
                  <p className="text-sm text-muted-foreground">Client Count</p>
                  <p className="text-2xl font-bold text-foreground">
                    {selectedAdvisor.clientCount.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            <Separator />

            {/* Verification Result */}
            {verificationResult && (
              <div className={`${verificationResult.is_valid ? 'bg-success/5' : 'bg-error/5'} rounded-lg p-4`}>
                <div className="flex items-center gap-3">
                  {verificationResult.is_valid ? (
                    <CheckCircle className="h-6 w-6 text-success" />
                  ) : (
                    <XCircle className="h-6 w-6 text-error" />
                  )}
                  <div>
                    <h4 className={`font-semibold ${verificationResult.is_valid ? 'text-success' : 'text-error'}`}>
                      {verificationResult.is_valid ? 'Verification Successful' : 'Verification Failed'}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {verificationResult.message || (
                        verificationResult.is_valid 
                          ? 'This advisor is currently registered with SEBI and authorized to provide investment advisory services.'
                          : 'This advisor could not be verified in the SEBI database.'
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}